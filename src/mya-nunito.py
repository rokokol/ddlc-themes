"""Merge Nunito with the Greek and mathematics it lacks into one variable font, Mya Nunito.

    python3 mya-nunito.py VENDOR OUTDIR

Nunito draws Latin and Cyrillic well and has next to no Greek, no arrows, a handful of
operators and few super and subscripts. This adds them from Noto Sans, and from Noto Sans
Math where Noto Sans lacks them, as glyphs of Nunito's own variable font:

- the masters are Nunito's, read off its variation data, and its glyphs, substitutions and
  kerning are copied, not rebuilt, so every character Nunito has draws as in Nunito
- an added glyph is scaled about the baseline so that Noto's x stands as high as Nunito's at
  the body weight, its advance with it
- at each master the added glyph takes the weight of Noto Sans whose stem, scaled, is as wide
  as Nunito's stem there. What no weight of Noto matches, the stems of Noto Sans Math, which
  has one weight, and of Noto Sans past its Black, is made up by emboldening the outline the
  way FreeType does, which keeps the number and order of points, so the masters interpolate
- emboldening also brings the horizontal strokes to Nunito's at that master
- the openings between strokes come first: a glyph takes only as much of its emboldening as
  keeps them open by the measure of Nunito's equals sign, and thins only as far as its
  strokes hold, both measured on a raster by glyph_openings.py beside this file
- an added glyph keeps the sidebearings of the lightest master at every weight, as Nunito's
  own mathematical signs do
- an added letter rounds its outward corners by half the stem, so a stroke ends in a half
  circle as Nunito's do; a sign keeps its points

Writes MyaNunito.ttf and MyaNunito-Italic.ttf, the same as WOFF2, the static family Mya Nunito
Static for matplotlib, which reads no variation axis, and the licence, MyaNunito-LICENSE.txt,
into OUTDIR. The italic adds the same glyphs to Nunito Italic, so its operators stay upright,
as mathematics keeps them in slanted prose too, but a Greek letter Nunito lacks draws there as
its mathematical italic from Noto Sans Math, as Latin does in Nunito Italic: matplotlib sets a
formula's letters in the italic, and there phi keeps the loop that sets it apart from the phi
symbol. The build is byte-stable for the same input, fonttools, numpy and scipy
"""

import logging
import math
import re
import sys
import unicodedata
from copy import deepcopy
from pathlib import Path

from fontTools import varLib
from fontTools.designspaceLib import AxisDescriptor, DesignSpaceDocument, SourceDescriptor
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.pointPen import PointToSegmentPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPointPen
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
from fontTools.varLib import instancer

# The measure of openings lives beside this file, shared with the test
sys.path.insert(0, str(Path(__file__).resolve().parent))
from glyph_openings import (  # noqa: E402
    NOTCH_DEPTH,
    Flattener,
    keeps,
    kept_share,
    measured,
    narrowest,
    notch_shares,
    notches,
    openings,
    outline,
    parts,
    raster,
    ridge_width,
    strokes,
)

vendor, outdir = Path(sys.argv[1]), Path(sys.argv[2])

# Where the report's mathematics lives. A block is listed when a note might write a character
# from it; the codepoints a Noto font lacks, and those Nunito has, drop out on their own
BLOCKS = [
    (0x02B0, 0x02FF),  # Spacing Modifier Letters: the raised h, j, r, w, x and y of an index
    (0x0370, 0x03FF),  # Greek and Coptic
    (0x1D2C, 0x1D6A),  # Phonetic Extensions: the modifier letters of a transpose or an index
    (0x2070, 0x209F),  # Superscripts and Subscripts
    (0x2100, 0x214F),  # Letterlike Symbols: the blackboard R, C, N and Z
    (0x2190, 0x21FF),  # Arrows
    (0x2200, 0x22FF),  # Mathematical Operators
    (0x2300, 0x23FF),  # Miscellaneous Technical: floor and ceiling
    (0x25A0, 0x25FF),  # Geometric Shapes
    (0x27C0, 0x27FF),  # Miscellaneous Mathematical Symbols-A and Supplemental Arrows-A
    (0x2980, 0x29FF),  # Miscellaneous Mathematical Symbols-B
    (0x2A00, 0x2AFF),  # Supplemental Mathematical Operators
    (0x1D400, 0x1D7FF),  # Mathematical Alphanumeric Symbols: the double-struck E and 1
]
# Single marks outside the blocks: the double bar of a norm, the primes, the fraction slash,
# and the subscript j and the superscript V, which Latin Extended-C keeps beside the index i
LOOSE = [0x2016, 0x2032, 0x2033, 0x2034, 0x2044, 0x2C7C, 0x2C7D]

# The weight the prose is set in, where the x-heights are compared
BODY_WEIGHT = 500

# The static faces, for matplotlib and whatever else reads no variation axis, by style and
# weight: normal and bold, which matplotlib asks for unless told otherwise, and the body's
# Medium and the headings' Black, in both styles. They are a family of their own, so that a
# system holding both sees each family once
STATICS = {
    "Regular": ("", 400),
    "Medium": ("", 500),
    "Bold": ("", 700),
    "Black": ("", 900),
    "Italic": ("-Italic", 400),
    "MediumItalic": ("-Italic", 500),
    "BoldItalic": ("-Italic", 700),
    "BlackItalic": ("-Italic", 900),
}

FAMILY = "Mya Nunito"
STATIC_FAMILY = "Mya Nunito Static"

NUNITO = {"": vendor / "nunito/Nunito-wght.ttf", "-Italic": vendor / "nunito/Nunito-Italic-wght.ttf"}
SANS = vendor / "noto-sans/NotoSans-wdth-wght.ttf"
MATH = vendor / "noto-sans-math/NotoSansMath-Regular.ttf"
SANS_WIDTH = {"wdth": 100}
DEFAULT_SANS_WEIGHT = 400

# Measured openings, by source, codepoint, weight and scale
OPENINGS = {}
# How sharply an outline must turn, in degrees, for its point to be a corner that rounds: a
# square end turns by 90, while a curve drawn in short straight pieces turns by a few
CORNER = 35
# How far into a corner's angle its ink is sought, in font units: well inside the thinnest
# stroke, so a tip a few units wide still holds it
WEDGE = 2
# How far, in degrees, an outline may turn at a point and still run smooth through it: a curve
# whose points are rounded to whole units bends by a degree or two at each
SMOOTH = 10
# How much wider than its strength gives an added glyph's usual stroke may grow, in font units:
# six pixels of the raster that measures it. The median of the ridge steps between the widths a
# raster holds, by up to four pixels as a glyph grows, while a filled notch adds a stroke's width
RIDGE_SLACK = 24
# Measured notches, by source, codepoint, weight and scale
NOTCHES = {}
# The share of its strength and the source weight each added glyph took, by master: the
# first style decides, and the italic, which adds the same upright glyphs, follows
DECIDED = {}

