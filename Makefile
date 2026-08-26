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
SCENARIO   ?=
OPEN       := $(if $(filter Darwin,$(shell uname -s)),open,xdg-open)
SCENARIO_ARG := $(if $(SCENARIO),--scenario $(SCENARIO),)
SCENARIO_SLUGS = $(shell $(RUN) python -c "from backend.scenarios import catalogue; print(' '.join(catalogue()))" 2>/dev/null)

.DEFAULT_GOAL := help
.PHONY: help setup doctor run rounds traces harness baselines data build ui watch demo test lint fmt check clean reset reset-traces publish chat

# `demo` and `check` are ordered pipelines — -j would race them.
.NOTPARALLEL:

help: ## List the targets
	@grep -hE '^[a-z][a-z-]*:.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-11s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "  Overrides: PORT=$(PORT) ROUNDS=$(ROUNDS) SUPERNODES=$(SUPERNODES) SUPERLINK=$(SUPERLINK)"
	@echo "  SCENARIO picks a corpus; empty uses the manifest default. Slugs: $(SCENARIO_SLUGS)"
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
	@$(RUN) python -c "from flwr.cli.config_utils import load_and_validate; c, w = load_and_validate(); a = c['tool']['flwr']['app']; k = a['components']; print('components ' + ', '.join(f'{n}={r}' for n, r in k.items())); print('target     flwr ' + str(a.get('flwr-version-target', 'unpinned'))); print('warnings   ' + (', '.join(w) if w else 'none'))"
	@$(MAKE) --no-print-directory build
	@echo "environment is good"

# ------------------------------------------------------------------- the stack

run: rounds ## Alias for `rounds`

rounds: ## Run the federated protocol — ROUNDS rounds across SUPERNODES firm nodes
	$(RUN) python -m backend.rounds --rounds $(ROUNDS) --supernodes $(SUPERNODES) $(SCENARIO_ARG)

traces: ## Run every scenario once, so the UI's scenario selector is fully populated
	@for slug in $(SCENARIO_SLUGS); do \
	   echo "--- $$slug"; \
	   $(RUN) python -m backend.rounds --rounds $(ROUNDS) --supernodes $(SUPERNODES) \
	     --scenario $$slug >/dev/null 2>&1 || exit 1; \
	 done
	@echo "all scenarios traced — the selector can switch between them offline"

harness: ## Run the published harness the way a judge does — on SuperGrid
	$(RUN) flwr run . $(SUPERLINK) --stream --run-config "num-rounds=$(ROUNDS)"

baselines: ## Score the three conditions: isolated / consortium / centralised pool
	$(RUN) python -m backend.baselines

data: ## Regenerate the corpora — Data owner only, the R4 bio wording is hand-tuned
	$(RUN) python data/generate.py

build: ## Build the .fab bundle and throw it away, to prove it still builds
	@$(RUN) flwr build >/dev/null 2>&1 && rm -f ./*.fab && echo "fab        builds clean" \
		|| { echo "fab        FAILED — run 'uv run flwr build' for the error"; exit 1; }

publish: check ## Publish to Flower Hub — bumps nothing, so bump `version` first for a new one
	$(RUN) flwr app publish .
	@echo "-> https://flower.ai/apps/i53n1/consortium/"

chat: ## Talk to the published harness on SuperGrid: @i53n1/consortium <solicitation>
	$(RUN) flwr chat

ui: ## Serve the coverage matrix, ledger, and SF330 on localhost:PORT
	@echo "-> http://localhost:$(PORT)/   (ctrl-c to stop)"
	@( sleep 1 && $(OPEN) "http://localhost:$(PORT)/" >/dev/null 2>&1 & )
	@$(RUN) python frontend/serve.py $(PORT)

# `rounds` then `ui` is the wrong order to watch anything: the protocol has finished before
# the page can exist. This puts the page up first and runs the protocol into it, so the
# rounds land on screen as they happen.
watch: reset ## Serve the UI, then run the protocol into it — watch the rounds land live
	@$(RUN) python frontend/serve.py $(PORT) >/dev/null 2>&1 & \
	 ui=$$!; \
	 trap "kill $$ui 2>/dev/null" EXIT INT TERM; \
	 sleep 1; \
	 echo "-> http://localhost:$(PORT)/   (the page follows the run)"; \
	 ( $(OPEN) "http://localhost:$(PORT)/" >/dev/null 2>&1 & ); \
	 sleep 2; \
	 $(RUN) python -m backend.rounds --rounds $(ROUNDS) --supernodes $(SUPERNODES) $(SCENARIO_ARG); \
	 echo ""; \
	 echo "rounds complete — page still served on :$(PORT), ctrl-c to stop"; \
	 wait $$ui

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

# Only the live trace. The per-scenario traces are the thing `make traces` builds so the
# selector can switch offline at the table — wiping those on every run defeats the point.
reset: ## Clear the live trace so a run starts from nothing
	@rm -f frontend/state/trace.jsonl
	@echo "live trace cleared"

reset-traces: ## reset, plus the per-scenario traces the selector switches between
	@rm -f frontend/state/*.jsonl frontend/state/*.json
	@echo "all traces cleared — run make traces before the demo"

clean: reset-traces ## reset-traces, plus caches and build artefacts
	@rm -rf .pytest_cache .ruff_cache ./*.fab
	@find . -name __pycache__ -not -path './.venv/*' -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "caches cleared"
