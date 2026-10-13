"""Take the README's Super Productivity pictures: docs/super-productivity-<variant>.png.

nix run .#sp-demo                 both variants, from the checkout in the current directory
nix run .#sp-demo -- dark         one variant

The flake's app brings Super Productivity's web build out of the locked nixpkgs, and
Playwright with its browsers from the same revision; run by hand, SP_WEB names that build and
PLAYWRIGHT_BROWSERS_PATH the browsers. The page is a fresh in-memory profile, so no one's own
data is touched. The theme is dist/ddlc-super-productivity.css and the background a project's
image of the polka-dot paper, so dist/ must be rendered first. One frame shows the parts the
theme draws: open and done tasks over the paper, the update banner and a snack.
"""

import functools
import http.server
import os
import sys
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

repo = Path.cwd()
dist = repo / "dist"
web = Path(os.environ["SP_WEB"])
theme = (dist / "ddlc-super-productivity.css").read_text()
variants = sys.argv[1:] or ["light", "dark"]


class Handler(http.server.SimpleHTTPRequestHandler):
    """SP's build at the root, dist/ under /ddlc/ for the background picture"""

    def translate_path(self, path):
        if path.startswith("/ddlc/"):
            return str(dist / path.removeprefix("/ddlc/").split("?")[0])
        return super().translate_path(path)

    def log_message(self, format, *args):
        pass


server = http.server.ThreadingHTTPServer(
    ("127.0.0.1", 0), functools.partial(Handler, directory=str(web))
)
threading.Thread(target=server.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{server.server_port}/"

# SP opens no banner on demand in its web build, so the update banner's markup goes into the
# empty host, under the component's own scope attribute, which its stylesheet selects on
BANNER = """() => {
  const host = document.querySelector('banner');
  const scope = [...host.attributes].find(a => a.name.startsWith('_nghost-')).name.replace('_nghost-', '_ngcontent-');
  const button = label => `<button class="mdc-button mat-mdc-button mat-mdc-button-base mat-primary"><span class="mdc-button__label">${label}</span></button>`;
  host.innerHTML = `<div class="content-wrapper"><div class="inner-content-wrapper">
    <div class="message-wrapper"><mat-icon class="mat-icon notranslate material-icons mat-ligature-font">file_download</mat-icon>
    <div class="message">A new version of Super Productivity is available (v19.2.0).</div></div>
    <div class="buttons">${button('Download')}${button('Dismiss')}</div></div></div>`;
  host.querySelectorAll('*').forEach(e => e.setAttribute(scope, ''));
}"""


def set_background(page, picture):
    """Open the inbox's project settings and set its background image for both modes"""
    page.get_by_text("Inbox", exact=True).first.click(button="right")
    page.wait_for_timeout(800)
    page.get_by_role("menuitem", name="Settings").last.click()
    page.wait_for_timeout(1200)
    for side in ("Dark", "Light"):
        page.get_by_label(f"Background Image URL ({side} Theme)").fill(url + picture)
    page.get_by_role("button", name="Save").click()


with sync_playwright() as p:
    browser = p.chromium.launch()
    for variant in variants:
        page = browser.new_page(viewport={"width": 1280, "height": 800}, color_scheme=variant)
        page.goto(url)
        page.wait_for_timeout(3000)
        page.get_by_text("Simple Todo List").click()
        page.wait_for_timeout(1500)
        page.add_style_tag(content=theme)
        page.get_by_text("Inbox", exact=True).first.click()
        page.wait_for_timeout(1500)
        for _ in range(2):
            page.locator("task:not(.isDone) done-toggle").last.click()
            page.wait_for_timeout(1200)
        paper = f"ddlc/ddlc-polka-{variant}-1920x1080.webp"
        set_background(page, paper)
        page.wait_for_timeout(1500)
        hint = page.get_by_text("✕")
        if hint.count():
            hint.first.click()
            page.wait_for_timeout(600)
        page.evaluate(BANNER)
        # A second save with a changed value raises the snack the frame shows
        set_background(page, paper + "?again")
        page.wait_for_timeout(700)
        page.mouse.move(1270, 790)
        page.screenshot(path=str(repo / "docs" / f"super-productivity-{variant}.png"))
        page.close()
    browser.close()
server.shutdown()