# Mya Nunito is a Modified Version of all three under the OFL, which asks it to keep their
# copyright notices and to carry the licence. Each licence file opens with its notice, a blank
# line, and then the OFL itself, the same text in all three
LICENCES = [
    vendor / "nunito/Nunito-LICENSE.txt",
    vendor / "noto-sans/NotoSans-LICENSE.txt",
    vendor / "noto-sans-math/NotoSansMath-LICENSE.txt",
]
OFL_URL = "https://openfontlicense.org"
OFL_NOTICE = (
    "This Font Software is licensed under the SIL Open Font License, Version 1.1. "
    f"This license is available with a FAQ at: {OFL_URL}"
)


def notices():
    """The copyright notice of each source, the first line of its licence"""
    lines = [path.read_text().splitlines()[0] for path in LICENCES]
    if not all(line.startswith("Copyright ") for line in lines):
        sys.exit(f"mya-nunito.py: a licence does not open with its copyright notice: {lines}")
    return lines


def licence_text():
    """The three notices, then the OFL as Nunito's licence states it"""
    body = LICENCES[0].read_text().split("\n\n", 1)[1]
    return "\n".join(notices()) + "\n\n" + body


def drawing(glyphset, name):
    pen = DecomposingRecordingPen(glyphset)
    glyphset[name].draw(pen)
    return pen.value


def stroke(glyphset, name, vertical):
    """The width of the first stroke a line through the middle of the glyph crosses

    A vertical stem is cut by a horizontal line halfway up the glyph, a horizontal bar by a
    vertical line halfway across. The outline is measured rather than the bounding box, which
    takes in the tail of Nunito's l and the round ends of its strokes
    """
    pen = Flattener(glyphset)
    glyphset[name].draw(pen)
    box = BoundsPen(glyphset)
    glyphset[name].draw(box)
    xmin, ymin, xmax, ymax = box.bounds
    cut = (ymin + ymax) / 2 if vertical else (xmin + xmax) / 2
    hits = []
    for polygon in pen.polygons:
        for (ax, ay), (bx, by) in zip(polygon, polygon[1:] + polygon[:1]):
            if not vertical:
                ax, ay, bx, by = ay, ax, by, bx
            if (ay <= cut < by) or (by <= cut < ay):
                hits.append(ax + (cut - ay) * (bx - ax) / (by - ay))
    hits.sort()
    return hits[1] - hits[0]


def stems(glyphset, cmap):
    """The vertical stem of l and the horizontal bar of the minus sign, in font units"""
    return stroke(glyphset, cmap[ord("l")], True), stroke(glyphset, cmap[0x2212], False)


def x_height(glyphset, cmap):
    """The height of a lowercase x outline, which is what a reader sees as the text's size

    The outline is measured, not OS/2 sxHeight, which states 484 for Nunito while its x is 494
    high: the rounded terminals overshoot the flat top that sxHeight assumes
    """
    pen = BoundsPen(glyphset)
    glyphset[cmap[ord("x")]].draw(pen)
    return pen.bounds[3]


def nunito_masters(font):
    """Nunito's masters as weights: the peaks of the regions its glyph variations use

    A master is where a region peaks, in the normalized space after avar, so each peak is
    mapped back through avar and the axis to a weight
    """
    axis = font["fvar"].axes[0]
    peaks = {0.0}
    for variations in font["gvar"].variations.values():
        for variation in variations:
            peaks.add(variation.axes["wght"][1])
    segments = sorted(font["avar"].segments["wght"].items())

    def unmap(n):
        for (a, b), (c, d) in zip(segments, segments[1:]):
            if b <= n <= d:
                return a if d == b else a + (n - b) * (c - a) / (d - b)
        raise ValueError(n)

    return [round(axis.defaultValue + unmap(p) * (axis.maxValue - axis.defaultValue)) for p in sorted(peaks)]


def signed_area(contour):
    return sum(x0 * y1 - x1 * y0 for (x0, y0, _), (x1, y1, _) in zip(contour, contour[1:] + contour[:1])) / 2


def ink(contours):
    """The area the curves enclose, counters taken away"""
    pen = AreaPen()
    points = PointToSegmentPen(pen)
    for contour in contours:
        points.beginPath()
        for x, y, segment in contour:
            points.addPoint((x, y), segment)
        points.endPath()
    return abs(pen.value)


def embolden(contours, xstrength, ystrength):
    """FreeType's FT_Outline_EmboldenXY on control points, in floating point

    Each point moves along the bisector of the two edges that meet at it, so that every edge
    moves outward by half the strength, and the number and order of points stay. Off-curve
    points move as on-curve ones do, so a quadratic curve keeps its shape. A negative strength
    thins. FreeType then leaves the outline's left and bottom edges in place; here the bottom
    is kept centred instead, so an operator stays on the mathematical axis, while the left
    edge is kept, and the caller widens the advance by the strength to keep the right
    sidebearing. Returns the contours moved, kept smooth where they ran smooth
    """
    xs, ys = xstrength / 2, ystrength / 2
    truetype = sum(signed_area(c) for c in contours) < 0
    out_contours = []
    for points in contours:
        moved = [list(p) for p in points]
        reversals = set()
        first, last = 0, len(points) - 1
        vin, lin = (0.0, 0.0), 0.0
        anchor, lanchor = (0.0, 0.0), 0.0
        i, j, k = last, first, -1
        while j != i and i != k:
            if j != k:
                dx, dy = points[j][0] - points[i][0], points[j][1] - points[i][1]
                lout = math.hypot(dx, dy)
                if lout == 0:
                    j = j + 1 if j < last else first
                    continue
                vout = (dx / lout, dy / lout)
            else:
                vout, lout = anchor, lanchor
            if lin != 0:
                if k < 0:
                    k, anchor, lanchor = i, vin, lin
                d = vin[0] * vout[0] + vin[1] * vout[1]
                # Shift only where the outline turns by less than about 160 degrees
                if d > -0.9375:
                    d += 1
                    sx, sy = vin[1] + vout[1], vin[0] + vout[0]
                    q = vout[0] * vin[1] - vout[1] * vin[0]
                    if truetype:
                        sx, q = -sx, -q
                    else:
                        sy = -sy
                    # A short edge limits the shift, so a point does not run past its neighbour
                    shortest = min(lin, lout)
                    sx = sx * xs / d if xs * q <= shortest * d else sx * shortest / q
                    sy = sy * ys / d if ys * q <= shortest * d else sy * shortest / q
                else:
                    sx = sy = 0.0
                sharp = d <= -0.9375
                while i != j:
                    moved[i][0] += xs + sx
                    moved[i][1] += sy
                    if sharp:
                        reversals.add(i)
                    i = i + 1 if i < last else first
            else:
                i = j
            vin, lin = vout, lout
            j = j + 1 if j < last else first
        # FreeType leaves a point where the outline doubles back in place while the edges on
        # either side move out, which draws a spur where a hairline meets a bowl in a script
        # letter. Such a point moves as its moving neighbours do, on average
        n = len(points)
        for i in sorted(reversals):
            shifts = []
            for step in (-1, 1):
                k = (i + step) % n
                while k in reversals and k != i:
                    k = (k + step) % n
                if k not in reversals:
                    shifts.append((moved[k][0] - points[k][0], moved[k][1] - points[k][1]))
            if shifts:
                moved[i][0] = points[i][0] + sum(s[0] for s in shifts) / len(shifts)
                moved[i][1] = points[i][1] + sum(s[1] for s in shifts) / len(shifts)
        out_contours.append(moved)
    return [smoothed(before, after) for before, after in zip(contours, out_contours)]


