#!/usr/bin/env sh
# Stage the publishable app for `flwr app publish`, and echo the directory to publish.
#
# `flwr app publish` uploads SOURCE filtered only by the extension allowlist, `.flwr/`,
# `__pycache__` and `.gitignore` — it never reads `fab-exclude`; only `flwr build` does
# (`flwr/cli/build.py`). Publishing the repo root therefore ships `docs/`, `tests/`,
# `frontend/`, `CLAUDE.md` and the slide deck's 358 KB `package-lock.json` regardless of
# what `fab-exclude` says. So copy the harness alone into a directory named for the app.
#
# The staged pyproject drops `fab-exclude` itself: Hub builds the FAB server-side, and
# `flwr build` raises on an exclude pattern that matches no file — which every pattern in
# that list would, once the paths it names are not staged.
set -eu

stage="${1:?usage: publish-stage.sh <stage-dir>}"
app="$stage/consortium"          # `flwr app publish` validates the directory name

rm -rf "$stage"
mkdir -p "$app"
cp README.md LICENSE pyproject.toml "$app/"
cp -R agents backend data "$app/"
find "$app" -name __pycache__ -type d -prune -exec rm -rf {} +

python3 - "$app/pyproject.toml" <<'PY'
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text()
stripped = re.sub(
    r"\n# Hub keeps only.*?\nfab-exclude = \[.*?\n\]\n", "\n", text, flags=re.DOTALL
)
if stripped == text:
    sys.exit("publish-stage: could not strip fab-exclude from the staged pyproject")
path.write_text(stripped)
PY

echo "$app"
