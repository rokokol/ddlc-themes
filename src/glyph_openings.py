"""The openings between the strokes of a glyph, and the usual width of its strokes, measured
on a raster.

src/mya-nunito.py keeps the openings of the glyphs it adds from closing, and the notches
between their strokes from filling, as they grow heavier, and tests/mya-nunito.py checks that
they did not, both with these measures.
"""

import math

import numpy as np
from fontTools.pens.basePen import BasePen
from fontTools.pens.pointPen import DecomposingPointPen, PointToSegmentPen
from scipy import ndimage
from scipy.spatial import ConvexHull

# How fine an outline is rasterized to measure the openings between its strokes, in font units
RASTER = 4
# The widest opening worth measuring, in font units: wider than any emboldening takes away
WIDEST = 400
# How many times longer than wide white must run to be a slot between strokes. A corner whose
# sides meet at an angle above 2·atan(1 / (2·SLOT)), 14 degrees, holds short runs over a
# shorter stretch than that, and only sides that run almost parallel count
SLOT = 4
# How long a slot runs at the least, in font units: about the widest stem of a heavy text face.
# Where two strokes join at a narrow angle, a raster leaves a sliver a pixel or two wide that
# runs a few pixels, which no reader sees as an opening
SLOT_REACH = 120
# The smallest counter worth measuring, in pixels: where overlapping contours meet, a raster
# can leave a speck of white a pixel or two across inside the ink, which is no counter
SPECK = 9
# How far apart two separate parts of ink must stand to leave an opening between them, in font
# units: three pixels of the raster, a fifth of a pixel at 16 px. Closer parts touch at any
# size a reader sees, and the raster's pixel of error on each edge hides the rest
JOIN = 3 * RASTER
# The least depth of ink, in pixels from the nearest white, that the medial ridge counts: the
# ragged edge of a raster has peaks of its own a pixel or two deep
RIDGE_DEPTH = 2
# How deep a notch must reach in from the edge of a glyph's convex hull to be kept, in usual
# strokes of the font's l: deeper than where a stem meets a shoulder, which reaches a stroke or
# a little more, and as deep as between the arms of a k
NOTCH_DEPTH = 1.5


class Flattener(BasePen):
    """An outline as polygons, each curve cut into straight pieces"""

    def __init__(self, glyphset, steps=32):
        super().__init__(glyphset)
        self.steps = steps
        self.polygons, self.current = [], []

    def _moveTo(self, pt):
        self.current = [pt]

    def _lineTo(self, pt):
        self.current.append(pt)

    def _qCurveToOne(self, pt1, pt2):
        (x0, y0), (x1, y1), (x2, y2) = self._getCurrentPoint(), pt1, pt2
        for i in range(1, self.steps + 1):
            t = i / self.steps
            u = 1 - t
            self.current.append((u * u * x0 + 2 * u * t * x1 + t * t * x2, u * u * y0 + 2 * u * t * y1 + t * t * y2))

    def _curveToOne(self, pt1, pt2, pt3):
        (x0, y0), (x1, y1), (x2, y2), (x3, y3) = self._getCurrentPoint(), pt1, pt2, pt3
        for i in range(1, self.steps + 1):
            t = i / self.steps
            u = 1 - t
            self.current.append(
                (
                    u**3 * x0 + 3 * u * u * t * x1 + 3 * u * t * t * x2 + t**3 * x3,
                    u**3 * y0 + 3 * u * u * t * y1 + 3 * u * t * t * y2 + t**3 * y3,
                )
            )

    def _closePath(self):
        self.polygons.append(self.current)
        self.current = []

    _endPath = _closePath


class Contours(DecomposingPointPen):
    """A glyph's contours as lists of [x, y, segment type], components drawn in place"""

    skipMissingComponents = False

    def __init__(self, glyphset):
        super().__init__(glyphset, reverseFlipped=True)
        self.contours = []

    def beginPath(self, identifier=None, **kwargs):
        self.contours.append([])

    def addPoint(self, pt, segmentType=None, smooth=False, name=None, identifier=None, **kwargs):
        self.contours[-1].append([pt[0], pt[1], segmentType])

    def endPath(self):
        pass


def outline(glyphset, name, scale=1.0):
    """A glyph's contours, scaled about the origin"""
    pen = Contours(glyphset)
    glyphset[name].drawPoints(pen)
    return [[[x * scale, y * scale, s] for x, y, s in contour] for contour in pen.contours]