def smoothed(before, after):
    """Keep smooth what was smooth: a point on the curve between two control points, where
    the outline ran straight through it, goes back onto the line between them, at the share of
    the way it stood before

    Each point moves along its own bisector by its own amount, so where a tight curve bends
    hard the three no longer line up and the curve breaks in a kink, as in the loops of a
    script letter or the tail of ξ at Black
    """
    n = len(before)
    out = [list(p) for p in after]
    for i, (x, y, segment) in enumerate(before):
        (ax, ay, a_seg), (bx, by, b_seg) = before[i - 1], before[(i + 1) % n]
        if segment is None or a_seg is not None or b_seg is not None:
            continue
        ux, uy, vx, vy = x - ax, y - ay, bx - x, by - y
        lu, lv = math.hypot(ux, uy), math.hypot(vx, vy)
        if not lu or not lv or abs(math.degrees(math.atan2(ux * vy - uy * vx, ux * vx + uy * vy))) > SMOOTH:
            continue
        share = lu / (lu + lv)
        (px, py, _), (qx, qy, _) = after[i - 1], after[(i + 1) % n]
        out[i][0], out[i][1] = px + (qx - px) * share, py + (qy - py) * share
    return out


def collapsed(before, after):
    """Whether a contour turned inside out or shrank past what still reads as its shape

    A counter narrower than the strength closes up, and then its edges cross and it turns
    inside out; before that it is a sliver. A contour that keeps less than a quarter of its
    area counts as closed
    """
    for a, b in zip(before, after):
        area_a, area_b = signed_area(a), signed_area(b)
        if area_a and ((area_a > 0) != (area_b > 0) or abs(area_b) < abs(area_a) / 4):
            return True
    return False


def emboldened(contours, xstrength, ystrength):
    """The contours emboldened by the strength, or by as much of it as they take

    Where the whole strength would close a counter, as in a double-struck letter at Black or
    the narrow arrowheads of a long arrow, the glyph takes the largest share of it that keeps
    every contour open, found to a sixty-fourth. That glyph stops gaining weight there, and
    every other glyph takes the whole strength. Returns the contours and the share taken
    """
    after = embolden(contours, xstrength, ystrength)
    if not collapsed(contours, after):
        return after, 1.0
    lo, hi = 0.0, 1.0
    for _ in range(6):
        mid = (lo + hi) / 2
        if collapsed(contours, embolden(contours, xstrength * mid, ystrength * mid)):
            hi = mid
        else:
            lo = mid
    return embolden(contours, xstrength * lo, ystrength * lo), lo


def rounded(contours):
    return [[[round(x), round(y), s] for x, y, s in contour] for contour in contours]


def winding(contour, x, y):
    """How many times a contour's points wind about a point, counterclockwise counted up"""
    total = 0.0
    for (x0, y0, _), (x1, y1, _) in zip(contour, contour[1:] + contour[:1]):
        turn = math.atan2(y1 - y, x1 - x) - math.atan2(y0 - y, x0 - x)
        total += (turn + math.pi) % (2 * math.pi) - math.pi
    return round(total / (2 * math.pi))


def visible(contours, ci, x, y):
    """Whether a point of one contour lies on the edge of the ink: ink on one side of the
    contour there and none on the other, as for an outer edge or a counter's, and not inside
    the ink of a contour that overlaps it"""
    others = sum(winding(other, x, y) for oi, other in enumerate(contours) if oi != ci)
    own = 1 if signed_area(contours[ci]) > 0 else -1
    return (others == 0) != (others + own == 0)


def inked_wedge(contours, x, y, a, b):
    """Whether the ink fills the angle between a corner's two sides: an outward corner, and a
    needle tip that doubles back on itself, where the sign of the turn is no guide"""
    la, lb = math.dist((x, y), a), math.dist((x, y), b)
    wx, wy = (a[0] - x) / la + (b[0] - x) / lb, (a[1] - y) / la + (b[1] - y) / lb
    lw = math.hypot(wx, wy)
    if lw < 1e-6:
        return False
    px, py = x + WEDGE * wx / lw, y + WEDGE * wy / lw
    return sum(winding(contour, px, py) for contour in contours) != 0


def convex_corners(contours):
    """The corners to round, as (contour, point): every point on the curve where the outline
    turns outward by more than CORNER degrees on the edge of the ink. A corner turning inward
    is left sharp, as Nunito leaves where its strokes meet; so is one inside the ink of another
    contour, where a variable font lets contours overlap and a rounded corner would notch the
    join"""
    picked = []
    for ci, contour in enumerate(contours):
        n = len(contour)
        for pi, (x, y, segment) in enumerate(contour):
            if segment is None or n < 3:
                continue
            (ax, ay, _), (bx, by, _) = contour[pi - 1], contour[(pi + 1) % n]
            ux, uy, vx, vy = x - ax, y - ay, bx - x, by - y
            if not (ux or uy) or not (vx or vy):
                continue
            turn = math.degrees(math.atan2(ux * vy - uy * vx, ux * vx + uy * vy))
            if abs(turn) < CORNER or not inked_wedge(contours, x, y, (ax, ay), (bx, by)):
                continue
            if not visible(contours, ci, x, y):
                continue
            picked.append((ci, pi))
    return picked


def _lerp(p, q, t):
    return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)


def _quadratic(p0, c, p2, t):
    return _lerp(_lerp(p0, c, t), _lerp(c, p2, t), t)


