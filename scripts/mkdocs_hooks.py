"""MkDocs build hook (registered under `hooks:` in mkdocs.yml).

Module READMEs live outside docs/ and are pulled into docs/modules/NN.md by pymdownx.snippets.
Two things break when a page is assembled that way, and this hook fixes both:

- Images. A `![...](assets/x.svg)` in modules/NN-name/README.md resolves on GitHub but not on
  the site, because the page is docs/modules/NN.md. `on_files` registers every
  module PNG and SVG assets as the docs-relative file `modules/assets/<name>`, which is exactly
  where the snippet-included page looks for it.
- Terminal fences. termynal turns `<!-- termynal -->` fences into animated terminals, but its
  preprocessor runs before the snippet is included, so it never sees fences that live inside a
  README. Lowering its priority runs it after snippets.
"""

import html
import re
from pathlib import Path

import termynal.markdown
from mkdocs.structure.files import File

ROOT = Path(__file__).resolve().parents[1]

# termynal's preprocessor runs at priority 35, before pymdownx.snippets (32), so a
# `<!-- termynal -->` fence inside a snippet-included README is never seen. Run it after.
termynal.markdown.TERMYNAL_PREPROCESSOR_PRIORITY = 30


def on_page_content(content, **kwargs):
    """Keep commands outside Termynal's animation so copying also works during typing."""

    def add_copy(match):
        terminal = match.group(0)
        # Keep Termynal's page-load auto-initializer from starting this block
        # before it is visible; docs/js/keyboard.js initializes it on entry.
        terminal = terminal.replace('class="termy"', 'class="terminal-animation"', 1)
        inputs = re.findall(r'<span\b[^>]*data-ty="input"[^>]*>(.*?)</span>', terminal, re.S)
        commands = []
        for value in inputs:
            value = re.sub(r'<br\s*/?>', '\n', value)
            commands.append(html.unescape(re.sub(r'<[^>]+>', '', value)).strip())
        if not commands:
            return terminal
        command = html.escape('\n'.join(commands), quote=True)
        return (
            f'<div class="terminal-session" data-terminal-command="{command}">'
            '<button class="md-code__button terminal-copy" type="button" '
            'title="Copy command" aria-label="Copy command"></button>'
            '<span class="terminal-copy-status" role="status"></span>'
            f'{terminal}</div>'
        )

    return re.sub(r'<div\b[^>]*class="termy"[^>]*>.*?</div>', add_copy, content, flags=re.S)


def on_files(files, config):
    """Add module images to the build as `modules/assets/<name>` (MkDocs `on_files` event)."""
    for asset in sorted(ROOT.glob("modules/*/assets/*")):
        if asset.suffix.lower() in {".png", ".svg"}:
            files.append(File.generated(config, f"modules/assets/{asset.name}", abs_src_path=str(asset)))
    return files
