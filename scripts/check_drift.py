#!/usr/bin/env python3
"""
docs-drift: flag pull requests that change code without touching the docs
that describe it.

Reads a .docsdrift.yml config that maps code paths to the docs that are
supposed to describe them. Given a list of files changed in a pull request,
it reports any rule where the code side moved but the docs side did not.

No third-party dependencies. If PyYAML is installed it is used; otherwise a
small parser handles the subset of YAML this config needs.
"""

import argparse
import fnmatch
import json
import os
import sys

DEFAULT_CONFIG = ".docsdrift.yml"


# ---------------------------------------------------------------- config


def _parse_simple_yaml(text):
    """Parse the narrow YAML subset used by .docsdrift.yml.

    Supports top-level scalars, top-level lists of mappings, and
    string-list values. Deliberately small: the config is meant to stay
    readable, so the parser can stay readable too.
    """
    root = {}
    current_list = None
    current_item = None
    current_key = None

    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue

        indent = len(line) - len(line.lstrip())
        stripped = line.strip()

        # New item in a top-level list: "  - name: something"
        if stripped.startswith("- ") and indent > 0 and current_list is not None:
            current_item = {}
            current_list.append(current_item)
            current_key = None
            stripped = stripped[2:].strip()
            if not stripped:
                continue

        # A bare list entry belonging to the key we are inside of
        if stripped.startswith("- ") and current_key is not None:
            value = stripped[2:].strip().strip("'\"")
            target = current_item if current_item is not None else root
            target.setdefault(current_key, []).append(value)
            continue

        if ":" not in stripped:
            continue

        key, _, value = stripped.partition(":")
        key = key.strip()
        value = value.strip().strip("'\"")

        if indent == 0:
            current_item = None
            current_key = key
            if value == "":
                root[key] = []
                current_list = root[key]
            else:
                root[key] = _coerce(value)
                current_list = None
            continue

        target = current_item if current_item is not None else root
        current_key = key
        if value == "":
            target[key] = []
        else:
            target[key] = _coerce(value)

    return root


def _coerce(value):
    lowered = value.lower()
    if lowered in ("true", "yes"):
        return True
    if lowered in ("false", "no"):
        return False
    if value.isdigit():
        return int(value)
    return value


def load_config(path):
    if not os.path.exists(path):
        raise SystemExit(
            "docs-drift: no config found at %s.\n"
            "Copy the example from the docs-drift repo to get started." % path
        )

    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read()

    try:
        import yaml  # noqa: WPS433 - optional dependency by design

        return yaml.safe_load(text) or {}
    except ImportError:
        return _parse_simple_yaml(text)


# ---------------------------------------------------------------- matching


def matches_any(path, patterns):
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def as_list(value):
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return list(value)


def find_drift(changed_files, config):
    """Return a list of rules whose code changed but whose docs did not."""
    findings = []

    for index, rule in enumerate(config.get("rules", [])):
        name = rule.get("name") or "rule %d" % (index + 1)
        code_patterns = as_list(rule.get("code"))
        docs_patterns = as_list(rule.get("docs"))

        if not code_patterns or not docs_patterns:
            continue

        touched_code = [f for f in changed_files if matches_any(f, code_patterns)]
        touched_docs = [f for f in changed_files if matches_any(f, docs_patterns)]

        if touched_code and not touched_docs:
            findings.append(
                {
                    "name": name,
                    "why": rule.get("why", ""),
                    "changed_code": sorted(touched_code),
                    "expected_docs": docs_patterns,
                }
            )

    return findings


# ---------------------------------------------------------------- output


def render_comment(findings):
    lines = ["### Docs drift check", ""]

    if not findings:
        lines.append("No drift found. Code and docs moved together.")
        return "\n".join(lines)

    noun = "area" if len(findings) == 1 else "areas"
    lines.append(
        "This pull request changed code in %d %s without updating the docs "
        "that describe it." % (len(findings), noun)
    )
    lines.append("")

    for finding in findings:
        lines.append("**%s**" % finding["name"])
        if finding["why"]:
            lines.append("")
            lines.append(finding["why"])
        lines.append("")
        lines.append("Changed:")
        for path in finding["changed_code"][:10]:
            lines.append("- `%s`" % path)
        if len(finding["changed_code"]) > 10:
            lines.append("- and %d more" % (len(finding["changed_code"]) - 10))
        lines.append("")
        lines.append("Expected a matching update in:")
        for pattern in finding["expected_docs"]:
            lines.append("- `%s`" % pattern)
        lines.append("")

    lines.append(
        "If the docs genuinely do not need a change, add the "
        "`docs-drift-ok` label to this pull request."
    )
    return "\n".join(lines)


def read_changed_files(args):
    if args.changed_files:
        raw = args.changed_files
    elif args.changed_files_file:
        with open(args.changed_files_file, "r", encoding="utf-8") as handle:
            raw = handle.read()
    else:
        raw = sys.stdin.read()

    return [line.strip() for line in raw.replace(",", "\n").splitlines() if line.strip()]


def main():
    parser = argparse.ArgumentParser(description="Detect docs drift in a pull request.")
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--changed-files", help="Newline or comma separated paths.")
    parser.add_argument("--changed-files-file", help="File containing changed paths.")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument(
        "--fail-on-drift",
        action="store_true",
        help="Exit 1 when drift is found. Off by default so teams can adopt "
        "this as a nudge before making it a gate.",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    changed_files = read_changed_files(args)
    findings = find_drift(changed_files, config)

    if args.format == "json":
        print(json.dumps({"drift": findings}, indent=2))
    else:
        print(render_comment(findings))

    if findings and args.fail_on_drift:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