def _within(p0, c, p2, corner, cut, outgoing):
    """The parameter where a quadratic curve comes within the cut of the corner it starts or
    ends at: from 0 it leaves the corner, toward 1 it arrives there"""
    lo, hi = 0.0, 1.0
    for _ in range(24):
        mid = (lo + hi) / 2
        near = math.dist(_quadratic(p0, c, p2, mid), corner) < cut
        # Leaving, the curve is near the corner below the parameter; arriving, above it
        if near == outgoing:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def filleted(contours, corners, radius):
    """The contours with each corner cut back along both its sides and closed by a quadratic
    arc tangent to both, so every master gains the same points

    A straight side is cut along its length. A curved side is split where it comes within the
    cut of the corner, so the end of a curved stroke rounds as a straight one does and the arc
    leaves the curve without a kink. The arc's control point is where the two tangents meet,
    or the corner where they meet nowhere near. The cut is the radius, or less where a side is
    short: half a straight side, which the corner at its other end may cut as well, or the
    whole of a curved one. So the square end of a stroke as wide as twice the radius becomes a
    half round. A curve two corners would both split is cut as a line on both, so the points
    a contour gains depend on its points alone and are the same on every master
    """
    out = [list(contour) for contour in contours]
    for ci in sorted({ci for ci, _ in corners}):
        contour = [tuple(p) for p in contours[ci]]
        n = len(contour)
        chosen = sorted(pi for c, pi in corners if c == ci)

        def on(i):
            return contour[i % n][2] is not None

        def at(i):
            return contour[i % n][:2]

        claims = {}
        for pi in chosen:
            for step in (-1, 1):
                if not on(pi + step):
                    for k in (pi + step, pi + 2 * step):
                        if not on(k):
                            claims[k % n] = claims.get(k % n, 0) + 1
        replace = {}
        for pi in chosen:
            corner, sides = at(pi), {}
            for step in (-1, 1):
                near = at(pi + step)
                split = not on(pi + step) and all(claims[k % n] == 1 for k in (pi + step, pi + 2 * step) if not on(k))
                if split:
                    far_on = on(pi + 2 * step)
                    far = at(pi + 2 * step) if far_on else _lerp(near, at(pi + 2 * step), 0.5)
                    sides[step] = (near, far, far_on)
                else:
                    sides[step] = (near, None, None)
            cut = min([radius] + [math.dist(corner, far) if far else math.dist(corner, near) / 2 for near, far, _ in sides.values()])
            ends = {}
            for step, (near, far, far_on) in sides.items():
                if far is None:
                    length = math.dist(corner, near)
                    end = _lerp(corner, near, cut / length) if length else corner
                    # The tangent runs along the side, toward the corner
                    ends[step] = (end, (corner[0] - end[0], corner[1] - end[1]))
                    continue
                outgoing = step == 1
                p0, p2 = (corner, far) if outgoing else (far, corner)
                t = _within(p0, near, p2, corner, cut, outgoing)
                end = _quadratic(p0, near, p2, t)
                if outgoing:
                    # The arc's end starts what is left of the curve, through a new control
                    leaving = _lerp(corner, near, t)
                    ends[step] = (end, (leaving[0] - end[0], leaving[1] - end[1]))
                    replace[(pi + 1) % n] = [[*_lerp(near, far, t), None]] + ([] if far_on else [[*far, "qcurve"]])
                else:
                    arriving = _lerp(near, corner, t)
                    ends[step] = (end, (arriving[0] - end[0], arriving[1] - end[1]))
                    replace[(pi - 1) % n] = ([] if far_on else [[*far, "qcurve"]]) + [[*_lerp(far, near, t), None]]
            (s, d1), (e, d2) = ends[-1], ends[1]
            # Where the tangent from the start, toward the corner, meets the one from the end
            control = corner
            det = d1[0] * d2[1] - d1[1] * d2[0]
            if abs(det) > 1e-9:
                u = ((e[0] - s[0]) * d2[1] - (e[1] - s[1]) * d2[0]) / det
                v = ((e[0] - s[0]) * d1[1] - (e[1] - s[1]) * d1[0]) / det
                meet = (s[0] + u * d1[0], s[1] + u * d1[1])
                if u > 0 and v > 0 and math.dist(meet, corner) < 2 * cut:
                    control = meet
            replace[pi] = [[*s, contour[pi][2]], [*control, None], [*e, "qcurve"]]
        out[ci] = [list(p) for i in range(n) for p in replace.get(i, [contour[i]])]
    return out


def ttglyph(contours):
    pen = TTGlyphPointPen(None)
    for contour in contours:
        pen.beginPath()
        for x, y, segment in contour:
            pen.addPoint((round(x), round(y)), segment)
        pen.endPath()
    return pen.glyph()


def wanted_codepoints():
    wanted = {cp for lo, hi in BLOCKS for cp in range(lo, hi + 1)} | set(LOOSE)
    have_nunito = set()
    for path in NUNITO.values():
        have_nunito |= set(TTFont(path, lazy=True).getBestCmap())
    have_sans = set(TTFont(SANS, lazy=True).getBestCmap())
    have_math = set(TTFont(MATH, lazy=True).getBestCmap())
    return sorted((wanted & have_sans) - have_nunito), sorted(((wanted & have_math) - have_sans) - have_nunito)


def math_italic(cp):
    """The mathematical italic codepoint of a Greek letter, found by its Unicode name, or None"""
    name = unicodedata.name(chr(cp))
    for greek, math in (("GREEK SMALL LETTER ", "SMALL "), ("GREEK CAPITAL LETTER ", "CAPITAL "),
                        ("GREEK LUNATE ", ""), ("GREEK ", "")):
        if name.startswith(greek):
            try:
                return ord(unicodedata.lookup("MATHEMATICAL ITALIC " + math + name[len(greek):]))
            except KeyError:
                return None
    return None


def italic_greek(font, nunito_cmap):
    """Map each Greek letter Nunito lacks to the glyph of its mathematical italic"""
    best = font.getBestCmap()
    for sub in font["cmap"].tables:
        for cp in [cp for cp in sub.cmap if 0x0370 <= cp <= 0x03FF and cp not in nunito_cmap]:
            twin = math_italic(cp) if unicodedata.category(chr(cp)).startswith("L") else None
            if twin in best:
                sub.cmap[cp] = best[twin]


def matching_weight(sans, cmap, scale, target):
    """The weight of Noto Sans whose stem, scaled, is as wide as the target, within its axis"""
    axis = next(a for a in sans["fvar"].axes if a.axisTag == "wght")

    def stem(weight):
        return scale * stems(sans.getGlyphSet(location={"wght": weight, **SANS_WIDTH}), cmap)[0]

    lo, hi = axis.minValue, axis.maxValue
    if target >= stem(hi):
        return round(hi)
    if target <= stem(lo):
        return round(lo)
    while hi - lo > 0.5:
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if stem(mid) < target else (lo, mid)
    return round((lo + hi) / 2)


