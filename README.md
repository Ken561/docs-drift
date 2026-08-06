# docs-drift

**Flag pull requests that change code without updating the docs that describe it.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## The problem

Documentation does not go stale all at once. It goes stale one pull request at a time.

Somebody renames a config flag on a Tuesday. The README still describes the old one. Nobody notices, because nothing breaks and no test fails. Six weeks later a new teammate spends their first morning debugging a setup guide that stopped being true in March, and the person who wrote that guide has no idea it happened.

The usual fixes do not hold. "Remember to update the docs" in a contributing guide relies on memory. A quarterly docs audit finds the drift months after it started. A required docs checkbox on the pull request template gets ticked out of habit.

The gap is feedback timing. The person who changed the code is the only one who knows what the docs should now say, and they know it for about ten minutes. After that the context is gone.

## What this does

`docs-drift` is a GitHub Action that runs on every pull request. You tell it which docs describe which code. When a pull request touches the code side and leaves the docs side alone, it says so in a comment while the author is still in the pull request.

That is the whole idea. It does not read your prose or judge your writing. It notices that two things that should move together did not.

## How it works

1. You add a `.docsdrift.yml` file that pairs code paths with the docs describing them.
2. On each pull request, the action diffs the branch against its base to get the changed files.
3. For every rule, it checks whether the code side matched and the docs side did not.
4. It posts one comment naming the rule, the files that changed, and where an update was expected.

Example comment:

> ### Docs drift check
>
> This pull request changed code in 1 area without updating the docs that describe it.
>
> **Public API reference**
>
> The API reference is the first thing new integrators read. When an endpoint changes and the reference does not, they lose a day.
>
> Changed:
> - `src/api/orders.py`
> - `src/api/users.py`
>
> Expected a matching update in:
> - `docs/api/**`
> - `openapi.yaml`
>
> If the docs genuinely do not need a change, add the `docs-drift-ok` label to this pull request.

## Setup

**1. Add the config.** Create `.docsdrift.yml` at the root of your repository:

```yaml
rules:
  - name: Public API reference
    why: >
      The API reference is the first thing new integrators read. When an
      endpoint changes and the reference does not, they lose a day.
    code:
      - "src/api/**"
      - "src/routes/**"
    docs:
      - "docs/api/**"
      - "openapi.yaml"
```

The `why` field is optional and it is the field that matters most. It appears in the comment, so the author sees the reason rather than just the rule. A rule without a reason reads like a policy. A rule with one reads like a colleague.

**2. Add the workflow.** Create `.github/workflows/docs-drift.yml`:

```yaml
name: Docs Drift

on:
  pull_request:
    types: [opened, synchronize, reopened, labeled, unlabeled]

permissions:
  contents: read
  pull-requests: write

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: your-org/docs-drift@v1
        with:
          fail-on-drift: "false"
```

That is it. No install step, no dependencies.

## Inputs

| Input | Default | What it does |
| --- | --- | --- |
| `config` | `.docsdrift.yml` | Path to the config file. |
| `fail-on-drift` | `false` | Fail the check when drift is found. |
| `comment` | `true` | Post the report as a pull request comment. |
| `skip-label` | `docs-drift-ok` | Label that skips the check on a pull request. |

## Outputs

| Output | What it contains |
| --- | --- |
| `drift-found` | `true` when at least one rule drifted. |
| `report` | The markdown report, for use in later steps. |

## Adoption notes

This is a tool that people have to actually want, so a few things are deliberate:

**It ships as a comment, not a blocker.** `fail-on-drift` defaults to `false`. A check that blocks merges on day one gets disabled by the end of week one. Start as a nudge, watch how often it fires, and turn on enforcement only once the rules have earned trust.

**Every rule has an escape hatch.** The `docs-drift-ok` label exists because sometimes the docs genuinely do not need to change, and a tool that cannot be overruled becomes a tool people route around.

**Start with two or three rules.** Map the docs that hurt most when they are wrong, usually setup instructions and the public API reference. A config with thirty rules on day one produces noise, and noise is how good checks get muted.

**Watch the skip rate.** If a rule gets skipped more often than it gets acted on, the rule is wrong, not the people. Rewrite the mapping or delete it.

## Local use

Run the check by hand against any list of files:

```bash
git diff --name-only main HEAD | python3 scripts/check_drift.py
```

JSON output, for wiring into something else:

```bash
git diff --name-only main HEAD | python3 scripts/check_drift.py --format json
```

## Development

```bash
python3 scripts/test_check_drift.py
```

Pure standard library, so there is nothing to install. If PyYAML happens to be present it gets used; otherwise a small built-in parser handles the config.

## Contributing

Issues and pull requests welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).
