"""Hold Mya Nunito in dist/ to what it promises: Nunito, untouched, plus the Greek and
mathematics it lacks, drawn from Noto at Nunito's size and weight.

    python3 tests/mya-nunito.py fonts DIST VENDOR SRC
    python3 tests/mya-nunito.py stacks DIST

The fonts mode reads the merged fonts and takes minutes. The stacks mode reads only the
stylesheets and the matplotlib styles that name the fonts, so an edit to them checks in seconds.

src/mya-nunito.py merges the vendored Nunito with Noto Sans and Noto Sans Math into one
variable font. The check reads the facts the merge promises, not the bytes, which
dist-is-current already compares:

- each face is variable on one weight axis over Nunito's whole range, 200 to 1000
- every glyph of Nunito draws as it does in Nunito, at every master and between them, with
  Nunito's own advance, substitutions and kerning, so Latin and Cyrillic are Nunito's
- the blocks the report is meant to cover are mapped wherever Noto has a codepoint that
  Nunito lacks, and nothing Nunito maps is mapped elsewhere
- the added glyphs stand at Nunito's x-height, and grow no lighter with the weight, Noto Sans
  Math included, though it has one weight of its own; most grow heavier
- no contour of an added glyph turns inside out at any weight, and no opening between its
  strokes closes past what Nunito's own equals sign allows, or closes at all, measured by
  src/glyph_openings.py
- the usual stroke of an added glyph grows no faster than Nunito's l, so no notch between
  strokes fills to a blot, and letters once held or blotted keep pace with their neighbours
- a deep notch of a glyph of Noto Sans Math, as between the arms of a kappa, keeps as large a
  share of its depth at the heaviest weight as the deep notches of Nunito's letters keep
- the added glyphs keep their sidebearings at every weight, as Nunito's own signs do
- a Greek letter Nunito lacks is upright in the roman and its mathematical italic in the italic
- the added letters end their strokes round, as Nunito's do: the stem of φ and the curved
  tail of ς alike
- the names say Mya Nunito and carry the copyright of both projects and the OFL
- the static faces for matplotlib are the variable font at fixed weights
- the report declares one face per style under the new name, and the prose starts with it,
  a heading in the kit and the report is Doki and then the prose stack, or the prose stack
  alone under data-ddlc-heading="plain", and the matplotlib styles name the static family
  (the stacks mode)
"""

import re
import sys
import unicodedata
from pathlib import Path

from fontTools.pens.areaPen import AreaPen
from fontTools.pens.boundsPen import BoundsPen, ControlBoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont

MODES = {"fonts": 3, "stacks": 1}
if len(sys.argv) < 2 or sys.argv[1] not in MODES or len(sys.argv) != 2 + MODES[sys.argv[1]]:
    sys.exit(__doc__.split("\n\n")[1])
mode = sys.argv[1]

# The blocks the report promises, written out here on purpose and not read from the generator:
# the check is the second statement of the promise
BLOCKS = {
    "Spacing Modifier Letters": (0x02B0, 0x02FF),
    "Greek and Coptic": (0x0370, 0x03FF),
    "Phonetic Extensions": (0x1D2C, 0x1D6A),
    "Superscripts and Subscripts": (0x2070, 0x209F),
    "Letterlike Symbols": (0x2100, 0x214F),
    "Arrows": (0x2190, 0x21FF),
    "Mathematical Operators": (0x2200, 0x22FF),
    "Miscellaneous Technical": (0x2300, 0x23FF),
    "Geometric Shapes": (0x25A0, 0x25FF),
    "Miscellaneous Mathematical Symbols-A": (0x27C0, 0x27EF),
    "Supplemental Arrows-A": (0x27F0, 0x27FF),
    "Miscellaneous Mathematical Symbols-B": (0x2980, 0x29FF),
    "Supplemental Mathematical Operators": (0x2A00, 0x2AFF),
    "Mathematical Alphanumeric Symbols": (0x1D400, 0x1D7FF),
}
LOOSE = "‖′″‴⁄ⱼⱽ"

# One line of a note the report has to draw whole
SAMPLE = "Пусть λ₁ ≥ λ₂, ∀ x ∈ ℝⁿ: ‖Ax‖ ≤ σ₁‖x‖ ⇒ ∑ᵢ aᵢ² < ∞, Δ = det(A − λI), φ ↦ ∫K φ dt, Aᵀ, Mᴹ, xⱼ, aʲ, ∅ ⊥ ⊕ ∘ √"

