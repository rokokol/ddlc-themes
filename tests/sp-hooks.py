"""Hold the Super Productivity theme to the Super Productivity it is written for.

    python3 tests/sp-hooks.py THEME.css SP_SOURCE

THEME.css is dist/ddlc-super-productivity.css and SP_SOURCE the app's source tree at the
version the flake's nixpkgs builds. A rule that names a class, a component or a variable the
app has dropped stops applying in silence, and only an eye on the app would notice; this check
notices on the lock bump that brings the new version.

What the theme hooks into, and how each is found in the source:
- a component, such as task or banner, by its `selector: '...'` in a TypeScript file
- a class or a body flag, such as status-bar or hasBgImage, as a whole word in the source
- a variable the theme sets, by a `var(--name` that reads it
- a variable the theme reads and does not set, by a `--name:` that sets it

Angular Material's classes and variables, mat-* and mdc-*, and the palette variables,
palette-*, that angular-material-css-vars writes, live in those packages rather than in the
app's source. One the app's source names passes; any other is listed as not checked here
instead of passing in silence.
"""

import re
import sys
from pathlib import Path

theme = Path(sys.argv[1]).read_text()
source = Path(sys.argv[2])

# Plain HTML elements, which any page has
HTML = {"body", "header", "nav", "main", "div", "span", "button", "a", "ul", "li", "section"}
MATERIAL = re.compile(r"^-*(mat|mdc|palette)-")

text = []
for path in sorted(source.joinpath("src").rglob("*")):
    if path.suffix in {".ts", ".html", ".scss", ".css"} and "node_modules" not in path.parts:
        text.append(path.read_text(errors="replace"))
corpus = "\n".join(text)
words = set(re.findall(r"[A-Za-z_][\w-]*", corpus))
components = set()
for value in re.findall(r"selector:\s*'([^']+)'", corpus):
    components.update(s.strip() for s in value.split(","))
read_vars = set(re.findall(r"var\(\s*(--[\w-]+)", corpus))
set_vars = set(re.findall(r"(--[\w-]+)\s*:", corpus))

css = re.sub(r"/\*.*?\*/", "", theme, flags=re.S)
preludes = re.findall(r"([^{}]+)\{", css)
declared = set(re.findall(r"(--[\w-]+)\s*:", css))
used = set(re.findall(r"var\(\s*(--[\w-]+)", css))

missing, unchecked = [], set()


def want(name, found, what, where):
    """A hook the app's source holds passes; a Material one it does not is only listed"""
    if found:
        return
    if MATERIAL.match(name.lstrip(".")):
        unchecked.add(name)
    else:
        missing.append(f"{what} — {where.strip()}")


for prelude in preludes:
    for selector in prelude.split(","):
        selector = selector.strip()
        if not selector:
            continue
        # Attribute tests and pseudo-classes are the theme's own, not hooks into the app
        bare = re.sub(r"\[[^\]]*\]|::?[\w-]+(\([^)]*\))?", "", selector)
        for name in re.findall(r"\.([\w-]+)", bare):
            want(f".{name}", name in words, f"class .{name}", selector)
        for name in re.findall(r"(?:^|[\s>+~])([a-z][\w-]*)", bare):
            if name not in HTML:
                want(name, name in components, f"component <{name}>", selector)

for name in sorted(declared):
    if not name.startswith("--ddlc-"):
        want(name, name in read_vars, f"variable {name} that nothing reads", "set in the theme")

for name in sorted(used - declared):
    want(name, name in set_vars, f"variable {name} that nothing sets", "read by the theme")

for line in missing:
    print(f"sp-hooks: the app has no {line}", file=sys.stderr)
print(f"sp-hooks: not checked here, Angular Material's: {', '.join(sorted(unchecked))}")
sys.exit(1 if missing else 0)
