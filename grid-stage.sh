#!/usr/bin/env sh
# Stage the federated surface as its own Flower App, and echo the directory to run.
#
# The repo's FAB declares `agentapp` and nothing else, because Hub rejects a bundle
# carrying both surfaces — `422 must contain either only 'agentapp' or exactly 'serverapp'
# and 'clientapp'` — and the SuperLink derives a run's task type from that declaration
# alone (`_get_app_type`). So `flwr run .` always starts the harness in one process, no
# ClientApp ever reaches a SuperNode, and `flwr ls --format json` reports the giveaway:
# `clientapp-seconds: 0.0`.
#
# A run is not a publish, though. `flwr run <dir>` builds a FAB from that directory and
# uploads it to the SuperLink without consulting Hub, so the two surfaces can be two app
# directories even though they cannot be two components of one bundle. This stages the
# second one — exactly `serverapp` + `clientapp` — and both the coordinator and all three
# firm nodes then run on SuperGrid. That is brief §6.1's two-project fallback, kept for
# running after it was ruled out for publishing; see docs/decisions.md.
#
# Named `consortium-grid` rather than `consortium` so the federation's runs tab tells the
# two surfaces apart at a glance. It is never published, so the name costs nothing.
set -eu

stage="${1:?usage: grid-stage.sh <stage-dir>}"
app="$stage/consortium-grid"

rm -rf "$stage"
mkdir -p "$app"
cp README.md LICENSE pyproject.toml "$app/"
cp -R agents backend data "$app/"
find "$app" -name __pycache__ -type d -prune -exec rm -rf {} +

python3 - "$app/pyproject.toml" <<'PY'
import re
import sys
from pathlib import Path


def once(pattern, replacement, text, what, flags=0):
    """Substitute exactly once, and fail loudly if the anchor has moved."""
    result, count = re.subn(pattern, replacement, text, count=1, flags=flags)
    if count != 1:
        sys.exit(f"grid-stage: could not {what} in the staged pyproject")
    return result


path = Path(sys.argv[1])
text = path.read_text()

# `flwr build` raises on an exclude pattern matching no file, and none of the paths that
# list names — docs/, frontend/, tests/ — are staged here.
text = once(
    r"\n# Hub keeps only.*?\nfab-exclude = \[.*?\n\]\n", "\n", text, "strip fab-exclude", re.DOTALL
)
text = once(
    r'^name = "consortium"$', 'name = "consortium-grid"', text, "rename the project", re.M
)
text = once(
    r'^agentapp = "backend\.agent_app:app"$',
    'serverapp = "backend.server_app:app"\nclientapp = "backend.client_app:app"',
    text,
    "swap agentapp for serverapp + clientapp",
    re.M,
)
# `[tool.flwr.app.config]` is copied as it stands. `scenario` and `trace-to-log` are declared
# in the repo's own pyproject because both surfaces read them, so nothing is injected here —
# and a key added in both places would be a duplicate TOML key rather than an override.

path.write_text(text)
PY

echo "$app"
