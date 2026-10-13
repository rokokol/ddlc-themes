"""Hold the polka-dot GIFs in dist/ to the paper that ddlc-roles.json describes.

    python3 tests/polka-gifs.py DIST

The check reads the facts the pictures promise, not their bytes: dist-is-current already
compares the bytes. Each GIF loops forever, has one frame per pixel step of one tile, lasts
one drift period, shows the ground and the dots of its variant, and every frame is the one
before it moved one step toward the bottom right, the last one included.
"""

import json
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageSequence

dist = Path(sys.argv[1])
paper = json.loads((dist / "ddlc-roles.json").read_text())["polka"]
tile, period = paper["tile"], paper["period"]

# The file names are the API: a variant, then a scale for a tile or a size for a screen
pictures = {
    "ddlc-polka-{v}.gif": (1, tile, tile),
    "ddlc-polka-{v}-2x.gif": (2, 2 * tile, 2 * tile),
    "ddlc-polka-{v}-1920x1080.gif": (1, 1920, 1080),
}

failures = []


def fail(name, why):
    failures.append(f"{name}: {why}")


def rgb(hex_colour):
    return tuple(int(hex_colour[i : i + 2], 16) for i in (1, 3, 5))


for variant in ("dark", "light"):
    roles = json.loads((dist / "ddlc-roles.json").read_text())[variant]
    ground, dots = rgb(roles["ground"]), rgb(roles["dots"])
    for pattern, (scale, width, height) in pictures.items():
        name = pattern.format(v=variant)
        path = dist / name
        if not path.is_file():
            fail(name, "missing")
            continue
        with Image.open(path) as gif:
            if gif.format != "GIF":
                fail(name, f"is {gif.format}, not a GIF")
                continue
            if gif.size != (width, height):
                fail(name, f"is {gif.size}, want {(width, height)}")
            if gif.info.get("loop") != 0:
                fail(name, "does not loop forever")
            frames, total = [], 0
            for frame in ImageSequence.Iterator(gif):
                total += frame.info["duration"]
                frames.append(frame.convert("RGB"))

        if len(frames) != tile:
            fail(name, f"has {len(frames)} frames, want one per step of the tile, {tile}")
        if total != period * 1000:
            fail(name, f"lasts {total} ms, want the drift period, {period * 1000}")

        # A dot's centre sits a quarter of the tile in on both axes, and the corner between
        # the dots is bare ground
        first = frames[0]
        centre = tile * scale // 4
        if first.getpixel((centre, centre)) != dots:
            fail(name, f"shows {first.getpixel((centre, centre))} at a dot's centre, want {dots}")
        if first.getpixel((0, 0)) != ground:
            fail(name, f"shows {first.getpixel((0, 0))} on the bare ground, want {ground}")

        # Frame k+1 is frame k moved one step toward the bottom right, and the step after the
        # last frame lands back on the first, so the loop has no seam. A screen-sized frame
        # wraps by whole tiles, so the comparison runs on its first tile
        side = tile * scale
        for index, frame in enumerate(frames):
            following = frames[(index + 1) % len(frames)]
            moved = ImageChops.offset(frame.crop((0, 0, side, side)), scale, scale)
            if ImageChops.difference(moved, following.crop((0, 0, side, side))).getbbox():
                fail(name, f"frame {index + 1} is not frame {index} moved one step")
                break

for line in failures:
    print(line, file=sys.stderr)
sys.exit(1 if failures else 0)
