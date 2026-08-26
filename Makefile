# Consortium — Federated Bid Assembly
#
# `make` on its own lists the targets. Two entry points matter:
#   make demo    — the 90-second run, start to finish
#   make check   — what to run before you push

UV         ?= uv
RUN        := $(UV) run

# `.env` holds the model endpoint and its key — per-machine and secret, so gitignored. Read
# here so `doctor` and `stage` can report what a run will actually use, and exported so a
# recipe's subprocesses inherit it. `?=` throughout, so an exported shell variable still wins.
# `backend/dotenv.py` reads the same file for runs started from the page's Run button, which
# `frontend/serve.py` spawns from whatever shell started it.
ifneq (,$(wildcard .env))
include .env
export
endif
PORT       ?= 8000
SLIDES     := docs/slides
PUBDIR     := .publish-stage
SLIDE_PORT ?= 3030
ROUNDS     ?= 3
SUPERNODES ?= 3
# `supergrid`, not empty. An empty SUPERLINK resolves to whatever `~/.flwr/config.toml`
# calls `default`, which is `local` — so the SuperGrid targets below ran against a local
# SuperLink and nothing they did ever appeared in the federation's runs tab.
SUPERLINK  ?= supergrid
SCENARIO   ?=
# Which federation a run is submitted to, and whose runs tab a judge is shown.
# `@i53n1/workspace` is simulation-runtime, so the SuperLink stands the SuperNodes up
# itself; `@i53n1/personal` is deployment-runtime with none registered, so a run there
# waits for nodes that never arrive.
FEDERATION ?= @i53n1/workspace
FEDERATION_URL := https://flower.ai/federations/$(subst @,,$(FEDERATION))?tab=runs
# Follows HARNESS_MODEL below, because both SuperGrid targets ask the same SuperLink and it
# resolves ids the same way for either. Separate only so a grid run can be pinned to a
# different model without moving what `harness` asks for. A firm node on a SuperNode reaches
# that model through the in-cluster proxy SuperGrid injects as `FLWR_MODEL_API_ENDPOINT`,
# which supplies the key itself; measured to also answer `glm-5.2`, `minimax-m3` and
# `gpt-oss-120b`, and to reject `glm-5.2-fp8` the same way — see docs/event.md.
GRID_MODEL ?= $(HARNESS_MODEL)
# One CPU per ClientApp, so three firms get three actors. At the default 2 the container's
# budget fits only two ClientAppActors for three SuperNodes, and Ray multiplexes: two firms
# share a process and answer the round one after the other. The log gives it away — the same
# `(ClientAppActor pid=...)` in front of two different firms. Isolation is by `Context`
# either way, but round 2 has each firm waiting on a model, and serialising two of those
# eats a five-minute task budget that three in parallel fit inside.
GRID_CPUS  ?= 1
GRIDDIR    := .grid-stage
# Round 2 reads prose with a model. Empty means round 1 only, so the gap stays open —
# a run without a model is honest, not broken. Endpoints are in docs/event.md.
MODEL      ?= $(CONSORTIUM_MODEL)
ENDPOINT   ?= $(FLWR_MODEL_API_ENDPOINT)
# A different model, because a different SuperLink resolves it. `flwr run` asks whichever
# SuperLink serves the run, and that process reads its own `FLWR_MODEL_API_ENDPOINT` — so on
# supergrid.flower.ai the shared endpoints in docs/event.md are not in play and their ids come
# back `400 not a valid model ID`. This one SuperGrid serves.
HARNESS_MODEL ?= openai/gpt-5.5
OPEN       := $(if $(filter Darwin,$(shell uname -s)),open,xdg-open)
SCENARIO_ARG := $(if $(SCENARIO),--scenario $(SCENARIO),)
SCENARIO_SLUGS = $(shell $(RUN) python -c "from backend.scenarios import catalogue; print(' '.join(catalogue()))" 2>/dev/null)