def raster(contours):
    """The contours filled by the non-zero rule, as TrueType fills overlapping contours, on a
    grid of RASTER units, with a white margin"""
    pen = Flattener(None, steps=8)
    points = PointToSegmentPen(pen)
    for contour in contours:
        points.beginPath()
        for x, y, segment in contour:
            points.addPoint((x, y), segment)
        points.endPath()
    edges = [(*a, *b) for polygon in pen.polygons for a, b in zip(polygon, polygon[1:] + polygon[:1])]
    if not edges:
        return None
    x0, y0, x1, y1 = np.array(edges, float).T
    left, bottom = min(x0.min(), x1.min()), min(y0.min(), y1.min())
    margin = 2
    width = int((max(x0.max(), x1.max()) - left) / RASTER) + 2 * margin + 1
    height = int((max(y0.max(), y1.max()) - bottom) / RASTER) + 2 * margin + 1
    image = np.zeros((height, width), bool)
    centres = (np.arange(width) - margin + 0.5) * RASTER + left
    for row in range(margin - 1, height - margin + 1):
        y = (row - margin + 0.5) * RASTER + bottom
        up, down = (y0 <= y) & (y1 > y), (y1 <= y) & (y0 > y)
        crossing = up | down
        if not crossing.any():
            continue
        t = (y - y0[crossing]) / (y1[crossing] - y0[crossing])
        xs = x0[crossing] + t * (x1[crossing] - x0[crossing])
        order = np.argsort(xs, kind="stable")
        winding = np.cumsum(np.where(up[crossing], 1, -1)[order])
        at = np.searchsorted(xs[order], centres, side="right")
        image[row] = np.where(at > 0, winding[np.maximum(at - 1, 0)], 0) != 0
    return image


def bounded_runs(image):
    """For each white pixel, the length of its run along the row when ink ends it on both
    sides, and 0 where the run reaches the margin"""
    out = np.zeros(image.shape, np.int32)
    for row, line in enumerate(image):
        edges = np.flatnonzero(np.diff(line.astype(np.int8)))
        # A white run starts after ink ends and stops where ink starts again
        starts, stops = edges[line[edges]] + 1, edges[~line[edges]] + 1
        for start in starts:
            after = stops[stops > start]
            if after.size:
                out[row, start : after[0]] = after[0] - start
    return out


def openings(contours):
    """The openings between the strokes of an outline, each as (width, axis), in font units

    - a counter, white enclosed by ink, measures the widest circle it holds; it narrows across
      its short side, so its axis is y when it is wider than tall
    - a slot, white between strokes and open at an end as in a double arrow, is a run of white
      with ink at both ends, along one axis, and its neighbours no longer than it, standing at
      least SLOT times its length and SLOT_REACH long across that axis: the shortest such run
      measures the slot. A corner where two strokes meet holds short runs too, but over a
      shorter stretch, so it does not count
    - separate parts of a glyph, as the bar under a subset sign, measure their closest approach,
      unless they come closer than JOIN: then they are one stroke drawn in two pieces, as the
      tail of a mathematical italic alpha against its bowl
    """
    return [(width, axis) for width, axis, _ in measured(contours)]


def keeps(found, reference):
    """Whether the openings measured() found keep every opening of the reference: as many
    counters and slots together, since a slot whose open end closes becomes a counter, and as
    many separate parts. An opening that closes leaves the measure's sight, and the narrowest
    opening left can still be wide"""
    parts = [sum(kind == "part" for *_, kind in f) for f in (found, reference)]
    return len(found) - parts[0] >= len(reference) - parts[1] and parts[0] >= parts[1]


def measured(contours):
    """The openings of an outline as openings() finds them, each as (width, axis, kind), the
    kind a counter, a slot or a part"""
    image = rastered(contours)
    if image is None:
        return []
    found = []
    white, _ = ndimage.label(~image)
    outside = white[0, 0]
    distance = ndimage.distance_transform_edt(~image)
    holes = np.zeros_like(image)
    for label, box in enumerate(ndimage.find_objects(white), 1):
        if label == outside or box is None:
            continue
        region = white[box] == label
        holes[box] |= region
        if region.sum() < SPECK:
            continue
        rows, cols = box[0].stop - box[0].start, box[1].stop - box[1].start
        found.append((2 * distance[box][region].max() * RASTER, "y" if cols >= rows else "x", "counter"))
    found += [(width, axis, "slot") for width, axis in slots(image, holes)]
    parts, count = ndimage.label(image)
    for part in range(1, count):
        apart = ndimage.distance_transform_edt(parts != part)
        gap = apart[(parts > part)].min() * RASTER
        if gap >= JOIN:
            found.append((gap, "xy", "part"))
    return found


