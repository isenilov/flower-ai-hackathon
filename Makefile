# Consortium — Federated Bid Assembly
#
# `make` on its own lists the targets. Two entry points matter:
#   make demo    — the 90-second run, start to finish
#   make check   — what to run before you push

UV         ?= uv
RUN        := $(UV) run
PORT       ?= 8000
ROUNDS     ?= 3
SUPERNODES ?= 3
SUPERLINK  ?=
OPEN       := $(if $(filter Darwin,$(shell uname -s)),open,xdg-open)

.DEFAULT_GOAL := help
.PHONY: help setup doctor run rounds baselines data build ui demo test lint fmt check clean reset

# `demo` and `check` are ordered pipelines — -j would race them.
.NOTPARALLEL:

help: ## List the targets
	@grep -hE '^[a-z][a-z-]*:.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-11s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "  Overrides: PORT=$(PORT) ROUNDS=$(ROUNDS) SUPERNODES=$(SUPERNODES) SUPERLINK=$(SUPERLINK)"
	@echo "  SUPERLINK names a connection from your Flower config; empty uses its default."

# ----------------------------------------------------------------- environment

setup: ## Install dependencies — first thing you run, and after anyone touches uv.lock
	@command -v $(UV) >/dev/null || { \
		echo "uv not found — install it: curl -LsSf https://astral.sh/uv/install.sh | sh"; \
		exit 1; }
	$(UV) sync

doctor: ## Verify the environment against the brief's §9.1 / §9.2 checklist
	@echo "python     $$($(RUN) python --version 2>/dev/null)"
	@echo "uv         $$($(UV) --version 2>/dev/null)"
	@echo "flwr       $$($(RUN) python -c 'import flwr; print(flwr.__version__)' 2>/dev/null)"
	@echo "ray        $$($(RUN) python -c 'import ray; print(ray.__version__)' 2>/dev/null)"
	@$(RUN) python -c "from flwr.cli.config_utils import load_and_validate; c, w = load_and_validate(); k = c['tool']['flwr']['app']['components']; print('app        ' + k['serverapp'] + ' / ' + k['clientapp']); print('warnings   ' + (', '.join(w) if w else 'none'))" 2>/dev/null
	@$(MAKE) --no-print-directory build
	@echo "environment is good"

# ------------------------------------------------------------------- the stack

run: rounds ## Alias for `rounds`

rounds: ## Run the federated protocol — ROUNDS rounds across SUPERNODES firm nodes
	$(RUN) flwr run . $(SUPERLINK) --stream \
		--run-config "num-rounds=$(ROUNDS)" \
		--federation-config "num-supernodes=$(SUPERNODES)"

baselines: ## Score the three conditions: isolated / consortium / centralised pool
	$(RUN) python -m backend.baselines

data: ## Regenerate the corpora — Data owner only, the R4 bio wording is hand-tuned
	$(RUN) python data/generate.py

build: ## Build the .fab bundle and throw it away, to prove it still builds
	@$(RUN) flwr build >/dev/null 2>&1 && rm -f ./*.fab && echo "fab        builds clean" \
		|| { echo "fab        FAILED — run 'uv run flwr build' for the error"; exit 1; }

ui: ## Serve the coverage matrix, ledger, and SF330 on localhost:PORT
	@echo "-> http://localhost:$(PORT)/   (ctrl-c to stop)"
	@( sleep 1 && $(OPEN) "http://localhost:$(PORT)/" >/dev/null 2>&1 & )
	@$(RUN) python -m http.server $(PORT) --directory frontend

demo: reset rounds baselines ui ## The full run: clean state -> rounds -> baselines -> UI

# --------------------------------------------------------------- dev / testing

test: ## Run the invariant tests — schema, vocabulary, and the corpus rules
	$(RUN) pytest -q

lint: ## Check formatting and lint without changing anything
	$(RUN) ruff format --check .
	$(RUN) ruff check .

fmt: ## Format and autofix. Only ever run this on files you own.
	$(RUN) ruff format .
	$(RUN) ruff check --fix .

check: lint test ## What to run before you push

# ---------------------------------------------------------------- housekeeping

reset: ## Clear run state so the demo starts from nothing
	@rm -f frontend/state/*.json
	@echo "run state cleared"

clean: reset ## reset, plus caches and build artefacts
	@rm -rf .pytest_cache .ruff_cache ./*.fab
	@find . -name __pycache__ -not -path './.venv/*' -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "caches cleared"