.DEFAULT_GOAL := help
.PHONY: help setup doctor run rounds traces harness grid baselines data build ui stage watch demo slides slides-build slides-deps test lint fmt check clean reset reset-traces publish chat

# `demo` and `check` are ordered pipelines — -j would race them.
.NOTPARALLEL:

help: ## List the targets
	@grep -hE '^[a-z][a-z-]*:.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "  Overrides: PORT=$(PORT) SLIDE_PORT=$(SLIDE_PORT) ROUNDS=$(ROUNDS) SUPERNODES=$(SUPERNODES) SUPERLINK=$(SUPERLINK)"
	@echo "             SCENARIO=$(SCENARIO) MODEL=$(MODEL) HARNESS_MODEL=$(HARNESS_MODEL)"
	@echo "  SCENARIO picks a corpus; empty uses the manifest default. Slugs: $(SCENARIO_SLUGS)"
	@echo "  SUPERLINK names a connection from your Flower config; SuperGrid needs supergrid."
	@echo "  GRID_MODEL=$(GRID_MODEL) is the id SuperGrid serves; MODEL is for direct calls."
	@echo "  FEDERATION=$(FEDERATION) is where \`make grid\` puts the coordinator and the firm nodes."
	@echo "  MODEL enables round-2 re-examination; empty runs round 1 and leaves the gap open."

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
	@echo "model      $(if $(MODEL),$(MODEL),NONE - round 2 finds nothing, gap stays open)"
	@echo "supergrid  $(HARNESS_MODEL) - what 'make harness' asks SuperGrid for"
	@echo "endpoint   $(if $(ENDPOINT),$(ENDPOINT),unset)"
	@echo "key        $(if $(strip $(FLWR_MODEL_API_KEY)),set,unset - correct for Qwen, wrong for GLM/Kimi/MiniMax)"
	@echo "dotenv     $(if $(wildcard .env),.env found,no .env - copy .env.example and fill in the key)"
	@echo "cache      $$(ls .cache/model 2>/dev/null | wc -l | tr -d ' ') responses on disk"
	@echo "traces     $$(ls frontend/state/trace-*.jsonl 2>/dev/null | wc -l | tr -d ' ') of $(words $(SCENARIO_SLUGS)) scenarios ready for the selector"
	@echo "environment is good"

# ------------------------------------------------------------------- the stack

run: rounds ## Alias for `rounds`

rounds: ## Run the federated protocol — ROUNDS rounds across SUPERNODES firm nodes
	$(RUN) python -m backend.rounds --rounds $(ROUNDS) --supernodes $(SUPERNODES) \
		--model "$(MODEL)" $(SCENARIO_ARG)

# Silently traced every scenario with no model once, and got four non-compliant bids for the
# selector to show a judge. An empty MODEL is a legitimate mode, so this warns rather than
# refuses — but it warns where it cannot be missed.
traces: ## Run every scenario once, so the UI's scenario selector is fully populated
	@test -n "$(MODEL)" || { \
	   echo ""; \
	   echo "  !! MODEL is empty. Round 2 will find nothing and every scenario will trace"; \
	   echo "  !! as NON-COMPLIANT. Set CONSORTIUM_MODEL and FLWR_MODEL_API_ENDPOINT first,"; \
	   echo "  !! or pass MODEL=... — see 'make doctor'."; \
	   echo ""; }
	@for slug in $(SCENARIO_SLUGS); do \
	   echo "--- $$slug"; \
	   $(RUN) python -m backend.rounds --rounds $(ROUNDS) --supernodes $(SUPERNODES) \
	     --model "$(MODEL)" --scenario $$slug >/dev/null 2>&1 || exit 1; \
	 done
	@echo "all scenarios traced — the selector can switch between them offline"