class Source:
    """Where a set of added glyphs comes from, and how it is drawn at one master

    glyphs(weight) is the source's glyph set at a weight of its own axis, or at its one weight
    when weight is None. weight is the weight the stems matched at this master, and residual
    the emboldening still owed to the stems
    """

    def __init__(self, prefix, cmap, unicodes, scale, glyphs, weight, residual):
        self.prefix, self.cmap, self.unicodes, self.scale = prefix, cmap, unicodes, scale
        self.glyphs, self.weight, self.residual = glyphs, weight, residual

    def contours(self, cp, weight):
        glyphset = self.glyphs(weight)
        return outline(glyphset, self.cmap[cp], self.scale), glyphset[self.cmap[cp]].width * self.scale


def notches_of(source, cp, weight):
    key = (source.prefix, cp, weight, source.scale)
    if key not in NOTCHES:
        NOTCHES[key] = notches(source.contours(cp, weight)[0])
    return NOTCHES[key]


def allowed_share(found, required, xres, yres):
    """The largest share of the strength that leaves every opening at least the required width

    Emboldening narrows an opening by the strength across it: the vertical strength for a gap
    between horizontal strokes, the horizontal one between vertical strokes, and the larger of
    the two where separate parts face each other in any direction. A negative result means the
    outline is too tight already
    """
    share = 1.0
    for width, axis, *_ in found:
        across ={"x": xres, "y": yres, "xy": max(xres, yres)}[axis]
        if across > 0:
            share = min(share, (width - required) / across)
    return share


