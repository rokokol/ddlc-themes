"""Draw the game menu's polka-dot paper as a looping GIF.

    python3 polka.py TILE DOT PERIOD GROUND DOTS SCALE WIDTH HEIGHT OUT

generate.sh calls this with the paper's grid and the variant's two colours as six-digit
hexes. TILE and DOT are CSS pixels, SCALE is device pixels per CSS pixel, WIDTH and HEIGHT
are device pixels.

A tile holds two dots, at a quarter and at three quarters of it on both axes. The edge of a
dot is the edge of the stylesheets' radial-gradient, which runs from the dots' colour at one
CSS pixel inside the radius to the ground at the radius, so a GIF and a page draw the same
dot. The picture holds two colours and their mixes only, so a palette of 256 steps between
them carries every edge without dithering.

The paper drifts one tile toward the bottom right per PERIOD seconds. A frame moves it one
CSS pixel, so frame k is the first frame wrapped by k steps, and the step after the last
frame is the first one again. GIF counts a frame's delay in hundredths of a second, so the
delays are spread to sum to the period exactly.
"""

import sys

from PIL import Image, ImageChops

tile, dot, period = (int(a) for a in sys.argv[1:4])
ground, dots = sys.argv[4], sys.argv[5]
scale, width, height = (int(a) for a in sys.argv[6:9])
out = sys.argv[9]


def channels(hex_colour):
    return [int(hex_colour[i : i + 2], 16) for i in (0, 2, 4)]


# Step i of the palette is i/255 of the dots over the ground, mixed in sRGB as CSS mixes
low, high = channels(ground), channels(dots)
palette = []
for i in range(256):
    palette += [(h * i + g * (255 - i) + 127) // 255 for h, g in zip(high, low)]

side = tile * scale
radius = dot * scale
centres = (side / 4, 3 * side / 4)
coverage = []
for y in range(side):
    for x in range(side):
        # A pixel is sampled at its centre, as a browser samples a gradient
        px, py = x + 0.5, y + 0.5
        cover = 0.0
        for c in centres:
            dx = min(abs(px - c), side - abs(px - c))
            dy = min(abs(py - c), side - abs(py - c))
            edge = (radius - (dx * dx + dy * dy) ** 0.5) / scale
            cover = max(cover, min(max(edge, 0.0), 1.0))
        coverage.append(round(cover * 255))

first = Image.new("P", (side, side))
first.putpalette(palette)
first.putdata(coverage)

frames = []
for step in range(tile):
    moved = ImageChops.offset(first, step * scale, step * scale)
    frame = Image.new("P", (width, height))
    frame.putpalette(palette)
    for top in range(0, height, side):
        for left in range(0, width, side):
            frame.paste(moved, (left, top))
    frames.append(frame)

# Frame k ends at hundredth floor(period * 100 * (k + 1) / tile), so the error never adds up
hundredths = [(period * 100 * (k + 1)) // tile - (period * 100 * k) // tile for k in range(tile)]

frames[0].save(
    out,
    save_all=True,
    append_images=frames[1:],
    duration=[h * 10 for h in hundredths],
    loop=0,
    optimize=False,
)