# The agent-runner path: one AgentApp task drives all three firm nodes in process over
# `LocalGrid`, so it is the published app a judge can `flwr chat` at, not a fan-out.
# `--federation` is what puts the run in the tab a judge is shown — without it the run goes
# to the default connection and is invisible there. For firm nodes on SuperNodes, see `grid`.
harness: ## Run the published harness the way a judge does — on SuperGrid's agent runner
	@echo "-> $(FEDERATION) · $(ROUNDS) rounds · agent runner · model $(if $(HARNESS_MODEL),$(HARNESS_MODEL),NONE — round 1 only)"
	$(RUN) flwr run . $(SUPERLINK) --federation $(FEDERATION) --stream \
		--run-config "num-rounds=$(ROUNDS) model='$(HARNESS_MODEL)'"
	@echo ""
	@echo "-> $(FEDERATION_URL)"

# The SuperGrid target where the firm nodes are real SuperNodes, and the one this repo is
# actually about. `harness` runs the published agentapp, which is a single task doing all
# three firms' work in threads — `flwr ls --format json` reports `clientapp-seconds: 0.0`
# for it. This runs the ServerApp/ClientApp pair, so the coordinator and the firm nodes are
# separate processes and that number is nonzero. See grid-stage.sh for why it needs a staged
# second app directory, and docs/decisions.md for the 12:00 decision it revisits.
#
# No endpoint is passed: a SuperNode reaches a model through the in-cluster proxy SuperGrid
# injects as `FLWR_MODEL_API_ENDPOINT`, which holds the key itself. Posting to the
# organisers' own endpoints from here is refused with 403 — SuperGrid does not route it.
#
# `simulation-config` first because the federation's SuperNode count is server-side state,
# and a stale 2 would silently drop firm C — the class of failure this repo asserts against
# rather than discovers on stage.
grid: ## Run the federated protocol on SuperGrid — coordinator and firm nodes on SuperNodes
	@sh grid-stage.sh $(GRIDDIR) >/dev/null
	@echo "-> $(FEDERATION) · $(ROUNDS) rounds · $(SUPERNODES) firm nodes · model $(if $(GRID_MODEL),$(GRID_MODEL),NONE — round 1 only)"
	@trap 'rm -rf $(GRIDDIR)' EXIT INT TERM; \
	 printf 'num-rounds = %s\nmodel = "%s"\nscenario = "%s"\n' \
	   '$(ROUNDS)' '$(GRID_MODEL)' '$(SCENARIO)' > $(GRIDDIR)/run-config.toml; \
	 $(RUN) flwr federation simulation-config $(FEDERATION) $(SUPERLINK) \
	   --num-supernodes $(SUPERNODES) --client-resources-num-cpus $(GRID_CPUS) >/dev/null; \
	 $(RUN) flwr run $(GRIDDIR)/consortium-grid $(SUPERLINK) --federation $(FEDERATION) \
	   --stream --run-config $(GRIDDIR)/run-config.toml
	@echo ""
	@echo "-> $(FEDERATION_URL)"

# NOT BUILT. `backend/baselines.py` is a docstring, so this prints nothing at all. The three
# readings it would score are already derived in `data/ground_truth.json` — `round_one_coverage`
# (declared), `self_assessment` (a firm alone), `coverage` (the oracle). Kept as a target so
# the gap is visible in `make help` rather than discovered at 17:30.
baselines: ## NOT BUILT — backend/baselines.py is a stub; prints nothing
	$(RUN) python -m backend.baselines

data: ## Regenerate the corpora — Data owner only, the R4 bio wording is hand-tuned
	$(RUN) python data/generate.py