def add_glyphs(master, sources, openness, thinness, radius, state, openings_of, decided):
    """Add the scaled, emboldened glyphs to one master, with their advances and codepoints

    openness is (width, ratio, drawn ratio, depth, notch share): no opening of a glyph need be
    wider than the width, nor narrow past the ratio of its own narrowest opening at the lightest
    master or the drawn ratio of its narrowest as the source draws it, and no notch deeper than
    the depth in a source of one weight keeps less of it than the notch share. thinness is (width,
    ratio) for strokes as they thin: down to the width, or to the ratio of their own. radius
    rounds the corners of the letters. state
    carries each glyph from the lighter master before, which is never heavier, and decided the
    share and weight each glyph took at this master in a style built before. Returns the
    glyphs that took less than the whole strength
    """
    capped = []
    glyf, hmtx = master["glyf"], master["hmtx"]
    order = list(master.getGlyphOrder())
    cmap = dict(master.getBestCmap())
    for source in sources:
        xres, yres = source.residual
        for cp in source.unicodes:
            name = source.prefix + source.cmap[cp]
            cmap[cp] = name
            if name in glyf:
                continue
            before = state.get(name)
            weight = source.weight
            scaled, width = source.contours(cp, weight)
            share, held = 1.0, False
            # The italic draws the same upright glyphs as the roman, out of a strength that
            # differs by a unit: what the roman took at this master, the italic starts from
            prior = decided.get(name)
            if prior and (prior[2] or prior[1] != prior[3]):
                # Held where the master below left it, or drawn at a lighter weight of its
                # source: the same again
                share, weight, held, _ = prior
                if held:
                    weight = before["weight"]
                if weight != source.weight:
                    scaled, width = source.contours(cp, weight)
            elif prior and not (xres > 0 or yres > 0) and source.weight is None:
                share = prior[0]
            # Openings first: no gap of an added glyph narrows past what is required of it,
            # which the glyph's own narrowest opening at the lightest master sets. A source
            # with a weight axis narrows its gaps by its heavier weight too, emboldened or not
            elif xres > 0 or yres > 0 or (before and source.weight is not None):
                growing = xres > 0 or yres > 0
                width_cap, ratio, ratio_drawn, deep, notch_share = openness
                # Its own openings: as the lightest master has them, and, for a source of one
                # weight, as the source draws them, since thinning that one weight to the
                # lightest can widen a narrow slot of the design, as between the strokes of a
                # sans-serif bold italic M, out of the measure's sight. A source with a weight
                # axis has a light weight of its own and is not thinned
                if before:
                    required = min(width_cap, ratio * before["open"], ratio_drawn * before["drawn"])
                else:
                    required = min(width_cap, narrowest(openings_of(source, cp, weight)))
                # Never lighter than at the master below: no share under the one that gives
                # the strength the glyph took there, which is negative where it was thinned
                floor = 0.0
                if before and growing:
                    floor = min(max(b / r for b, r in ((before["x"], xres), (before["y"], yres)) if r > 0), 1.0)

                # The openings it must keep: those of its source as drawn at the weight the
                # master below took, the one weight for a source of one weight. The master below
                # is no measure for that, since thinning can split what the source joins
                drawn_openings = openings_of(source, cp, before["weight"] if before else weight)
                # And the deep notches of a source of one weight, as it draws them at the
                # reference weight. A source with a weight axis keeps the notches its designers
                # drew at each weight
                drawn_notches = []
                if source.weight is None:
                    drawn_notches = [n for n in notches_of(source, cp, None) if n[0] >= deep]

                def fits(part, outline=scaled):
                    # Measured as the font will hold it, corners rounded and in whole units: a
                    # slot whose length is about the least a slot runs comes and goes with a
                    # rounded corner or a unit of rounding
                    out, _ = emboldened(outline, xres * part, yres * part)
                    if before and before["corners"]:
                        out = filleted(out, before["corners"], radius)
                    image = raster(rounded(out))
                    found = measured(image)
                    if narrowest(found) < required or not keeps(found, drawn_openings):
                        return False
                    if min(notch_shares(notches(image), drawn_notches), default=1.0) < notch_share:
                        return False
                    # Its strokes grow by the strength and no faster: faster, emboldening fills
                    # a notch between strokes that is no opening the measure above sees, as
                    # the inner V of a bold italic M, and the glyph turns to a blot
                    grown = max(xres, yres, 0) * part
                    return ridge_width(image) <= ridge_width(outline) + grown + RIDGE_SLACK

                if growing:
                    if prior:
                        foreseen = prior[0]
                    else:
                        foreseen = allowed_share(openings_of(source, cp, weight), required, xres, yres)
                    share = max(foreseen, floor)
                    # The narrowing is foreseen from the openings the outline has, so it is
                    # measured too. A heavier outline can grow new openings where strokes meet,
                    # and an opening between parallel steps does not narrow at all: the whole
                    # strength is taken whenever the outline keeps its openings with it, and a
                    # foresight down to the floor is sought above the floor too
                    if share < 1 and fits(1.0):
                        share = 1.0
                    elif share == floor or not fits(share):
                        lo, hi = floor, share if share > floor else 1.0
                        for _ in range(6):
                            mid = (lo + hi) / 2
                            lo, hi = (mid, hi) if fits(mid) else (lo, mid)
                        share = lo
                elif not fits(1.0):
                    # The weight itself closes an opening: a lighter one, below
                    share = -1.0
                if share < 0 and weight is not None:
                    # A source with a weight axis thins by its own lighter weights rather than
                    # by the outline: the heaviest weight, down to the one the master below
                    # took, whose openings hold with no emboldening
                    lo, hi = (before["weight"] if before else weight), weight
                    while hi - lo > 1:
                        mid = (lo + hi) // 2
                        if fits(0.0, source.contours(cp, mid)[0]):
                            lo = mid
                        else:
                            hi = mid
                    share = 0.0
                    if before and not fits(0.0, source.contours(cp, lo)[0]):
                        # No weight down to the one below holds: held as the master below
                        held, lo = True, before["weight"]
                    weight = lo
                    scaled, width = source.contours(cp, weight)
                elif before and growing and share <= floor:
                    # Held where the master below left it: the same source and strength, so
                    # the glyph is that one, not one a little heavier along one axis
                    held = True
                    if weight != before["weight"]:
                        weight = before["weight"]
                        scaled, width = source.contours(cp, weight)
            elif xres < 0 or yres < 0:
                # Thinning: no stroke thinner than Nunito's thinnest stroke at this master, or
                # than its own width thinned in the proportion Nunito's bar is, whichever
                # allows more, so a hairline of a double-struck letter does not vanish
                thinnest, ratio = thinness

                image = raster(scaled)
                source_strokes = dict((axis, w) for w, axis in strokes(image))
                source_parts = parts(image)

                def thin_fits(part):
                    out, _ = emboldened(scaled, xres * part, yres * part)
                    image = raster(out)
                    if parts(image) > source_parts:
                        return False
                    for w, axis in strokes(image):
                        own = source_strokes.get(axis, min(source_strokes.values(), default=w))
                        if w < min(thinnest, ratio * own):
                            return False
                    return True

                if not thin_fits(1.0):
                    lo, hi = 0.0, 1.0
                    for _ in range(6):
                        mid = (lo + hi) / 2
                        lo, hi = (mid, hi) if thin_fits(mid) else (lo, mid)
                    share = lo
            decided.setdefault(name, (share, weight, held, source.weight))
            xs, ys = (before["x"], before["y"]) if held else (xres * share, yres * share)
            contours, kept = emboldened(scaled, xs, ys)
            xs, ys = xs * kept, ys * kept
            if held or share * kept < 1:
                capped.append(name)
            # A letter's corners round as Nunito's stroke ends are, the same corners on every
            # master; a sign keeps the points of its arrows and bars. They are chosen on the
            # lightest master's source as drawn: thinning it can shrink the cut that ends a
            # stroke to nothing, and the corners on it with it. A glyph held as at the master
            # below keeps that master's radius too: a wider one would take ink away as the
            # weight grows
            corners, fillet = [], before["radius"] if held else radius
            if unicodedata.category(chr(cp)).startswith("L"):
                corners = before["corners"] if before else convex_corners(scaled)
                emboldened_contours = contours
                contours = filleted(emboldened_contours, corners, fillet)
                # A small glyph of many corners, as a raised colon's triangles, loses more ink to
                # the wider radius than it gains in weight: it keeps the radius below
                if before and ink(contours) < before["ink"]:
                    fillet = before["radius"]
                    contours = filleted(emboldened_contours, corners, fillet)
                # Still lighter, it is held as the master below drew it
                if before and ink(contours) < before["ink"]:
                    held, weight = True, before["weight"]
                    scaled, width = source.contours(cp, weight)
                    xs, ys = before["x"], before["y"]
                    contours = filleted(emboldened(scaled, xs, ys)[0], corners, fillet)
            glyph = ttglyph(contours)
            glyph.recalcBounds(glyf)
            advance = width + xs
            lsb, rsb = getattr(glyph, "xMin", 0), advance - getattr(glyph, "xMax", 0)
            if before is None:
                state[name] = {
                    "lsb": lsb,
                    "rsb": rsb,
                    "open": narrowest(openings(rounded(contours))),
                    "drawn": narrowest(openings_of(source, cp, None)) if source.weight is None else math.inf,
                    "corners": corners,
                }
            else:
                # The sidebearings are those of the lightest master: Noto Sans spaces its
                # heavier weights tighter, which would otherwise come along with them. The
                # outline moves by whole units, so it rounds as it was measured
                shift = round(state[name]["lsb"] - lsb)
                contours = [[[x + shift, y, s] for x, y, s in c] for c in contours]
                advance += shift + (state[name]["rsb"] - rsb)
                glyph = ttglyph(contours)
                glyph.recalcBounds(glyf)
            state[name].update({"x": xs, "y": ys, "weight": weight, "radius": fillet, "ink": ink(contours)})
            glyf.glyphs[name] = glyph
            order.append(name)
            hmtx[name] = (round(advance), getattr(glyph, "xMin", 0))
    master.setGlyphOrder(order)
    glyf.glyphOrder = order
    # A fresh cmap: Nunito's has no subtable for codepoints past the Basic Multilingual Plane,
    # where the mathematical alphanumerics are
    table = newTable("cmap")
    table.tableVersion = 0
    table.tables = []
    for platform, encoding, fmt in ((0, 3, 4), (0, 4, 12), (3, 1, 4), (3, 10, 12)):
        sub = CmapSubtable.newSubtable(fmt)
        sub.platformID, sub.platEncID, sub.language = platform, encoding, 0
        sub.cmap = {cp: g for cp, g in cmap.items() if fmt == 12 or cp <= 0xFFFF}
        table.tables.append(sub)
    master["cmap"] = table
    return capped


