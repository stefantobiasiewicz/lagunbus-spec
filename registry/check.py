#!/usr/bin/env python3
"""Checks whether the tables in the markdown agree with the registry.

Run it from the specification's top directory:

    python3 registry/check.py

Without external dependencies — it reads only those YAML fields it needs, so that the
specification repository does not require installing anything.
Exit code 1 means a drift.
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
errors = []


def read(path):
    with io.open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return f.read()


def entries(yaml_text, first_key):
    """Pulls a list of dicts out of simple YAML: entries begin with '- <key>:'."""
    out, current = [], None
    for line in yaml_text.splitlines():
        m = re.match(r"^\s*-\s+(\w+):\s*(.*)$", line)
        if m and m.group(1) == first_key:
            current = {m.group(1): m.group(2).strip()}
            out.append(current)
            continue
        if m:
            current = {m.group(1): m.group(2).strip()}
            out.append(current)
            continue
        m = re.match(r"^\s+(\w+):\s*(.*)$", line)
        if m and current is not None:
            current[m.group(1)] = m.group(2).strip()
    return out


def error(what):
    errors.append(what)


# --- 1. Endpoint types --------------------------------------------------------
types = [p for p in entries(read("registry/endpoint-types.yaml"), "id") if "name" in p and "id" in p]

seen = {}
for t in types:
    if t["id"] in seen:
        error("duplicate type ID %s: %s and %s" % (t["id"], seen[t["id"]], t["name"]))
    seen[t["id"]] = t["name"]

registered_files = set()
for t in types:
    if t.get("status") != "described":
        continue
    file_ = t.get("file")
    if not file_:
        error("type %s (%s) has status 'described' but points at no file" % (t["id"], t["name"]))
        continue
    registered_files.add(os.path.basename(file_))
    if not os.path.exists(os.path.join(ROOT, file_)):
        error("type %s (%s): no file %s" % (t["id"], t["name"], file_))
        continue
    heading = read(file_).splitlines()[0]
    expected = "# Typ endpointu `%s` · %s" % (t["id"], t["name"])
    if heading.strip() != expected:
        error("%s: heading %r, the registry says %r" % (file_, heading.strip(), expected))

for name in sorted(os.listdir(os.path.join(ROOT, "types"))):
    if not name.endswith(".md") or name == "SZABLON.md":
        continue
    if name not in registered_files:
        error("types/%s exists but is not in the registry of types" % name)


# --- 2. Result codes ----------------------------------------------------------
codes = [p for p in entries(read("registry/result-codes.yaml"), "id") if "name" in p]
text_04 = read("04-interakcje.md")
in_markdown = dict(re.findall(r"^\|\s*`(0x[0-9A-F]{2})`\s*\|\s*`(\w+)`\s*\|", text_04, re.M))

for c in codes:
    if c["id"] not in in_markdown:
        error("code %s %s is in the registry, not in 04-interakcje.md §8" % (c["id"], c["name"]))
    elif in_markdown[c["id"]] != c["name"]:
        error("code %s: the registry says %s, 04-interakcje.md says %s"
              % (c["id"], c["name"], in_markdown[c["id"]]))

from_registry = {c["id"] for c in codes}
for ident, name in in_markdown.items():
    if ident not in from_registry:
        error("code %s %s is in 04-interakcje.md, not in the registry" % (ident, name))


# --- 3. Frame kinds -----------------------------------------------------------
kinds = [p for p in entries(read("registry/frame-kinds.yaml"), "id") if "name" in p and "id" in p]
text_05 = read("05-mapowanie-can.md")
for k in kinds:
    pattern = r"\|\s*`%s`\s*\|\s*`%s`\s*\|" % (re.escape(k["id"]), re.escape(k["name"]))
    if not re.search(pattern, text_05):
        error("kind %s %s is in the registry, not in the table of 05-mapowanie-can.md §2"
              % (k["id"], k["name"]))


# The check above states only that a kind appears SOMEWHERE in the chapter with the right
# number — and that let through a drift which survived the renumbering of the ladder at
# W15: the table in §2 was correct while §6.1 and §6.2 gave numbers from before the change.
# So we check EVERY table row in which a kind's name stands next to a nibble — in any
# column order.
by_name = dict((k["name"], k["id"]) for k in kinds)
for line in text_05.splitlines():
    if not line.lstrip().startswith("|"):
        continue
    nibble = re.findall(r"`(0x[0-9A-F])`", line)
    if not nibble:
        continue
    for name, ident in by_name.items():
        if ("`%s`" % name) in line and ident not in nibble:
            error("05-mapowanie-can.md: the row with `%s` gives %s, the registry says %s — %s"
                  % (name, "/".join(nibble), ident, line.strip()[:60]))

# --- 4. Node classes ----------------------------------------------------------
classes = [p for p in entries(read("registry/node-classes.yaml"), "id") if "name" in p and "id" in p]
for c in classes:
    pattern = r"\|\s*`%s`\s*\|\s*`%s`\s*\|" % (re.escape(c["id"]), re.escape(c["name"]))
    if not re.search(pattern, text_05):
        error("node class %s %s is in the registry, not in the table of "
              "05-mapowanie-can.md §4.1" % (c["id"], c["name"]))

# NodeClass is not an attribute — we watch that nobody adds it there.
if re.search(r"`NodeClass`\s*\|", read("types/0x0001-device.md")):
    error("types/0x0001-device.md: NodeClass showed up in the attribute table; "
          "it is to live in the ANNOUNCEMENT frame alone")


# --- 5. Common attributes ----------------------------------------------------
common = [p for p in entries(read("registry/common-attributes.yaml"), "id") if "name" in p]
text_01 = read("01-model-danych.md")
in_01 = dict(re.findall(r"^\|\s*`(0x[0-9A-F]{2})`\s*\|\s*`(\w+)`\s*\|", text_01, re.M))

for a in common:
    if a["id"] not in in_01:
        error("common attribute %s %s is in the registry, not in 01-model-danych.md §4"
              % (a["id"], a["name"]))
    elif in_01[a["id"]] != a["name"]:
        error("common attribute %s: the registry says %s, 01-model-danych.md says %s"
              % (a["id"], a["name"], in_01[a["id"]]))

common_from_registry = {a["id"] for a in common}
for ident, name in in_01.items():
    if ident not in common_from_registry:
        error("common attribute %s %s is in 01-model-danych.md, not in the registry"
              % (ident, name))


# --- 6. System endpoints in the diagrams ----------------------------------------
# The ASCII diagrams are the one place none of the other checks sees: code blocks are cut
# out before the links are checked. The assignment of a type to a fixed endpoint has
# already drifted once between a diagram and the table beside it.
fixed_ep = {}
for t in types:
    if "fixed_endpoint" in t and "name" in t:
        fixed_ep[t["fixed_endpoint"]] = t["name"]
known_types = {t["name"] for t in types if "name" in t}

for directory, _, files in os.walk(ROOT):
    if ".git" in directory:
        continue
    for name in sorted(files):
        if not name.endswith(".md"):
            continue
        rel = os.path.relpath(os.path.join(directory, name), ROOT)
        for m in re.finditer(r"\bep([0-3])\b[ \t]+([A-Z]\w+)", read(rel)):
            ep, named = m.group(1), m.group(2)
            if named not in known_types:
                continue
            expected = fixed_ep.get(ep)
            if expected and named != expected:
                error("%s: ep%s described as %s, the registry says %s"
                      % (rel, ep, named, expected))


# --- 7. References to sections --------------------------------------------------
# Section numbers shift with every rebuild of a chapter, and a reference to a section that
# does not exist does not catch the eye while reading.
sections = {}
for directory, _, files in os.walk(ROOT):
    if ".git" in directory:
        continue
    for name in files:
        if not name.endswith(".md"):
            continue
        rel = os.path.relpath(os.path.join(directory, name), ROOT)
        numbers = set()
        for m in re.finditer(r"^#{2,4}\s+(\d+(?:\.\d+)?)\.?\s", read(rel), re.M):
            numbers.add(m.group(1))
        sections[rel] = numbers

for directory, _, files in os.walk(ROOT):
    if ".git" in directory:
        continue
    for name in sorted(files):
        if not name.endswith(".md"):
            continue
        rel = os.path.relpath(os.path.join(directory, name), ROOT)
        content = re.sub(r"```.*?```", " ", read(rel), flags=re.S)

        for m in re.finditer(r"\]\(([^)]+\.md)\)[^§\n]{0,40}§\s*(\d+(?:\.\d+)?)", content):
            target = os.path.relpath(os.path.join(directory, m.group(1)), ROOT)
            if target in sections and m.group(2) not in sections[target]:
                error("%s: a reference to %s §%s — there is no such section"
                      % (rel, target, m.group(2)))

        for m in re.finditer(r"(?<!\])\(§\s*(\d+(?:\.\d+)?)\)", content):
            if m.group(1) not in sections[rel]:
                error("%s: a reference to its own §%s — there is no such section"
                      % (rel, m.group(1)))


# --- 8. Dead links ------------------------------------------------------------
for directory, _, files in os.walk(ROOT):
    if ".git" in directory:
        continue
    for name in files:
        if not name.endswith(".md") or name == "SZABLON.md":
            continue  # the template holds example links, deliberately non-existent
        path = os.path.join(directory, name)
        with io.open(path, encoding="utf-8") as f:
            content = f.read()
        for target in re.findall(r"\]\(([^)]+\.md)(?:#[^)]*)?\)", content):
            if target.startswith("http"):
                continue
            if not os.path.exists(os.path.join(directory, target)):
                rel_path = os.path.relpath(path, ROOT)
                error("%s: a dead link to %s" % (rel_path, target))


# --- the result ---------------------------------------------------------------
if errors:
    print("DRIFT — %d %s:\n" % (len(errors), "problem" if len(errors) == 1 else "problems"))
    for e in errors:
        print("  ·", e)
    sys.exit(1)

print("The registry agrees with the specification.")
print("  endpoint types:      %d (%d described)"
      % (len(types), sum(1 for t in types if t.get("status") == "described")))
print("  result codes:        %d" % len(codes))
print("  frame kinds:         %d" % len(kinds))
print("  node classes:        %d" % len(classes))
print("  common attributes:   %d" % len(common))
print("  files with sections: %d" % len(sections))
