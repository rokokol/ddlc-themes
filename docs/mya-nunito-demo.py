"""Take the README's Mya Nunito pictures: docs/mya-nunito-<variant>.png.

nix shell nixpkgs#chromium -c python3 docs/mya-nunito-demo.py          both variants
nix shell nixpkgs#chromium -c python3 docs/mya-nunito-demo.py dark     one variant

Run it from the checkout, after dist/ is rendered. It serves the checkout over HTTP and has a
headless Chromium take docs/mya-nunito-demo.html, so no window opens. $CHROMIUM names another
browser binary. The browser gets a fresh profile, so no one's own profile is touched. The
fallback in the Nunito rows is whatever system font the browser picks for a sign Nunito lacks.
"""

import functools
import http.server
import os
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

repo = Path.cwd()
variants = sys.argv[1:] or ["light", "dark"]
browser = os.environ.get("CHROMIUM", "chromium")
# Wide enough for the line at the heaviest weight, high enough for both faces
SIZE = "1110,310"


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Handler, directory=str(repo)))
threading.Thread(target=server.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{server.server_port}/docs/mya-nunito-demo.html"

for variant in variants:
    out = repo / "docs" / f"mya-nunito-{variant}.png"
    with tempfile.TemporaryDirectory() as profile:
        shot = subprocess.run(
            [
                browser,
                "--headless=new",
                f"--user-data-dir={profile}",
                "--no-first-run",
                "--hide-scrollbars",
                "--force-device-scale-factor=1",
                # Time for the stylesheet and the fonts to load before the shot
                "--virtual-time-budget=5000",
                f"--window-size={SIZE}",
                f"--screenshot={out}",
                f"{url}?theme={variant}",
            ],
            capture_output=True,
            text=True,
        )
    # Chromium chats on stderr even when it succeeds, so it is shown only on a failure
    if shot.returncode != 0 or not out.is_file():
        sys.exit(f"mya-nunito-demo: {browser} failed for {variant}:\n{shot.stderr}")
    print(f"wrote {out.relative_to(repo)}")
server.shutdown()
