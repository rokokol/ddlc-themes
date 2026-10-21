"""Hold Mya Nunito in dist/ to what it promises: Nunito, untouched, plus the Greek and
mathematics it lacks, drawn from Noto at Nunito's size and weight.

    python3 tests/mya-nunito.py DIST VENDOR SRC

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
  strokes closes past what Nunito's own equals sign allows, measured by src/glyph_openings.py
- the added glyphs keep their sidebearings at every weight, as Nunito's own signs do
- the names say Mya Nunito and carry the copyright of both projects and the OFL
- the static faces for matplotlib are the variable font at fixed weights
- the report declares one face per style under the new name, and the prose starts with it
"""

import re
import sys
from pathlib import Path

from fontTools.pens.areaPen import AreaPen
from fontTools.pens.boundsPen import BoundsPen, ControlBoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont

dist, vendor, src = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
sys.path.insert(0, str(src))
from glyph_openings import narrowest, openings  # noqa: E402
from glyph_openings import outline as contours_of  # noqa: E402

# The blocks the report promises, written out here on purpose and not read from the generator:
# the check is the second statement of the promise
BLOCKS = {
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
SAMPLE = "Пусть λ₁ ≥ λ₂, ∀ x ∈ ℝⁿ: ‖Ax‖ ≤ σ₁‖x‖ ⇒ ∑ᵢ aᵢ² < ∞, Δ = det(A − λI), φ ↦ ∫K φ dt, Aᵀ, Mᴹ, xⱼ, ∅ ⊥ ⊕ ∘ √"

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
# How far an added sidebearing may stray from its width at 200, in font units: the outline and
# the advance each round to a whole unit
SPACING_TOLERANCE = 2

failures = []


def fail(why):
    failures.append(why)


def outline(glyphset, name):
    pen = DecomposingRecordingPen(glyphset)
    glyphset[name].draw(pen)
    return [(op, tuple((round(x, 3), round(y, 3)) for x, y in args)) for op, args in pen.value]


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
    # its own opening at 200 narrowed by as large a share as Nunito's equals gap has
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
    own = {g: narrowest(openings(contours_of(sets[200], g))) for g in added}
    for weight in HEAVY:
        heavy_set = font.getGlyphSet(location={"wght": weight})
        gap = equals(nunito.getGlyphSet(location={"wght": weight}), nunito_cmap)
        closed = []
        for g in added:
            promise = min(proportion * gap, own[g] * gap / lightest_gap)
            width = narrowest(openings(contours_of(heavy_set, g)))
            # A glyph held as light as at 200 has done what it can: its own design is tighter
            # than the promise, or the measure finds a slot only at this weight
            held = area(heavy_set, g) <= HELD * area(sets[200], g)
            if width < OPENING_TOLERANCE * promise and not held:
                closed.append(f"{g} {width:.0f} < {promise:.0f}")
        if closed:
            fail(f"{label}: {len(closed)} added glyphs close their openings at weight {weight}, from {closed[:5]}")

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

# matplotlib draws the static family: of a variable font it reads the default instance alone,
# which is ExtraLight, so the variable family has no place in its stacks
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

if failures:
    print("\n".join(f"mya-nunito: {why}" for why in failures), file=sys.stderr)
    sys.exit(1)
print(f"mya-nunito: {len(promised)} codepoints added to Nunito in both styles, its own glyphs untouched")
