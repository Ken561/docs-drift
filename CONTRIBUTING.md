# Contributing

Thanks for taking a look.

## Getting started

Nothing to install. The check is pure standard-library Python 3.

```bash
git clone <your fork>
cd docs-drift
python3 scripts/test_check_drift.py
```

## What is most useful

- **Rule patterns for a stack we do not cover.** If you wrote a `.docsdrift.yml`
  that works well for your language or framework, open a pull request adding it
  to `examples/`. Real configs from real repos are worth more than invented ones.
- **Adoption reports.** If you rolled this out to a team, an issue describing
  what fired, what got skipped, and what you changed as a result is genuinely
  valuable. The hard part of this tool is tuning, not code.
- **Bug reports with a file list.** Include the changed paths and the config,
  since that is enough to reproduce anything.

## Design constraints

Two rules keep this small enough to trust:

1. **No required dependencies.** If it cannot be done with the standard library,
   it probably does not belong here.
2. **The tool nudges, it does not judge.** It reports that two things did not
   move together. It does not evaluate whether documentation is good.

## Pull requests

Run the tests, keep the diff focused, and update the README if you changed
behavior. The irony of letting this repo's own docs drift is not lost on anyone.