FAMILY = "Mya Nunito"
FACES = {
    "": "nunito/Nunito-wght.ttf",
    "-Italic": "nunito/Nunito-Italic-wght.ttf",
}
# The static faces, one file each, for matplotlib, which reads no variation axis: normal and
# bold, which it asks for, and the body's Medium and the headings' Black, in both styles. They
# are a family of their own, so a system holding both sees each family once
STATIC_FAMILY = "Mya Nunito Static"
STATICS = {
    "MyaNunitoStatic-Regular.ttf": ("", 400),
    "MyaNunitoStatic-Medium.ttf": ("", 500),
    "MyaNunitoStatic-Bold.ttf": ("", 700),
    "MyaNunitoStatic-Black.ttf": ("", 900),
    "MyaNunitoStatic-Italic.ttf": ("-Italic", 400),
    "MyaNunitoStatic-MediumItalic.ttf": ("-Italic", 500),
    "MyaNunitoStatic-BoldItalic.ttf": ("-Italic", 700),
    "MyaNunitoStatic-BlackItalic.ttf": ("-Italic", 900),
}
# Where outlines are compared: Nunito's three masters, and weights between them, where a
# delta rebuilt rather than kept would show
WEIGHTS = (200, 300, 500, 700, 850, 1000)

# How far the added x-height may stand from Nunito's, as a share of it
X_HEIGHT_TOLERANCE = 0.03

# How much narrower than the promise an opening may measure. The raster has a pixel of four
# font units, and a run's ends may fall a pixel either way in each of the two measures that
# are compared, eight units in all against the narrowest promised opening, about fifty units
# at weight 1000: about a sixth
OPENING_TOLERANCE = 0.85
# The weights where openings are held, and the one they are measured against: Regular, where
# Nunito's stem is as wide as Noto Sans Math's
HEAVY = (700, 1000)
REGULAR = 400
# How much more ink than at 200 a glyph may carry and still count as held at its lightest: a
# held glyph repeats its outline at 200, and only rounding to whole units tells them apart
HELD = 1.01
# What share of the added glyphs must grow heavier from 200 to 1000: the rest are those whose
# openings or hairlines allow no weight at all, double-struck and patterned glyphs above all
MOSTLY = 0.9
# Letters once held at Regular or blotted at Black, each with a neighbour of the same alphabet:
# at each weight the usual stroke of the letter stands to the neighbour's as in Noto Sans Math,
# to the share given. A neighbour that its strokes stop thinning at 200 stands heavier there
KEEP_PACE = (("𝛼", "𝛽"), ("𝜅", "𝛽"), ("𝙈", "𝙉"))
PACE_WEIGHTS = (200, 400, 500, 700, 1000)
PACE = 0.2
# How much faster than Nunito's l from Regular an added glyph's usual stroke may grow from its
# source, in font units: the median of the ridge steps between the widths a raster holds by up
# to six pixels, and Nunito's italic l grows a few units slower than the strength it sets
BLOT_SLACK = 32
# How far the end of an added stroke may stand from Nunito's in depth, as a share of the
# stroke: a square end is about 0 deep, a half circle 0.38
CAP_TOLERANCE = 0.08
# How far from the end of φ's and l's stems and ς's tail they still run straight, in font
# units, at every weight: the bowl of φ begins about twice as far down
CAP_STRAIGHT = 140
# How far from its end the tail of ς runs straight, in font units, before its curl
TAIL_STRAIGHT = 70
# What share of the depth of Nunito's l the end of ς's tail must reach: the level cut across a
# slanting stroke measures shallower than a stem's end, and a square cut a tenth or less
TAIL_SHARE = 0.55
# How far an added sidebearing may stray from its width at 200, in font units: the outline and
# the advance each round to a whole unit
SPACING_TOLERANCE = 2

failures = []


def fail(why):
    failures.append(why)


def finish(summary):
    if failures:
        print("\n".join(f"mya-nunito: {why}" for why in failures), file=sys.stderr)
        sys.exit(1)
    print(f"mya-nunito: {summary}")
    sys.exit(0)


