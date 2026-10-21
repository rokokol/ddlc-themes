"""Hold the symbol fonts in dist/ to what the report stylesheet declares for them.

    python3 tests/symbol-fonts.py DIST VENDOR

Nunito has no Greek to speak of, no arrows and hardly any mathematical operators, so the report
stylesheet adds two WOFF2 subsets under the same family name: Noto Sans, with its weight axis,
and Noto Sans Math for what Noto Sans lacks. The check reads the facts that make the arrangement
work, not the bytes, which dist-is-current already compares:

- the subsets hold exactly the codepoints the stylesheet gives them in unicode-range, so the
  browser neither asks a face for a glyph it lacks nor leaves one of its glyphs unused
- no codepoint is declared that Nunito has, or that both subsets have, since the later face
  would then override Nunito or the other subset
- every codepoint of the blocks the report is meant to cover is declared when either Noto font
  has it and Nunito does not
- Noto Sans keeps its weight axis and the weights Nunito's faces declare, and size-adjust
  brings the x-height of each subset to Nunito's at the body weight
"""

import re
import sys
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

dist, vendor = Path(sys.argv[1]), Path(sys.argv[2])

# The blocks the report promises, written out here on purpose and not read from the generator:
# the check is the second statement of the promise. Arrows, mathematical operators, letterlike
# symbols, super and subscripts, Greek, the phonetic modifiers of a matrix's T and an index
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

# Marks a mathematical note uses outside those blocks, each by its own reason
LOOSE = "‖′″‴⁄ⱼⱽ"

# One line of a note the report has to draw whole
SAMPLE = "Пусть λ₁ ≥ λ₂, ∀ x ∈ ℝⁿ: ‖Ax‖ ≤ σ₁‖x‖ ⇒ ∑ᵢ aᵢ² < ∞, Δ = det(A − λI), φ ↦ ∫K φ dt, Aᵀ, Mᴹ, xⱼ, ∅ ⊥ ⊕ ∘ √"

SYMBOL_FILES = {"sans": "NotoSans-Symbols.woff2", "math": "NotoSansMath-Symbols.woff2"}
FACE_STYLES = ("normal", "italic")

# How far off the x-heights may be after size-adjust: a font unit in a hundred
X_HEIGHT_TOLERANCE = 0.01

failures = []


def fail(why):
    failures.append(why)


def cmap(path):
    return set(TTFont(path, lazy=True).getBestCmap())


def ranges_to_set(text):
    out = set()
    for part in text.split(","):
        part = part.strip().removeprefix("U+")
        lo, _, hi = part.partition("-")
        out.update(range(int(lo, 16), int(hi or lo, 16) + 1))
    return out


def x_height(font, location):
    font = instancer.instantiateVariableFont(font, location, inplace=False) if location else font
    glyphs = font.getGlyphSet()
    pen = BoundsPen(glyphs)
    glyphs[font.getBestCmap()[ord("x")]].draw(pen)
    return pen.bounds[3]


css_path = dist / "ddlc-report.css"
faces = []
for block in re.findall(r"@font-face\s*\{(.*?)\}", css_path.read_text(), re.S):
    decl = dict(
        (k.strip(), v.strip()) for k, v in (line.split(":", 1) for line in block.split(";") if ":" in line)
    )
    faces.append(decl)

nunito_faces = [f for f in faces if "Symbols" not in f.get("src", "") and f.get("font-family") == "Nunito"]
if len(nunito_faces) != 2:
    fail(f"expected the two Nunito faces, found {len(nunito_faces)}")
nunito_weights = {f.get("font-weight") for f in nunito_faces}

declared = {}
for kind, name in SYMBOL_FILES.items():
    mine = [f for f in faces if name in f.get("src", "")]
    if {f.get("font-style", "normal") for f in mine} != set(FACE_STYLES):
        fail(f"{name}: expected one @font-face per style {FACE_STYLES}, found {len(mine)}")
    for f in mine:
        if f.get("font-family") != "Nunito":
            fail(f"{name}: the face is named {f.get('font-family')!r}, not Nunito")
        if f.get("font-weight") not in nunito_weights:
            fail(f"{name}: font-weight {f.get('font-weight')!r} is not the range of Nunito's faces")
        if not re.fullmatch(r"\d+(\.\d+)?%", f.get("size-adjust", "")):
            fail(f"{name}: no size-adjust in per cent")
    ranges = {f.get("unicode-range") for f in mine}
    if len(ranges) != 1 or None in ranges:
        fail(f"{name}: the faces do not share one unicode-range")
        declared[kind] = set()
    else:
        declared[kind] = ranges_to_set(ranges.pop())
    if not (dist / name).is_file():
        fail(f"{name}: missing in dist")

nunito = cmap(vendor / "nunito/Nunito-wght.ttf") | cmap(vendor / "nunito/Nunito-Italic-wght.ttf")
noto_sans = cmap(vendor / "noto-sans/NotoSans-wdth-wght.ttf")
noto_math = cmap(vendor / "noto-sans-math/NotoSansMath-Regular.ttf")