build: ## Build the .fab bundle and throw it away, to prove it still builds
	@$(RUN) flwr build >/dev/null 2>&1 && rm -f ./*.fab && echo "fab        builds clean" \
		|| { echo "fab        FAILED — run 'uv run flwr build' for the error"; exit 1; }

# Publishes a staged copy, not the repo: `flwr app publish` never reads `fab-exclude`, so
# the root would ship docs/, tests/ and the deck's lockfile. See publish-stage.sh. Build the
# stage first — Hub builds server-side, and that build is where a bad stage would surface.
publish: check ## Publish to Flower Hub — bumps nothing, so bump `version` first for a new one
	@sh publish-stage.sh $(PUBDIR) >/dev/null
	@$(RUN) flwr build --app $(PUBDIR)/consortium >/dev/null 2>&1 && rm -f ./*.fab \
		|| { echo "stage      FAILED — run 'uv run flwr build --app $(PUBDIR)/consortium'"; exit 1; }
	$(RUN) flwr app publish $(PUBDIR)/consortium
	@rm -rf $(PUBDIR)
	@echo "-> https://flower.ai/apps/i53n1/consortium/"

chat: ## Talk to the published harness on SuperGrid: @i53n1/consortium <solicitation>
	$(RUN) flwr chat

ui: ## Serve the coverage matrix, ledger, and SF330 on localhost:PORT
	@echo "-> http://localhost:$(PORT)/   (ctrl-c to stop)"
	@( sleep 1 && $(OPEN) "http://localhost:$(PORT)/" >/dev/null 2>&1 & )
	@$(RUN) python frontend/serve.py $(PORT)

# The demo. Put this pane on the left of the screen and the browser on the right, then drive
# every run from the page's Run button: `serve.py` spawns the protocol with stdout inherited,
# so the log lands here while the animation plays there. Neither half is a recording.
stage: reset ## Split screen: this pane is the log, the browser is the process
	@echo ""
	@echo "  Consortium — stage"
	@echo "  ------------------"
	@echo "  page      http://localhost:$(PORT)/"
	@echo "  model     $(if $(MODEL),$(MODEL),NONE — round 2 finds nothing and the gap stays open)"
	@echo "  key       $(if $(strip $(FLWR_MODEL_API_KEY)),set,unset)"
	@echo "  endpoint  $(if $(ENDPOINT),$(ENDPOINT),unset)"
	@echo ""
	@echo "  Press Run on the page. The protocol logs here. Ctrl-c to stop."
	@echo ""
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
	 $(RUN) python -m backend.rounds --rounds $(ROUNDS) --supernodes $(SUPERNODES) \
	   --quiet --model "$(MODEL)" $(SCENARIO_ARG); \
	 echo ""; \
	 echo "rounds complete — page still served on :$(PORT), ctrl-c to stop"; \
	 wait $$ui

# `stage` is what we actually demo — see docs/demo-script.md. This one is kept for a
# hands-off run: no Run button, no split screen, and `baselines` in the middle is a no-op.
demo: reset rounds ui ## Unattended run: clean state -> rounds -> UI. For the demo use `stage`.

# ------------------------------------------------------------------- the slides

# Node, not uv: the deck adds nothing to uv.lock and nobody re-runs `uv sync` for it. Slidev
# installs into docs/slides/node_modules (gitignored) rather than resolving through npx every
# time, because `npx @slidev/cli` cannot install the theme it then demands. Once installed it
# runs offline — so run `make slides` once before the freeze, not at 17:29.
slides: slides-deps ## Serve the deck on :SLIDE_PORT with hot reload — problem, architecture, roadmap
	cd $(SLIDES) && npx slidev slides.md --port $(SLIDE_PORT) --open

slides-build: slides-deps ## Build the deck to docs/slides/dist — opens with no node process
	cd $(SLIDES) && npx slidev build slides.md --base ./ --out dist
	@echo "-> $(SLIDES)/dist/index.html"

slides-deps:
	@command -v npm >/dev/null || { echo "npm not found — install Node 20+"; exit 1; }
	@test -d $(SLIDES)/node_modules || { echo "installing Slidev into $(SLIDES)…"; \
	   cd $(SLIDES) && npm install --silent; }

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
