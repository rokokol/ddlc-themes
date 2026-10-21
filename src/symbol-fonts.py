"""Cut the symbols Nunito lacks out of Noto Sans and Noto Sans Math.

    python3 symbol-fonts.py VENDOR OUTDIR

Nunito draws Latin and Cyrillic well and has next to no Greek, no arrows, a handful of
operators and few super and subscripts. The report stylesheet adds two WOFF2 subsets under the
same family name, so a page that says `font-family: Nunito` gets mathematics from Noto with no
second name to write. Each codepoint of the blocks below goes to Noto Sans where Noto Sans has
it, to Noto Sans Math where only that has it, and to neither where Nunito has it already. So
the subsets never overlap each other or Nunito, and unicode-range can state them exactly.

Writes NotoSans-Symbols.woff2 and NotoSansMath-Symbols.woff2 into OUTDIR, and prints a JSON
object on stdout: per subset, the unicode-range and the size-adjust the stylesheet declares.
"""

import json
import sys
from pathlib import Path

from fontTools import subset
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

vendor, outdir = Path(sys.argv[1]), Path(sys.argv[2])

# Where the report's mathematics lives. A block is listed when a note might write a character
# from it; the codepoints a Noto font lacks, and those Nunito has, drop out on their own
BLOCKS = [
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

nunito_regular = TTFont(vendor / "nunito/Nunito-wght.ttf")
nunito_italic = TTFont(vendor / "nunito/Nunito-Italic-wght.ttf")
sans_path = vendor / "noto-sans/NotoSans-wdth-wght.ttf"
math_path = vendor / "noto-sans-math/NotoSansMath-Regular.ttf"

wanted = {cp for lo, hi in BLOCKS for cp in range(lo, hi + 1)} | set(LOOSE)
have_nunito = set(nunito_regular.getBestCmap()) | set(nunito_italic.getBestCmap())
have_sans = set(TTFont(sans_path, lazy=True).getBestCmap())
have_math = set(TTFont(math_path, lazy=True).getBestCmap())

sans_unicodes = sorted((wanted & have_sans) - have_nunito)
math_unicodes = sorted(((wanted & have_math) - have_sans) - have_nunito)


def x_height(font, location):
    """The height of a lowercase x outline, which is what a reader sees as the text's size"""
    if location:
        font = instancer.instantiateVariableFont(font, location, inplace=False)
    glyphs = font.getGlyphSet()
    pen = BoundsPen(glyphs)
    glyphs[font.getBestCmap()[ord("x")]].draw(pen)
    return pen.bounds[3] / font["head"].unitsPerEm


def size_adjust(noto, location):
    """Scale Noto so its x stands as high as Nunito's at the body weight

    Noto's x is taller than Nunito's, so at the same font-size Greek would loom over the
    Cyrillic line it stands in. The outline is measured, not OS/2 sxHeight, which states 484
    for Nunito while its x is 494 high: the rounded terminals overshoot the flat top that
    sxHeight assumes. The ratio is rounded to a tenth of a per cent
    """
    ratio = x_height(nunito_regular, {"wght": BODY_WEIGHT}) / x_height(noto, location)
    return f"{ratio * 100:.1f}%"


def cut(path, unicodes, out, pin):
    """Subset one font to the codepoints, keeping its weight axis, and write it as WOFF2"""
    font = TTFont(path, recalcTimestamp=False)
    options = subset.Options()
    options.hinting = False
    options.name_legal = True
    options.drop_tables += ["MATH", "DSIG"]
    options.recalc_timestamp = False
    subsetter = subset.Subsetter(options)
    subsetter.populate(unicodes=unicodes)
    subsetter.subset(font)
    # The subsetter keeps every codepoint that maps to a glyph it kept, so the division slash
    # rides along with the fraction slash. Such a codepoint would sit in two subsets, and the
    # stylesheet states only the codepoints given here
    keep = set(unicodes)
    for table in font["cmap"].tables:
        table.cmap = {cp: glyph for cp, glyph in table.cmap.items() if cp in keep}
    # Pinning the width axis comes after the cut: the other order leaves the variation table
    # without the glyphs the pin did not change, and the subsetter then fails on them
    if pin:
        instancer.instantiateVariableFont(font, pin, inplace=True)
    font.flavor = "woff2"
    font.save(out)


def unicode_range(unicodes):
    """The codepoints as runs, as unicode-range spells them"""
    runs, start, prev = [], None, None
    for cp in unicodes:
        if prev is None or cp != prev + 1:
            if start is not None:
                runs.append((start, prev))
            start = cp
        prev = cp
    runs.append((start, prev))
    return ",\n    ".join(
        f"U+{lo:04X}" if lo == hi else f"U+{lo:04X}-{hi:04X}" for lo, hi in runs
    )


sans_font = TTFont(sans_path)
cut(sans_path, sans_unicodes, outdir / "NotoSans-Symbols.woff2", {"wdth": 100})
cut(math_path, math_unicodes, outdir / "NotoSansMath-Symbols.woff2", None)

print(
    json.dumps(
        {
            "sans": {
                "range": unicode_range(sans_unicodes),
                "size-adjust": size_adjust(sans_font, {"wght": BODY_WEIGHT, "wdth": 100}),
            },
            "math": {
                "range": unicode_range(math_unicodes),
                "size-adjust": size_adjust(TTFont(math_path), None),
            },
        }
    )
)
