"""MkDocs build hook (registered under `hooks:` in mkdocs.yml).

Module READMEs live outside docs/ and are pulled into docs/modules/NN.md by pymdownx.snippets.
Two things break when a page is assembled that way, and this hook fixes both:

- Images. A `![...](assets/x.png)` in modules/NN-name/README.md resolves on GitHub but not on
  the site, because the page is docs/modules/NN.md. `on_files` registers every
  modules/*/assets/*.png as the docs-relative file `modules/assets/<name>`, which is exactly
  where the snippet-included page looks for it.
- Terminal fences. termynal turns `<!-- termynal -->` fences into animated terminals, but its
  preprocessor runs before the snippet is included, so it never sees fences that live inside a
  README. Lowering its priority runs it after snippets.
"""

from pathlib import Path

import termynal.markdown
from mkdocs.structure.files import File

ROOT = Path(__file__).resolve().parents[1]

# termynal's preprocessor runs at priority 35, before pymdownx.snippets (32), so a
# `<!-- termynal -->` fence inside a snippet-included README is never seen. Run it after.
termynal.markdown.TERMYNAL_PREPROCESSOR_PRIORITY = 30


def on_files(files, config):
    """Add every module diagram PNG to the build as `modules/assets/<name>` (MkDocs `on_files` event)."""
    for png in sorted(ROOT.glob("modules/*/assets/*.png")):
        files.append(File.generated(config, f"modules/assets/{png.name}", abs_src_path=str(png)))
    return files