def stacks(dist):
    # The report declares one face per style under the new name, and the prose begins with it
    css = (dist / "ddlc-report.css").read_text()
    faces = []
    for block in re.findall(r"@font-face\s*\{(.*?)\}", css, re.S):
        faces.append(dict((k.strip(), v.strip()) for k, v in (line.split(":", 1) for line in block.split(";") if ":" in line)))
    for style in FACES:
        css_style = "italic" if style else "normal"
        mine = [f for f in faces if f.get("font-style", "normal") == css_style]
        if len(mine) != 1 or mine[0].get("font-family") != f'"{FAMILY}"':
            fail(f"ddlc-report.css: expected one {css_style} face named {FAMILY}, found {[f.get('font-family') for f in mine]}")
        elif f"MyaNunito{style}.woff2" not in mine[0].get("src", "") or mine[0].get("font-weight") != "200 1000":
            fail(f"ddlc-report.css: the {css_style} face does not load MyaNunito{style}.woff2 over 200 1000")
    prose = re.search(r"--ddlc-font-prose:\s*([^;]+);", css)
    if not prose or not prose.group(1).startswith(f"'{FAMILY}', Nunito,"):
        fail(f"ddlc-report.css: the prose stack does not begin with {FAMILY} and then Nunito")

    # A heading is Doki and then the prose face, until data-ddlc-heading="plain" on the root
    # leaves Doki out: then it is the prose stack alone, in the kit and the report alike
    for sheet in ("ddlc-ui.css", "ddlc-report.css"):
        css = (dist / sheet).read_text()
        prose = re.search(r"--ddlc-font-prose:\s*([^;]+);", css)
        heading = re.search(r"--ddlc-font-heading:\s*([^;]+);", css)
        plain = re.search(r':root\[data-ddlc-heading="plain"\]\s*\{\s*--ddlc-font-heading:\s*([^;]+);', css)
        if not (prose and heading):
            fail(f"{sheet}: no prose or heading stack")
            continue
        if not heading.group(1).startswith(f"Doki, {prose.group(1)}"):
            fail(f"{sheet}: the heading stack is {heading.group(1)!r}, not Doki and then the prose stack")
        if not plain:
            fail(f'{sheet}: data-ddlc-heading="plain" sets no heading stack')
        elif "Doki" in plain.group(1) or not plain.group(1).startswith(prose.group(1)):
            fail(f'{sheet}: data-ddlc-heading="plain" sets {plain.group(1)!r}, not the prose stack without Doki')

    # matplotlib draws the static family: of a variable font it reads the default instance
    # alone, which is ExtraLight, so the variable family has no place in its stacks
    for style_file in ("ddlc.mplstyle", "ddlc-dark.mplstyle"):
        params = dict(
            (k.strip(), v.strip())
            for k, v in (line.split(":", 1) for line in (dist / style_file).read_text().splitlines() if ":" in line and not line.startswith("#"))
        )
        stack = [f.strip() for f in params.get("font.sans-serif", "").split(",")]
        if not stack or stack[0] != STATIC_FAMILY or FAMILY in stack:
            fail(f"{style_file}: font.sans-serif is {stack}, expected {STATIC_FAMILY} first and not {FAMILY}")
        for key in ("mathtext.rm", "mathtext.it", "mathtext.bf", "mathtext.sf"):
            if params.get(key, "").split(":")[0] != STATIC_FAMILY:
                fail(f"{style_file}: {key} is {params.get(key)!r}, not {STATIC_FAMILY}")


if mode == "stacks":
    stacks(Path(sys.argv[2]))
    finish("the kit, the report and the matplotlib styles name Mya Nunito as promised")

dist, vendor, src = Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
sys.path.insert(0, str(src))
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
    ridge_width,
)
from glyph_openings import outline as contours_of  # noqa: E402


def math_italic(cp):
    """The mathematical italic codepoint of a Greek letter, by its Unicode name, or None"""
    name = unicodedata.name(chr(cp))
    for greek, math in (("GREEK SMALL LETTER ", "SMALL "), ("GREEK CAPITAL LETTER ", "CAPITAL "),
                        ("GREEK LUNATE ", ""), ("GREEK ", "")):
        if name.startswith(greek):
            try:
                return ord(unicodedata.lookup("MATHEMATICAL ITALIC " + math + name[len(greek):]))
            except KeyError:
                return None
    return None


def outline(glyphset, name):
    pen = DecomposingRecordingPen(glyphset)
    glyphset[name].draw(pen)
    return [(op, tuple((round(x, 3), round(y, 3)) for x, y in args)) for op, args in pen.value]