def renamed(nunito, sans, math_font):
    """Nunito's names under the new family, with the notices of all three sources"""
    name = deepcopy(nunito["name"])
    postscript = {6, 25} | {i.postscriptNameID for i in nunito["fvar"].instances}
    for record in name.names:
        if record.nameID in (0, 8, 9, 11, 12, 13, 14):
            continue
        text = record.toUnicode()
        if record.nameID in postscript or record.nameID == 3:
            text = re.sub(r"\bNunito", FAMILY.replace(" ", ""), text)
        else:
            text = re.sub(r"\bNunito\b", FAMILY, text)
        record.string = text
    versions = [f["name"].getDebugName(5).split(";")[0].removeprefix("Version ") for f in (nunito, sans, math_font)]
    description = (
        f"Nunito {versions[0]} with the Greek, arrows, operators and letterlike symbols it lacks, "
        f"taken from Noto Sans {versions[1]} and Noto Sans Math {versions[2]}, scaled to its x-height "
        "and following its weight. Merged by ddlc-themes"
    )
    for platform, encoding, language in ((3, 1, 0x409),):
        name.setName(". ".join(notices()), 0, platform, encoding, language)
        name.setName(description, 10, platform, encoding, language)
        name.setName(OFL_NOTICE, 13, platform, encoding, language)
        name.setName(OFL_URL, 14, platform, encoding, language)
    name.names.sort(key=lambda r: (r.platformID, r.platEncID, r.langID, r.nameID))
    return name


def build(style, unicodes_sans, unicodes_math, sans, math_font):
    nunito = TTFont(NUNITO[style], recalcTimestamp=False)
    ncmap = nunito.getBestCmap()
    scmap, mcmap = sans.getBestCmap(), math_font.getBestCmap()

    # The scales: Noto's x as high as Nunito's at the body weight. Noto Sans Math has one weight
    nunito_body = nunito.getGlyphSet(location={"wght": BODY_WEIGHT})
    sans_body = sans.getGlyphSet(location={"wght": BODY_WEIGHT, **SANS_WIDTH})
    sans_scale = x_height(nunito_body, ncmap) / x_height(sans_body, scmap)
    math_glyphs = math_font.getGlyphSet()
    math_scale = x_height(nunito_body, ncmap) / x_height(math_glyphs, mcmap)
    math_stems = [math_scale * s for s in stems(math_glyphs, mcmap)]

    # Noto Sans draws some glyphs at one weight whatever the axis says, the double-struck and
    # script letters among them. Those are drawn at its default weight, Regular, and emboldened
    # from Regular's stems, as Noto Sans Math is
    sans_default = sans.getGlyphSet(location={"wght": DEFAULT_SANS_WEIGHT, **SANS_WIDTH})
    sans_default_stems = [sans_scale * s for s in stems(sans_default, scmap)]
    thinnest = sans.getGlyphSet(location={"wght": 100, **SANS_WIDTH})
    heaviest = sans.getGlyphSet(location={"wght": 900, **SANS_WIDTH})
    fixed = [cp for cp in unicodes_sans if drawing(thinnest, scmap[cp]) == drawing(heaviest, scmap[cp])]
    varying = [cp for cp in unicodes_sans if cp not in set(fixed)]

    sans_sets = {}

    def sans_at(weight):
        if weight not in sans_sets:
            sans_sets[weight] = sans.getGlyphSet(location={"wght": weight, **SANS_WIDTH})
        return sans_sets[weight]

    def openings_of(source, cp, weight):
        key = (source.prefix, cp, weight, source.scale)
        if key not in OPENINGS:
            OPENINGS[key] = measured(source.contours(cp, weight)[0])
        return OPENINGS[key]

    def equals_gap(glyphset, cmap, scale=1.0):
        """The gap of an equals sign, the plainest opening between two strokes a font has"""
        return narrowest(openings(outline(glyphset, cmap[ord("=")], scale)))

    # The openings take Nunito's equals sign as their measure. The reference weight is where
    # Nunito's stem is as wide as Noto Sans Math's, so Math draws there as it is. At each
    # master an added glyph's gaps may narrow, whichever allows more:
    # - down to the share of Nunito's equals gap there that Math's equals gap is of Nunito's
    #   at the reference weight, the proportion the two families have where their stems match
    # - by as large a share of their own width at the lightest master as Nunito's equals gap
    #   has narrowed by since then, for a glyph Noto draws tighter than its own equals sign,
    #   which the first rule would hold lighter than its design at every weight
    # A glyph whose openings allow none of its strength stays as heavy as at the master below,
    # thinner than its own design if need be: an opening matters more than the stem's match
    def nunito_stem(weight):
        return stems(nunito.getGlyphSet(location={"wght": weight}), ncmap)[0]

    lo, hi = nunito["fvar"].axes[0].minValue, nunito["fvar"].axes[0].maxValue
    while hi - lo > 0.5:
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if nunito_stem(mid) < math_stems[0] else (lo, mid)
    reference_weight = round(lo)
    reference_gap = equals_gap(nunito.getGlyphSet(location={"wght": reference_weight}), ncmap)
    proportion = equals_gap(math_glyphs, mcmap, math_scale) / reference_gap
    reference_bar = stems(nunito.getGlyphSet(location={"wght": reference_weight}), ncmap)[1]

    weights = nunito_masters(nunito)
    lightest_gap = equals_gap(nunito.getGlyphSet(location={"wght": weights[0]}), ncmap)

    # The notches take Nunito's own Latin letters as their measure, as the openings take its
    # equals sign: a deep notch of an added glyph, as between the arms of a kappa, keeps as
    # large a share of its depth as Nunito's letters keep of theirs from the reference weight,
    # all but the shallowest tenth.
    # A notch is deep when it reaches further in than NOTCH_DEPTH usual strokes of Nunito's l
    # at the reference weight. A shallow one, as where a stem meets a shoulder, fills in Noto's
    # heavy weights and in the emboldened ones alike
    deep = NOTCH_DEPTH * ridge_width(outline(nunito.getGlyphSet(location={"wght": reference_weight}), ncmap[ord("l")]))
    latin = [ncmap[cp] for cp in [*range(ord("A"), ord("Z") + 1), *range(ord("a"), ord("z") + 1)]]
    nunito_notches = {}

    def notches_at(weight):
        if weight not in nunito_notches:
            glyphset = nunito.getGlyphSet(location={"wght": weight})
            nunito_notches[weight] = {g: notches(outline(glyphset, g)) for g in latin}
        return nunito_notches[weight]

    def notch_share(lighter, heavier):
        """The share of their depth the deep notches of Nunito's letters keep from one weight to
        a heavier one"""
        return kept_share(
            [
                share
                for g in latin
                for share in notch_shares(notches_at(heavier)[g], [n for n in notches_at(lighter)[g] if n[0] >= deep])
            ]
        )

    state, sources = {}, []
    for weight in weights:
        glyphs = nunito.getGlyphSet(location={"wght": weight})
        stem, bar = stems(glyphs, ncmap)
        sans_weight = matching_weight(sans, scmap, sans_scale, stem)
        sans_stems = [sans_scale * s for s in stems(sans_at(sans_weight), scmap)]
        gap = equals_gap(glyphs, ncmap)
        openness = (
            proportion * gap,
            gap / lightest_gap,
            gap / reference_gap,
            deep,
            # Only at the heaviest master: up to the middle one Nunito keeps its notches all but
            # whole, deeper than an emboldened outline can, and a notch that loses a fifth of
            # its depth there still reads, while at the heaviest an emboldened kappa loses half
            notch_share(reference_weight, weight) if weight == weights[-1] else 0.0,
        )
        master = instancer.instantiateVariableFont(nunito, {"wght": weight}, inplace=False)
        capped = add_glyphs(
            master,
            [
                Source(
                    "noto.",
                    scmap,
                    varying,
                    sans_scale,
                    sans_at,
                    sans_weight,
                    (stem - sans_stems[0], bar - sans_stems[1]),
                ),
                Source(
                    "noto.",
                    scmap,
                    fixed,
                    sans_scale,
                    lambda _: sans_default,
                    None,
                    (stem - sans_default_stems[0], bar - sans_default_stems[1]),
                ),
                Source(
                    "math.",
                    mcmap,
                    unicodes_math,
                    math_scale,
                    lambda _: math_glyphs,
                    None,
                    (stem - math_stems[0], bar - math_stems[1]),
                ),
            ],
            openness,
            (min(stem, bar), bar / reference_bar),
            # Nunito ends a stroke in a half circle at every weight: a corner rounds by half
            # its stem, which filleted() cuts to half the end where the end is narrower
            stem / 2,
            state,
            openings_of,
            DECIDED.setdefault(weight, {}),
        )
        print(
            f"mya-nunito.py: {FAMILY}{style.replace('-', ' ')} at {weight}: stem {stem:.0f}, bar {bar:.0f}; "
            f"Noto Sans {sans_weight} emboldened by {stem - sans_stems[0]:+.0f}, {bar - sans_stems[1]:+.0f}; "
            f"its {len(fixed)} glyphs of one weight and Noto Sans Math by "
            f"{stem - sans_default_stems[0]:+.0f}, {bar - sans_default_stems[1]:+.0f} and "
            f"{stem - math_stems[0]:+.0f}, {bar - math_stems[1]:+.0f}; "
            f"openings down to {openness[0]:.0f} or {openness[1]:.2f} of their own at weight {weights[0]}; "
            f"notches deeper than {deep:.0f} down to {openness[4]:.2f} of their depth as drawn; "
            f"{len(capped)} glyphs take less, to keep their openings and strokes"
        )
        sources.append((weight, master))

    # The designspace places each master where Nunito's normalized space has it, through
    # Nunito's own axis mapping, so the regions varLib builds are Nunito's
    axis = nunito["fvar"].axes[0]
    segments = sorted(nunito["avar"].segments["wght"].items())
    span = axis.maxValue - axis.defaultValue

    def design(weight):
        n = (weight - axis.defaultValue) / span
        for (a, b), (c, d) in zip(segments, segments[1:]):
            if a <= n <= c:
                return 1000 * (b + (n - a) * (d - b) / (c - a))
        raise ValueError(weight)

    doc = DesignSpaceDocument()
    ax = AxisDescriptor()
    ax.tag, ax.name = "wght", "Weight"
    ax.minimum, ax.default, ax.maximum = axis.minValue, axis.defaultValue, axis.maxValue
    ax.map = [(axis.defaultValue + a * span, 1000 * b) for a, b in segments if a >= 0]
    doc.addAxis(ax)
    for weight, master in sources:
        source = SourceDescriptor()
        source.font = master
        source.name = f"wght{weight}"
        source.location = {"Weight": design(weight)}
        doc.addSource(source)

    # varLib only warns about a glyph whose masters do not match, and leaves it with one weight
    skipped = []

    class Refuse(logging.Handler):
        def emit(self, record):
            if "incompatible" in record.getMessage():
                skipped.append(record.getMessage())

    handler = Refuse()
    logging.getLogger("fontTools.varLib").addHandler(handler)
    try:
        vf = varLib.build(doc, exclude=["GSUB", "GPOS", "GDEF", "STAT", "MVAR"])[0]
    finally:
        logging.getLogger("fontTools.varLib").removeHandler(handler)
    if skipped:
        sys.exit("mya-nunito.py: " + "; ".join(skipped))

    # Nunito's own tables and glyph variations go in as they are, so nothing of Nunito is
    # rebuilt: a delta re-derived from the masters may land half a unit off between them
    for tag in ("GSUB", "GPOS", "GDEF", "STAT", "avar"):
        vf[tag] = deepcopy(nunito[tag])
    for glyph in nunito.getGlyphOrder():
        vf["glyf"][glyph] = deepcopy(nunito["glyf"][glyph])
        vf["gvar"].variations[glyph] = deepcopy(nunito["gvar"].variations.get(glyph, []))
    vf["fvar"] = deepcopy(nunito["fvar"])
    vf["name"] = renamed(nunito, sans, math_font)
    if style:
        italic_greek(vf, ncmap)
    vf["OS/2"].recalcUnicodeRanges(vf)
    vf["OS/2"].recalcCodePageRanges(vf)
    vf.recalcTimestamp = False
    return vf