def slots(image, skip):
    """The narrowest long run of white between ink along each axis, as (width, axis)

    Pixels in skip are left out. A slot runs at least SLOT times its width and SLOT_REACH long
    across its axis, so a corner's short runs do not count
    """
    reach = SLOT_REACH
    found = []
    for axis, grid in (("x", image), ("y", image.T)):
        runs = bounded_runs(grid)
        if axis == "y":
            runs = runs.T
        runs[skip] = 0
        across = 0 if axis == "x" else 1
        # A region of short runs only shrinks as the length falls, so a region too short to
        # reach at the longest length never holds a slot, and its runs need no trying
        candidates = (runs > 0) & (runs <= WIDEST // RASTER)
        regions, _ = ndimage.label(candidates)
        for label, box in enumerate(ndimage.find_objects(regions), 1):
            if box is not None and box[across].stop - box[across].start < reach / RASTER:
                candidates[box] &= regions[box] != label
        for length in np.unique(runs[candidates]):
            regions, _ = ndimage.label(candidates & (runs <= length))
            least = max(SLOT * length, reach / RASTER)
            if any(box[across].stop - box[across].start >= least for box in ndimage.find_objects(regions)):
                found.append((int(length) * RASTER, axis))
                break
    return found


def strokes(contours):
    """The thinnest long strokes of an outline, as (width, axis): the slots of its ink"""
    image = rastered(contours)
    if image is None:
        return []
    return slots(~image, np.zeros_like(image))


def ridge_width(contours):
    """The usual width of an outline's strokes, in font units: the median width of the ink
    along its medial ridge, where the distance to the nearest white peaks

    Emboldening by a strength widens each stroke by about that strength. Where it fills a
    notch between two strokes, as the inner V of a bold italic M, the two strokes become one
    mass wider than either, and the median grows faster than the strength
    """
    image = rastered(contours)
    if image is None:
        return 0.0
    depth = ndimage.distance_transform_edt(image)
    ridge = (depth >= ndimage.maximum_filter(depth, size=3)) & (depth > RIDGE_DEPTH)
    if not ridge.any():
        return 0.0
    return float(np.median(2 * depth[ridge] * RASTER))


def notches(contours):
    """The notches of an outline: white inside the convex hull of its ink that opens to the
    outside, as between the arms of a k, each as (depth, x, y) in font units. The depth is how
    far the notch reaches in from the edge of the hull, and x and y are where it reaches
    deepest, from the middle of the raster, which emboldening keeps in place"""
    image = rastered(contours)
    if image is None or image.sum() < 3:
        return []
    rows, cols = np.nonzero(image)
    if len(set(rows)) < 2 or len(set(cols)) < 2:
        return []
    hull = ConvexHull(np.c_[cols, rows].astype(float))
    grid_rows, grid_cols = np.mgrid[: image.shape[0], : image.shape[1]]
    inside = np.ones(image.shape, bool)
    for a, b, c in hull.equations:
        inside &= a * grid_cols + b * grid_rows + c <= 0.5
    white, _ = ndimage.label(~image)
    labels, count = ndimage.label(inside & (white == white[0, 0]))
    depth = ndimage.distance_transform_edt(inside)
    middle = (np.array(image.shape) - 1) / 2
    found = []
    for label, box in enumerate(ndimage.find_objects(labels), 1):
        region = labels[box] == label
        if region.sum() < SPECK:
            continue
        local = np.where(region, depth[box], 0)
        row, col = np.unravel_index(local.argmax(), local.shape)
        row, col = row + box[0].start, col + box[1].start
        found.append((depth[row, col] * RASTER, (col - middle[1]) * RASTER, (row - middle[0]) * RASTER))
    return found


def notch_shares(found, reference):
    """For each notch of the reference, the share of its depth that the notch found nearest
    its deepest point keeps, 0 where no notch of found reaches within the reference's depth"""
    shares = []
    for depth, x, y in reference:
        near = [d for d, u, v in found if math.hypot(u - x, v - y) <= depth]
        shares.append(max(near, default=0.0) / depth)
    return shares


def kept_share(shares):
    """The share of their depth that all but the shallowest tenth of a set of notches keep: the
    measure a font's own letters set for notches. Their least share is an outlier, as where the
    crossbar of a t grows over its notch"""
    ordered = sorted(shares)
    return min(ordered[len(ordered) // 10], 1.0) if ordered else 1.0


def parts(contours):
    """How many separate pieces of ink an outline draws"""
    image = rastered(contours)
    return 0 if image is None else ndimage.label(image)[1]


def rastered(contours):
    """The raster of contours, or the raster itself when given one, so that one outline is
    rasterized once for several measures"""
    return contours if isinstance(contours, np.ndarray) else raster(contours)


def narrowest(found):
    return min((width for width, *_ in found), default=math.inf)