def cap_depth(glyphset, name, bottom=False, straight=None):
    """How far from the top of a glyph, or its bottom, the stroke that ends there reaches nearly
    all its width, as a share of the width: a half circle reaches 97 per cent at 0.38 of its
    width, a square end at once. The width is that of the first stroke from the left, across a
    horizontal line: the stem of φ or l at the top, the tail of ς, cut level, at the bottom"""
    pen = Flattener(glyphset, steps=32)
    glyphset[name].draw(pen)
    edges = [(a, b) for poly in pen.polygons for a, b in zip(poly, poly[1:] + poly[:1])]
    ys = [y for poly in pen.polygons for _, y in poly]
    end, inward = (min(ys), 1) if bottom else (max(ys), -1)

    def width(y):
        xs = sorted(ax + (y - ay) * (bx - ax) / (by - ay) for (ax, ay), (bx, by) in edges if (ay - y) * (by - y) < 0)
        return xs[1] - xs[0] if len(xs) >= 2 else 0

    # Away from the end the stroke runs straight, before φ's bowl or ς's curl widens it
    straight = straight or CAP_STRAIGHT
    full = width(end + inward * straight)
    depth = next((d for d in range(1, straight) if width(end + inward * d) >= 0.97 * full), straight)
    return depth / full


def sides(glyphset, name):
    """The left and right sidebearings, to the box of the points as TrueType keeps them: the
    box of the curves themselves moves by a unit or more as an emboldened curve bends"""
    pen = ControlBoundsPen(glyphset)
    glyphset[name].draw(pen)
    return pen.bounds[0], glyphset[name].width - pen.bounds[2]


def bounds(glyphset, name):
    pen = BoundsPen(glyphset)
    glyphset[name].draw(pen)
    return pen.bounds


def area(glyphset, name):
    pen = AreaPen(glyphset)
    glyphset[name].draw(pen)
    return abs(pen.value)


def contour_signs(glyphset, name):
    """The sign of each contour's area: a contour that turns inside out flips it"""
    pen = DecomposingRecordingPen(glyphset)
    glyphset[name].draw(pen)
    signs, current = [], None
    for op, args in pen.value:
        if op == "moveTo":
            current = AreaPen()
            current.moveTo(*args)
        elif op in ("closePath", "endPath"):
            current.closePath()
            signs.append(current.value > 0)
        else:
            getattr(current, op)(*args)
    return signs


# The OFL asks a Modified Version to keep the copyright notices of what it was made from: the
# first line of each source's licence, in the font's names and in the licence beside it
LICENCES = ("nunito/Nunito-LICENSE.txt", "noto-sans/NotoSans-LICENSE.txt", "noto-sans-math/NotoSansMath-LICENSE.txt")
NOTICES = [(vendor / path).read_text().splitlines()[0] for path in LICENCES]
licence = dist / "MyaNunito-LICENSE.txt"
if not licence.is_file():
    fail("MyaNunito-LICENSE.txt: missing in dist")
else:
    text = licence.read_text()
    for line in NOTICES:
        if line not in text:
            fail(f"MyaNunito-LICENSE.txt: lacks {line!r}")
    if "SIL OPEN FONT LICENSE Version 1.1" not in text or "5) The Font Software, modified or unmodified" not in text:
        fail("MyaNunito-LICENSE.txt: does not carry the whole OFL")

wanted = {cp for lo, hi in BLOCKS.values() for cp in range(lo, hi + 1)} | {ord(c) for c in LOOSE}
nunito_cmaps = {style: TTFont(vendor / path).getBestCmap() for style, path in FACES.items()}
have_nunito = set().union(*map(set, nunito_cmaps.values()))
have_noto = set(TTFont(vendor / "noto-sans/NotoSans-wdth-wght.ttf", lazy=True).getBestCmap())
have_noto |= set(TTFont(vendor / "noto-sans-math/NotoSansMath-Regular.ttf", lazy=True).getBestCmap())
promised = (wanted & have_noto) - have_nunito

