# Evals (step 9)

This is a method and a harness, not a published score. The project is a drill with fictional data, so the paid eval run was deliberately not done. This page says exactly what exists, what was run once, what was not run, and how to run the rest.

## How it works

`claude plugin eval` starts a fresh, non-interactive Claude session for each run, with only this plugin loaded, sends a prompt, and grades the result. The eval folder is hidden from the agent, so it never sees the expected answers: the run is blind. Each case runs several times, and a case's score is the share of graders that passed.

- **Single source of truth:** `evals/expected.yaml` (the expected market, risk tier, owner and escalate flag per ticket) and `tickets/*.md`.
- **Generator:** `python3 scripts/build_evals.py` writes everything under `evals/` except `expected.yaml`. `--check` fails if the committed files are out of date, and the free CI job runs it.
- **Cases:** `evals/triage-HR-1001/` to `triage-HR-1012/`. Each has a `prompt.md` ("Please triage support ticket HR-xxxx and prepare the case file.") and 8 graders:
  - four `regex` graders on the produced `cases/HR-xxxx.md` for market, risk tier, owner and escalate;
  - two `regex` graders that the case file contains no customer email and no customer name;
  - a `tool_used` grader that the ticket was read through the Zoho `searchTickets` tool;
  - a `tool_used` grader that the triage skill was invoked (reported as an indicator, not scored, in a two-arm run).
- **Mocks:** a runner has no Zoho connection, so `evals/mocks/zoho/ZohoDesk_searchTickets.md` answers every lookup from `evals/mocks/zoho/fixtures/HR-xxxx.json`, one fixture per ticket, in the shape Zoho returns. The fixtures use the fictional tickets only.

## What was run

One case, once: `triage-HR-1001`, one run, no baseline, capped at $2.

| Result | Value |
|---|---|
| Score | 1.00 (8 of 8 graders) |
| Cost | $0.13 (list-price estimate) |
| Time | 35 seconds |

Command used:

```
claude plugin eval . --case triage-HR-1001 --runs 1 --ablation none --allow-tools Write --trust-plugin --max-cost-usd 2 --no-publish
```

That one run shows the harness works end to end: the mock is picked up, the skill writes the case file in an empty workspace, and the graders read it. It says little about the other 11 tickets, and one run of a non-deterministic agent is a point estimate.

## What was not run

- The other 11 triage cases, and repeated runs of any case.
- The no-plugin baseline arm, which shows what the plugin adds.
- End-to-end draft cases (triage, drafter, reviewer). They are designed below but not built, because unrun graders would be unverified.

## Cost estimate for the rest

Only the first row is measured. The rest are extrapolations.

| What | Rough cost |
|---|---|
| 1 triage case, 1 run (measured) | $0.13 |
| 12 triage cases, 1 run each | about $1.60 |
| 12 triage cases, 3 runs each | about $4.70 |
| 12 triage cases, 3 runs, with baseline | roughly $7 to $9 |
| 5 draft cases, 1 run each | roughly $2.50 to $5 |
| Everything, 3 runs each, with baseline | roughly $25 to $40 |

Runs are billed to whatever credential Claude Code uses: plan usage limits for a subscription, API credits for an API key. `--max-cost-usd` stops new runs once the ceiling is reached.

## How to run it

All 12 triage cases once, capped:

```
claude plugin eval . --trust-plugin --ablation none --allow-tools Write --runs 1 --max-cost-usd 3 --threshold 0.8 --no-publish
```

The fuller run, pinned models, three runs, with the baseline arm and a JSON result:

```
claude plugin eval . --trust-plugin --allow-tools Write --runs 3 --threshold 0.8 \
  --model claude-sonnet-5-5 --judge-model claude-haiku-4-5-20251001 \
  --max-cost-usd 15 --no-publish --json results.json
```

Exit code 0 means every case met the threshold, 1 means a case fell below it or a file failed to load, and 2 means the cost ceiling stopped the run early. Results go to `evals/results/`, which git ignores.

## Draft cases (designed, not built)

For each of HR-1001 (safety), HR-1003 (chargeback, no customer reply), HR-1005 (press), HR-1007 (German, double charge) and HR-1012 (legal threat), one case would ask "Please draft a reply for ticket HR-xxxx". It needs:

- an `orders` mock, `evals/mocks/orders/get_order.md`, returning `mcp_servers/orders/orders.json` entries by `{{input.order_id}}`, because the plugin's real orders server is not started in a run without `--allow-real-servers`;
- `--allow-tools "Write"` so the command can save `drafts/HR-xxxx.md`;
- graders on the saved draft: `customer_reply` is `yes` or `no` as expected, the front matter says `review: pass`, the closing line and language match the market file, forbidden words do not appear (for example a refund confirmation for HR-1007, a cause or compensation for HR-1001), and a few `llm` graders for rules a regex cannot express.

## Risks the draft cases would test

- The agents and the triage skill read `policy/` and `cases/` by relative path. In a run, the working folder is empty, so those reads may fail. The same may apply to an installed plugin used in another folder. The triage case does not touch `policy/`, so this is unverified.
- The reviewer is a second model pass and not a guarantee.

## CI

- `.github/workflows/checks.yml` runs on every pull request and on pushes to `main`. It is free: the hook tests, the orders server tests, `build_evals.py --check` and `claude plugin validate .`.
- `.github/workflows/evals.yml` runs the paid suite. It can only be started by hand, uses an `ANTHROPIC_API_KEY` repository secret, and uploads `results.json`. A pull request cannot start it, and workflows from forks never receive secrets.
- Neither workflow has been run on GitHub yet, and the install of the Claude Code CLI in them is untested.
- Policy changes go through a pull request. Before merging one, start the eval workflow by hand and read the result.
