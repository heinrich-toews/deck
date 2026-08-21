#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Heinrich Toews
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Strip nextcloud/ocp dev-stub mappings from the generated composer autoloader.

The app mounts its dev vendor/ into a Nextcloud instance. Composer's
autoload-dev maps OCP\\ -> vendor/nextcloud/ocp/OCP, which hijacks the
server's own OCP namespace at runtime (breaks #[Override] checks and
replaces the real server interfaces with simplified stubs).

This removes only those mappings so OCP resolves to the Nextcloud server,
while keeping the rest of the (full dev) autoloader intact for PHPUnit etc.

Re-run after any `composer install` / `composer dump-autoload`.

Usage: python3 scripts/strip-ocp-autoload.py [vendor-dir]
"""
import re
import sys
from pathlib import Path

vendor = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("vendor")
cdir = vendor / "composer"
MARK = "nextcloud/ocp/OCP"


def clean_file(p: Path, line_rule=None, block_rules=None) -> int:
    """Line-based cleaning. line_rule(line)->True to drop; block_rules = list of
    regex strings matched against the joined text ([^\\n] only per line)."""
    txt = p.read_text()
    before = txt
    for rule in (block_rules or []):
        txt = re.sub(rule, "", txt)
    if line_rule is not None:
        lines = txt.splitlines(keepends=True)
        txt = "".join(l for l in lines if not line_rule(l))
    p.write_text(txt)
    return int(txt != before)


def clean_psr4(p):
    return clean_file(p, line_rule=lambda l: "OCP\\\\" in l and MARK in l)


def clean_classmap(p):
    return clean_file(p, line_rule=lambda l: "OCP\\\\" in l and MARK in l)


def clean_static(p):
    block_rules = [
        # prefixLengthsPsr4 entry: 'OCP\\' => 4,
        r"\n\s*'OCP\\\\' => \d+,",
        # prefixDirsPsr4 block: 'OCP\\' => array ( ... nextcloud/ocp/OCP ... ),
        r"\n\s*'OCP\\\\' =>\s*\n\s*array \(\s*\n\s*0 => __DIR__ \. '/\.\.' \. '/nextcloud/ocp/OCP',\s*\n\s*\),",
    ]

    def line_rule(l):
        return "OCP\\\\" in l and (MARK in l or l.strip().startswith("'OCP\\' =>"))

    return clean_file(p, line_rule=line_rule, block_rules=block_rules)


total = 0
for f in ("autoload_psr4.php", "autoload_classmap.php", "autoload_static.php"):
    p = cdir / f
    if not p.exists():
        continue
    if f.endswith("_psr4.php"):
        n = clean_psr4(p)
    elif f.endswith("_classmap.php"):
        n = clean_classmap(p)
    else:
        n = clean_static(p)
    total += n
    print(f"{f}: {'cleaned' if n else 'unchanged'}")
print(f"done ({total} files changed)")