merged = {}
for style, path in FACES.items():
    label = f"MyaNunito{style}"
    ttf, woff2 = dist / f"{label}.ttf", dist / f"{label}.woff2"
    if not (ttf.is_file() and woff2.is_file()):
        fail(f"{label}: the .ttf or the .woff2 is missing in dist")
        continue
    font, nunito = TTFont(ttf), TTFont(vendor / path)
    merged[style] = font
    packed = TTFont(woff2)
    if packed.flavor != "woff2" or packed.getBestCmap() != font.getBestCmap():
        fail(f"{label}.woff2 is not the .ttf packed")
    if packed.getGlyphOrder() != font.getGlyphOrder():
        fail(f"{label}.woff2 holds other glyphs than the .ttf")

    axes = {a.axisTag: (a.minValue, a.defaultValue, a.maxValue) for a in font["fvar"].axes} if "fvar" in font else {}
    if axes != {"wght": (200.0, 200.0, 1000.0)}:
        fail(f"{label}: axes {axes}, expected wght alone from 200 to 1000 at default 200")
    if font["avar"].segments != nunito["avar"].segments:
        fail(f"{label}: the weight axis is mapped otherwise than Nunito's")

    # Nunito, untouched: its glyphs keep their ids, their outlines, their advances, and its
    # substitutions and kerning compile to the same bytes
    order, nunito_order = font.getGlyphOrder(), nunito.getGlyphOrder()
    if order[: len(nunito_order)] != nunito_order:
        fail(f"{label}: Nunito's glyphs do not keep their ids")
    for tag in ("GSUB", "GPOS", "GDEF"):
        if tag not in font or font[tag].compile(font) != nunito[tag].compile(nunito):
            fail(f"{label}: {tag} differs from Nunito's")
    for weight in WEIGHTS:
        mine = font.getGlyphSet(location={"wght": weight})
        theirs = nunito.getGlyphSet(location={"wght": weight})
        changed = [g for g in nunito_order if outline(mine, g) != outline(theirs, g) or mine[g].width != theirs[g].width]
        if changed:
            fail(f"{label}: {len(changed)} glyphs of Nunito draw otherwise at weight {weight}, from {changed[:5]}")

    cmap = font.getBestCmap()
    moved = [cp for cp, g in nunito_cmaps[style].items() if cmap.get(cp) != g]
    if moved:
        fail(f"{label}: {len(moved)} codepoints of Nunito map to another glyph, from U+{moved[0]:04X}")
    lacking = sorted(promised - set(cmap))
    if lacking:
        fail(f"{label}: {len(lacking)} codepoints Noto has and Nunito lacks are not mapped, from U+{lacking[0]:04X}")
    for block, (lo, hi) in BLOCKS.items():
        if not any(lo <= cp <= hi for cp in cmap):
            fail(f"{label}: nothing of {block}")
    for char in sorted(set(SAMPLE) - {" "}):
        if ord(char) not in cmap:
            fail(f"{label}: {char!r} U+{ord(char):04X} of the sample line is not mapped")

    # A Greek letter Nunito lacks is upright in the roman and slanted in the italic, where it
    # draws as its mathematical italic: matplotlib sets a formula's letters in the italic, and
    # there phi keeps the loop that sets it apart from the phi symbol
    for cp in sorted(cp for cp in promised if 0x0370 <= cp <= 0x03FF and unicodedata.category(chr(cp)).startswith("L")):
        twin = math_italic(cp)
        if twin is None or twin not in cmap:
            continue
        if style and cmap.get(cp) != cmap[twin]:
            fail(f"{label}: {chr(cp)} U+{cp:04X} draws {cmap.get(cp)}, not its mathematical italic {cmap[twin]}")
        if not style and cmap.get(cp) == cmap[twin]:
            fail(f"{label}: {chr(cp)} U+{cp:04X} draws its mathematical italic in the roman")

    added = sorted({cmap[cp] for cp in set(cmap) - set(nunito_cmaps[style])})
    if not added:
        continue

    # A glyph varLib skipped for masters that do not match would keep one weight, but the
    # generator refuses that warning; a glyph its openings hold as at 200 keeps one weight by
    # design. Whether most grow heavier is checked below
    # The x-height: Noto Sans's nu and Noto Sans Math's italic x are flat-topped at their
    # x-height, and stand where Nunito's x does at the body weight
    body = font.getGlyphSet(location={"wght": 500})
    x_top = bounds(body, cmap[ord("x")])[3]
    for cp in (cp for cp in (0x03BD, 0x1D465) if cp in cmap):
        top = bounds(body, cmap[cp])[3]
        if abs(top - x_top) / x_top > X_HEIGHT_TOLERANCE:
            fail(f"{label}: U+{cp:04X} stands {top:.0f} high at weight 500, Nunito's x {x_top:.0f}")

    # Never lighter with the weight, and no contour inside out. A glyph whose openings stop it
    # may stay as it was at 200 all the way up
    sets = {w: font.getGlyphSet(location={"wght": w}) for w in (200, 500, 1000)}
    lighter = [
        g
        for g in added
        if not (area(sets[200], g) <= area(sets[500], g) * HELD and area(sets[500], g) <= area(sets[1000], g) * HELD)
    ]
    if lighter:
        fail(f"{label}: {len(lighter)} added glyphs grow lighter with the weight, from {lighter[:5]}")
    heavier = sum(area(sets[1000], g) > 1.05 * area(sets[200], g) for g in added)
    if heavier < MOSTLY * len(added):
        fail(f"{label}: only {heavier} of {len(added)} added glyphs grow heavier from 200 to 1000")
    flipped = [g for g in added if len({tuple(contour_signs(s, g)) for s in sets.values()}) != 1]
    if flipped:
        fail(f"{label}: {len(flipped)} added glyphs turn a contour inside out between weights, from {flipped[:5]}")

    # The openings. Nunito's equals sign is the measure: at a heavy weight an added glyph's
    # narrowest opening is at least the share of Nunito's equals gap there that Noto Sans
    # Math's equals gap is of Nunito's at Regular, or, for a glyph drawn tighter than that,
    # its own opening at 200, or as its source draws it at Regular, narrowed by as large a share
    # as Nunito's equals gap has since: thinning a source of one weight to 200 can widen a
    # narrow slot of the design out of the measure's sight
    def equals(glyphset, cmap, scale=1.0):
        return narrowest(openings(contours_of(glyphset, cmap[ord("=")], scale)))

    math_font = TTFont(vendor / "noto-sans-math/NotoSansMath-Regular.ttf")
    math_set, math_cmap = math_font.getGlyphSet(), math_font.getBestCmap()
    nunito_cmap = nunito.getBestCmap()
    scale = bounds(nunito.getGlyphSet(location={"wght": 500}), nunito_cmap[ord("x")])[3] / bounds(
        math_set, math_cmap[ord("x")]
    )[3]
    proportion = equals(math_set, math_cmap, scale) / equals(nunito.getGlyphSet(location={"wght": REGULAR}), nunito_cmap)
    lightest_gap = equals(nunito.getGlyphSet(location={"wght": 200}), nunito_cmap)
    regular_gap = equals(nunito.getGlyphSet(location={"wght": REGULAR}), nunito_cmap)
    own = {g: narrowest(openings(contours_of(sets[200], g))) for g in added}
    # As drawn: Noto Sans Math's glyph, and Noto Sans's at its Regular, at Nunito's x-height
    sans_font = TTFont(vendor / "noto-sans/NotoSans-wdth-wght.ttf")
    sans_set = sans_font.getGlyphSet(location={"wght": REGULAR, "wdth": 100})
    sans_scale = bounds(nunito.getGlyphSet(location={"wght": 500}), nunito_cmap[ord("x")])[3] / bounds(
        sans_font.getGlyphSet(location={"wght": 500, "wdth": 100}), sans_font.getBestCmap()[ord("x")]
    )[3]
    drawn, drawn_stroke, drawn_notches = {}, {}, {}
    for g in added:
        source, name = g.split(".", 1)
        glyphset, factor = (math_set, scale) if source == "math" else (sans_set, sans_scale)
        contours = contours_of(glyphset, name, factor)
        drawn[g], drawn_stroke[g], drawn_notches[g] = measured(contours), ridge_width(contours), notches(contours)
    for weight in HEAVY:
        heavy_set = font.getGlyphSet(location={"wght": weight})
        gap = equals(nunito.getGlyphSet(location={"wght": weight}), nunito_cmap)
        closed, lost = [], []
        for g in added:
            promise = min(proportion * gap, own[g] * gap / lightest_gap, narrowest(drawn[g]) * gap / regular_gap)
            found = measured(contours_of(heavy_set, g))
            width = narrowest(found)
            # A glyph held as light as at 200 has done what it can: its own design is tighter
            # than the promise, or the measure finds a slot only at this weight
            held = area(heavy_set, g) <= HELD * area(sets[200], g)
            if width < OPENING_TOLERANCE * promise and not held:
                closed.append(f"{g} {width:.0f} < {promise:.0f}")
            # An opening that closes leaves the measure, and the narrowest left can be wide
            if not keeps(found, drawn[g]) and not held:
                lost.append(g)
        if lost:
            fail(f"{label}: {len(lost)} added glyphs close an opening of their source at weight {weight}, from {lost[:5]}")
        if closed:
            fail(f"{label}: {len(closed)} added glyphs close their openings at weight {weight}, from {closed[:5]}")

    # The strokes. An added glyph's usual stroke grows from its source as drawn at Regular no
    # faster than Nunito's l from Regular: where it grows faster, emboldening has filled a notch
    # between strokes, as the inner V of a bold italic M, which is no opening the measure above
    # sees
    def nunito_l(weight):
        return ridge_width(contours_of(nunito.getGlyphSet(location={"wght": weight}), nunito_cmap[ord("l")]))

    for weight in HEAVY:
        heavy_set = font.getGlyphSet(location={"wght": weight})
        allowed = nunito_l(weight) - nunito_l(REGULAR)
        blotted = []
        for g in added:
            grown = ridge_width(contours_of(heavy_set, g)) - drawn_stroke[g]
            if grown > allowed + BLOT_SLACK:
                blotted.append(f"{g} +{grown:.0f}")
        if blotted:
            fail(f"{label}: {len(blotted)} added glyphs blot at weight {weight}, from {blotted[:5]}, Nunito's l +{allowed:.0f}")

    # The notches. A notch of a glyph of Noto Sans Math that reaches deeper than NOTCH_DEPTH of
    # the usual strokes of Nunito's l at Regular, as between the arms of a kappa, keeps at the heaviest weight as
    # large a share of its depth as the deep notches of Nunito's Latin letters keep of theirs
    # from Regular, all but the shallowest tenth. The stroke above misses a notch that fills
    # between short arms, which are a small part of the glyph's ridge. Lighter, Nunito keeps
    # its notches all but whole, deeper than an emboldened outline can, and Noto Sans draws its
    # own at each weight
    deep = NOTCH_DEPTH * nunito_l(REGULAR)
    latin = [nunito_cmap[cp] for cp in [*range(ord("A"), ord("Z") + 1), *range(ord("a"), ord("z") + 1)]]

    def nunito_notches(weight):
        glyphset = nunito.getGlyphSet(location={"wght": weight})
        return {g: notches(contours_of(glyphset, g)) for g in latin}

    regular_notches = nunito_notches(REGULAR)
    for weight in HEAVY[-1:]:
        heavy_notches = nunito_notches(weight)
        need = kept_share(
            [s for g in latin for s in notch_shares(heavy_notches[g], [n for n in regular_notches[g] if n[0] >= deep])]
        )
        heavy_set = font.getGlyphSet(location={"wght": weight})
        middle_set = font.getGlyphSet(location={"wght": HEAVY[-2]})
        filled = []
        for g in added:
            reference = [n for n in drawn_notches[g] if n[0] >= deep]
            # A glyph held as at the weight below has done what it can: there, where no notch
            # is held, its notches narrowed past the share already
            if not g.startswith("math.") or not reference or area(heavy_set, g) <= HELD * area(middle_set, g):
                continue
            share = min(notch_shares(notches(contours_of(heavy_set, g)), reference))
            if share < OPENING_TOLERANCE * need:
                filled.append(f"{g} {share:.2f}")
        if filled:
            fail(
                f"{label}: {len(filled)} added glyphs fill a deep notch at weight {weight}, from {filled[:5]}, "
                f"Nunito's letters keep {need:.2f} of theirs"
            )
    # Letters once held at Regular or blotted at Black keep pace with their neighbours: the
    # mathematical italic alpha and kappa beside beta, the sans-serif bold italic M beside N
    for char, neighbour in KEEP_PACE:
        if ord(char) not in cmap or ord(neighbour) not in cmap:
            continue
        mine, theirs = (ridge_width(contours_of(math_set, math_cmap[ord(c)])) for c in (char, neighbour))
        for weight in PACE_WEIGHTS:
            at = font.getGlyphSet(location={"wght": weight})
            ratio = ridge_width(contours_of(at, cmap[ord(char)])) / ridge_width(contours_of(at, cmap[ord(neighbour)]))
            if abs(ratio / (mine / theirs) - 1) > PACE:
                fail(
                    f"{label}: the stroke of {char} is {ratio:.2f} of {neighbour}'s at weight {weight}, "
                    f"{mine / theirs:.2f} in Noto Sans Math"
                )

    # The sidebearings of the added glyphs stay as at 200, as those of Nunito's own signs do,
    # each side to a unit or two of rounding
    for weight in HEAVY:
        heavy_set = font.getGlyphSet(location={"wght": weight})
        moved = [
            g
            for g in added
            if bounds(sets[200], g)
            and max(abs(a - b) for a, b in zip(sides(heavy_set, g), sides(sets[200], g))) > SPACING_TOLERANCE
        ]
        if moved:
            fail(f"{label}: {len(moved)} added glyphs change their sidebearings at weight {weight}, from {moved[:5]}")

    # Rounded as Nunito is: the end of a straight stroke of an added letter is a half circle,
    # as Nunito's l ends in one. The stem of the stroked phi rises bare above its bowl, and
    # Nunito lacks it: φ in the roman, ϕ in the italic, where φ is the looped mathematical italic
    phi_cp = 0x03D5 if style else 0x03C6
    phi = cmap.get(phi_cp)
    for weight in (400, 700, 1000) if phi else ():
        mine = cap_depth(font.getGlyphSet(location={"wght": weight}), phi)
        theirs = cap_depth(nunito.getGlyphSet(location={"wght": weight}), nunito_cmap[ord("l")])
        if abs(mine - theirs) > CAP_TOLERANCE:
            fail(f"{label}: the stem of {chr(phi_cp)} ends {mine:.2f} of its stroke deep at {weight}, Nunito's l {theirs:.2f}")

    # The end of a curved stroke rounds as well: the tail of ς, which Noto Sans cuts level where
    # it curls down. Its straight run is short, so its end is measured nearer, and it is held to
    # a share of the depth of Nunito's l rather than to it. Only in the roman: the italic ς is
    # the mathematical italic of Noto Sans Math, whose tail ends in a slanted cut that a level
    # measure cannot read, and it rounds by the same fillet this checks
    sigma = None if style else cmap.get(0x03C2)
    for weight in (400, 700, 1000) if sigma else ():
        mine = cap_depth(font.getGlyphSet(location={"wght": weight}), sigma, bottom=True, straight=TAIL_STRAIGHT)
        theirs = cap_depth(nunito.getGlyphSet(location={"wght": weight}), nunito_cmap[ord("l")])
        if mine < TAIL_SHARE * theirs:
            fail(f"{label}: the tail of ς ends {mine:.2f} of its stroke deep at {weight}, Nunito's l {theirs:.2f}")

    # The names
    name = font["name"]
    family = name.getDebugName(16) or name.getDebugName(1)
    if family != FAMILY:
        fail(f"{label}: the family is {family!r}")
    notice = name.getDebugName(0) or ""
    for line in NOTICES:
        if line not in notice:
            fail(f"{label}: the copyright notice lacks {line!r}")
    if "SIL Open Font License, Version 1.1" not in (name.getDebugName(13) or "") or not name.getDebugName(14):
        fail(f"{label}: no OFL in the licence names")
    if not re.fullmatch(r"\S+", name.getDebugName(6) or " ") or not name.getDebugName(3) or not name.getDebugName(5):
        fail(f"{label}: the PostScript name, the unique name or the version is missing or has a space")
    # The names a system or a browser finds the face by, the PostScript name of each instance
    # among them; the copyright and the description may name the sources
    identifying = {1, 3, 4, 6, 16, 21, 25} | {i.postscriptNameID for i in font["fvar"].instances}
    stray = [
        r.nameID for r in name.names if r.nameID in identifying and re.search(r"(?<!Mya )(?<!Mya)Nunito", r.toUnicode())
    ]
    if stray:
        fail(f"{label}: names {sorted(set(stray))} still call the face Nunito alone")

