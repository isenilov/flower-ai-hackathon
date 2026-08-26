# Consortium — team working agreement

Hackathon repo, four people, one afternoon. The brief is `docs/consortium-brief.md`;
read it before touching code. This file overrides the user-level `~/.claude/CLAUDE.md`
wherever the two disagree — there is no Jira project, no PR review, and no `master`
branch here.

## 1. Always work in a worktree

**Every task starts by entering a worktree. Never edit files in the primary checkout.**

At the start of a task, call `EnterWorktree` with a short name for the task
(`EnterWorktree(name: "optimiser")`). That puts the session in
`.claude/worktrees/<name>/` on its own local branch, cut fresh from `origin/main`.
Do the work, commit, land it (§2), then `ExitWorktree`.

Why: four people and their agents run in parallel against one branch. Worktrees keep
each stream of edits on its own filesystem tree, so two sessions never write the same
file at the same time and nothing gets clobbered mid-edit. Conflicts then surface once,
at push time, where they are cheap.

- The primary checkout at the repo root is for reading, running the demo, and landing —
  not for editing.
- One worktree per task, not per person. Finish it, land it, remove it.
- `.claude/worktrees/` is gitignored; the worktree branch is scratch and never leaves
  your machine.

## 2. One branch: `main`

`main` is the only branch that exists on `origin`. No feature branches, no PRs, no
review gates.

Land from inside your worktree:

```bash
git add -A && git commit -m "feat(backend): greedy set-cover optimiser"
git fetch origin && git rebase origin/main
git push origin HEAD:main
```

- **Rebase, never merge.** A merge commit from a worktree branch drags the scratch
  branch name into shared history.
- **Push early and often.** Small increments that land are worth more than a perfect
  module that lands at 16:35. If it runs, push it.
- **Pull before you start and before you push.** `git fetch origin && git rebase origin/main`.
- If the rebase conflicts, fix it in your worktree. Never force-push `main`.

## 3. Stay in your lane

Directory ownership follows the task table in the brief (§11). Editing outside your lane
is what produces conflicts on a shared branch — if you need a change in someone else's
directory, say so in chat first.

| Directory | Owner | Contents |
|---|---|---|
| `data/` | Data | RFP, per-firm corpora, vocabulary, ground truth, generator |
| `backend/` | Flower + Fusion | Coordinator, firm node, transport, bander, optimiser, assembly, baselines |
| `agents/` | Agent | Matcher agent, local search, round-2 re-examination, prompts |
| `frontend/` | Viz | Coverage matrix, disclosure ledger, SF330 render |
| `docs/` | all | Brief, demo script, decisions |
| `tests/` | all | Invariants on the schema and the corpora. Whoever breaks one owns the fix. |

Two rules that matter more than the table:

- **Never reformat, rename, or move a file you do not own.** A drive-by import sort in
  someone else's module turns a two-line conflict into a whole-file one.
- **Contracts are frozen once agreed.** `backend/schema.py` (the `Attestation` and
  `Requirement` shapes) freezes at 11:20 per the brief's first milestone; `backend/transport.py`
  freezes when round 1 goes end to end. Changing either after that blocks three other
  people — announce it, don't just push it.

## 4. Environment

Everything goes through the Makefile — `make` lists the targets. The four you need:

```bash
make setup     # once, and after anyone touches uv.lock
make rounds    # the federated protocol, logs streaming
make check     # lint + invariant tests — run this before every push
make demo      # the full demo sequence — see docs/demo-script.md
```

`make check` is not optional. The invariant tests in `tests/` guard the two things that
break silently: `data/vocabulary.json` drifting from `backend/schema.py`, and a corpus edit
that destroys the engineered R4 gap. They fail here or they fail on stage.

`make fmt` exists but read §3 first — running it over the whole tree reformats files you
do not own and turns a two-line conflict into a whole-file one. Pass paths you own:
`uv run ruff format agents/`.

Python ≥ 3.13, `uv`, `flwr >= 1.34`. Dependencies are stdlib-first per the brief (§9.3):
`dataclasses` over pydantic, `re` for the bander, `numpy` for optimiser arithmetic. Adding
a dependency means everyone re-runs `uv sync` — check that it earns its place, and mention
it when you push `uv.lock`.

## 5. Commits

Conventional Commits without a ticket ID: `<type>(<scope>): <summary>`, scope being the
directory (`data`, `backend`, `agents`, `frontend`, `docs`). Imperative, lowercase.

```
feat(agents): gap-directed round-2 re-query
fix(backend): reject unknown banded keys instead of dropping them
data(data): tune firm B bio wording so round 1 misses the R4 match
```

Small and often. Nothing is squashed, nothing is rewritten — history is a hackathon log,
not a release artefact.

## 6. Hard deadlines

The brief's milestones are real and the cut list (§11) is in strict order. **16:50 is a
code freeze** — after it, nothing merges, and the only work is rehearsal. Demos are ready
at **17:30**, when judges come to the table. If you are mid-task at 16:40, push what runs
and stop.

Two things are never cut. **Round 2**, because without gap-directed re-examination this is
federated RAG with extra steps. And the **Hub publish** — a published app and a public repo
are the submission gates, not features, and the final publish is at **16:30**, before the
freeze. If the 16:20 choice is between a working demo beat and a published app, publish.