for kind, name in SYMBOL_FILES.items():
    path = dist / name
    if not path.is_file():
        continue
    inside = cmap(path) - {0}
    if inside != declared[kind]:
        extra, lacking = inside - declared[kind], declared[kind] - inside
        fail(f"{name}: holds {len(extra)} codepoints that unicode-range omits, lacks {len(lacking)} that it declares")
    if declared[kind] & nunito:
        fail(f"{name}: declares codepoints Nunito has: {sorted(map(hex, declared[kind] & nunito))[:5]}")

if declared["sans"] & declared["math"]:
    fail("both subsets declare " + ", ".join(sorted(map(hex, declared["sans"] & declared["math"]))[:5]))
if not declared["sans"] <= noto_sans:
    fail("the Noto Sans subset declares codepoints Noto Sans lacks")
if not declared["math"] <= noto_math:
    fail("the Noto Sans Math subset declares codepoints Noto Sans Math lacks")
if declared["math"] & noto_sans:
    fail("the Math subset holds codepoints Noto Sans has, which Noto Sans draws")

# Coverage: whatever a block names and a Noto font draws, and Nunito does not, is declared
wanted = {cp for lo, hi in BLOCKS.values() for cp in range(lo, hi + 1)} | {ord(c) for c in LOOSE}
undeclared = {"sans": [], "math": []}
for cp in sorted(wanted - nunito):
    source = "sans" if cp in noto_sans else "math" if cp in noto_math else None
    if source and cp not in declared[source]:
        undeclared[source].append(cp)
for source, missing in undeclared.items():
    if missing:
        first = ", ".join(f"U+{cp:04X}" for cp in missing[:5])
        fail(f"{len(missing)} codepoints of {source} that Nunito lacks are not declared, from {first}")
for label, (lo, hi) in BLOCKS.items():
    if not any(lo <= cp <= hi for cp in declared["sans"] | declared["math"]):
        fail(f"{label}: nothing declared")

for char in sorted(set(SAMPLE)):
    cp = ord(char)
    if char.isspace() or cp in nunito:
        continue
    if cp not in declared["sans"] | declared["math"]:
        fail(f"{char!r} U+{cp:04X} of the sample line is neither in Nunito nor declared")

# The weight axis survives in the Noto Sans subset, and the Math subset is its single weight
if (dist / SYMBOL_FILES["sans"]).is_file():
    sans = TTFont(dist / SYMBOL_FILES["sans"])
    axes = {a.axisTag: (a.minValue, a.maxValue) for a in sans["fvar"].axes} if "fvar" in sans else {}
    if axes.get("wght") != (100.0, 900.0):
        fail(f"{SYMBOL_FILES['sans']}: weight axis is {axes.get('wght')}, expected 100 to 900")
    if "wdth" in axes:
        fail(f"{SYMBOL_FILES['sans']}: the width axis was kept, which only costs bytes")
if (dist / SYMBOL_FILES["math"]).is_file() and "fvar" in TTFont(dist / SYMBOL_FILES["math"]):
    fail(f"{SYMBOL_FILES['math']}: Noto Sans Math has one weight and no axis")

# size-adjust: the x of each subset, scaled, stands as high as Nunito's at the body weight, 500
nunito_x = x_height(TTFont(vendor / "nunito/Nunito-wght.ttf"), {"wght": 500})
sources = {
    "sans": x_height(TTFont(vendor / "noto-sans/NotoSans-wdth-wght.ttf"), {"wght": 500, "wdth": 100}),
    "math": x_height(TTFont(vendor / "noto-sans-math/NotoSansMath-Regular.ttf"), None),
}
for kind, name in SYMBOL_FILES.items():
    for f in (f for f in faces if name in f.get("src", "")):
        adjust = float(f.get("size-adjust", "0%").rstrip("%")) / 100
        scaled = sources[kind] * adjust
        if abs(scaled - nunito_x) / nunito_x > X_HEIGHT_TOLERANCE:
            fail(f"{name}: x-height {scaled:.1f} after size-adjust, Nunito's is {nunito_x:.1f} at weight 500")

# The font's own statement of its x-height, a second measure that does not touch the outlines.
# It differs from the outline for Nunito, whose rounded x overshoots, so the margin is wider
nunito_os2 = TTFont(vendor / "nunito/Nunito-wght.ttf")["OS/2"].sxHeight
declared_os2 = {
    "sans": TTFont(vendor / "noto-sans/NotoSans-wdth-wght.ttf")["OS/2"].sxHeight,
    "math": TTFont(vendor / "noto-sans-math/NotoSansMath-Regular.ttf")["OS/2"].sxHeight,
}
for kind, name in SYMBOL_FILES.items():
    for f in (f for f in faces if name in f.get("src", "")):
        adjust = float(f.get("size-adjust", "0%").rstrip("%")) / 100
        if abs(declared_os2[kind] * adjust - nunito_os2) / nunito_os2 > 3 * X_HEIGHT_TOLERANCE:
            fail(f"{name}: sxHeight {declared_os2[kind] * adjust:.0f} after size-adjust, Nunito states {nunito_os2}")

if failures:
    print("\n".join(f"symbol-fonts: {why}" for why in failures), file=sys.stderr)
    sys.exit(1)
print(f"symbol-fonts: sans {len(declared['sans'])} codepoints, math {len(declared['math'])}, all declared and drawn")