for file, (style, weight) in STATICS.items():
    path = dist / file
    if not path.is_file():
        fail(f"{file}: missing in dist")
        continue
    font = TTFont(path)
    if "fvar" in font or "gvar" in font:
        fail(f"{file}: still variable")
    if font["OS/2"].usWeightClass != weight:
        fail(f"{file}: weight class {font['OS/2'].usWeightClass}, expected {weight}")
    if bool(font["OS/2"].fsSelection & 1) != (style == "-Italic"):
        fail(f"{file}: the italic bit does not match the style")
    if (font["name"].getDebugName(16) or font["name"].getDebugName(1)) != STATIC_FAMILY:
        fail(f"{file}: not of the family {STATIC_FAMILY}")
    if re.search(r"Nunito(?! Static|Static| Project)", " ".join(font["name"].getDebugName(i) or "" for i in (1, 4, 6, 16))):
        fail(f"{file}: a name calls the face by the variable family's name")
    if style in merged:
        source = merged[style].getGlyphSet(location={"wght": weight})
        here = font.getGlyphSet()
        for char in "aжλ∑":
            g = font.getBestCmap()[ord(char)]
            if abs(area(here, g) - area(source, g)) > 0.01 * area(source, g):
                fail(f"{file}: {char!r} is not the variable font's at weight {weight}")

finish(f"{len(promised)} codepoints added to Nunito in both styles, its own glyphs untouched")