def main():
    unicodes_sans, unicodes_math = wanted_codepoints()
    sans = TTFont(SANS)
    math_font = TTFont(MATH)
    base = FAMILY.replace(" ", "")
    (outdir / f"{base}-LICENSE.txt").write_text(licence_text())
    built = {}
    for style in NUNITO:
        vf = build(style, unicodes_sans, unicodes_math, sans, math_font)
        out = outdir / f"{base}{style}.ttf"
        vf.save(out)
        built[style] = out
        packed = TTFont(out, recalcTimestamp=False)
        packed.flavor = "woff2"
        packed.save(outdir / f"{base}{style}.woff2")
    static_base = STATIC_FAMILY.replace(" ", "")
    for label, (style, weight) in STATICS.items():
        static = instancer.instantiateVariableFont(
            TTFont(built[style], recalcTimestamp=False), {"wght": weight}, updateFontNames=True
        )
        # The instancer names the face after the variable family; the static family takes
        # its own name, and drops the PostScript prefix only a variable font has
        name = static["name"]
        for record in list(name.names):
            if record.nameID == 25:
                name.removeNames(nameID=25)
                continue
            if record.nameID in (1, 4, 16, 18, 21):
                record.string = record.toUnicode().replace(FAMILY, STATIC_FAMILY)
            elif record.nameID in (3, 6, 20):
                record.string = record.toUnicode().replace(base, static_base)
        static.recalcTimestamp = False
        static.save(outdir / f"{static_base}-{label}.ttf")


if __name__ == "__main__":
    main()
