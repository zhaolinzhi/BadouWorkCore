#!/usr/bin/env python3
"""badou-coding sync: pull upstream superpowers skills, never touch custom skills.

Hard rule: never rm-rf or overwrite any directory outside UPSTREAM_SKILLS allowlist.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

# Plugin layout (relative to this file)
PLUGIN_DIR = Path(__file__).resolve().parent
SKILLS_DIR = PLUGIN_DIR / "skills"

# upstream superpowers skills that auto-sync from the plugin cache
UPSTREAM_SKILLS = frozenset({
    "brainstorming",
    "writing-plans",
    "test-driven-development",
    "verification-before-completion",
    "subagent-driven-development",
    "dispatching-parallel-agents",
    "executing-plans",
    "finishing-a-development-branch",
    "requesting-code-review",
    "receiving-code-review",
    "systematic-debugging",
    "using-git-worktrees",
    "writing-skills",
    "using-badou",
})

# Badou custom skills - sync script NEVER touches these
CUSTOM_SKILLS = frozenset({
    "backend-module-generator",
    "backend-flow-engine",
    "frontend-module-quickstart",
    "frontend-module-list",
    "frontend-module-edit",
    "frontend-module-child-edit",
    "frontend-module-tree-edit",
    "frontend-module-tree-list",
    "frontend-module-tree-table",
    "frontend-module-extend-field",
    "frontend-module-global-styles",
    "frontend-module-list-search-set-value",
    "frontend-module-page-debug",
    "frontend-module-this-reference",
})


def log(msg: str) -> None:
    print(f"[badou-coding-sync] {msg}", file=sys.stderr)


def find_upstream_cache() -> Path | None:
    """Locate upstream superpowers skill cache."""
    candidates = [
        Path.home() / ".claude/plugins/cache/claude-plugins-official/superpowers",
    ]
    for base in candidates:
        if base.exists():
            versions = sorted(
                [p for p in base.iterdir() if p.is_dir()],
                key=lambda p: p.name,
                reverse=True,
            )
            if versions:
                skills = versions[0] / "skills"
                if skills.exists():
                    return skills
    return None


def safety_check() -> int:
    """Pre-flight: log every directory NOT in UPSTREAM_SKILLS as preserved."""
    if not SKILLS_DIR.exists():
        log(f"skills dir does not exist: {SKILLS_DIR}")
        return 1
    for entry in SKILLS_DIR.iterdir():
        if entry.is_dir() and entry.name in UPSTREAM_SKILLS:
            continue  # OK to sync
        log(f"preserving {entry.name} (custom or unknown)")
    return 0


# Addendum markers (must stay in sync with .badou-local.md templates)
USER_CONTENT_MARKER = "<!-- BADOU-LOCAL-USER-CONTENT -->"
ANCHOR_MARKER_PREFIX = "<!-- BADOU-LOCAL-ANCHOR"


def extract_addendum(local_md: Path) -> str | None:
    """Extract user content from .badou-local.md / .badou-local.en.md.

    Returns the content BELOW the BADOU-LOCAL-USER-CONTENT marker
    (with leading/trailing newlines stripped). Returns None if the
    file is missing or its user section is empty.
    """
    if not local_md.exists():
        return None
    raw = local_md.read_text(encoding="utf-8")
    if USER_CONTENT_MARKER in raw:
        raw = raw.split(USER_CONTENT_MARKER, 1)[1]
    body = raw.strip("\n")
    return body or None


def inject_addendum(skill_md: Path, addendum: str) -> bool:
    """Append addendum as '## Badou Enterprise Addendum' section at end of SKILL.md.

    Upstream superpowers SKILL.md does NOT include a BADOU-LOCAL-ANCHOR
    marker, so we append to the file end (rather than inject mid-file).
    Idempotent: returns False if section header already exists.

    Returns True if injected, False if file missing / addendum empty /
    section already present.
    """
    if not skill_md.exists() or not addendum:
        return False
    raw = skill_md.read_text(encoding="utf-8")
    section_header = "## Badou Enterprise Addendum"
    if section_header in raw:
        return False  # already injected; don't double-append
    if raw and not raw.endswith("\n"):
        raw += "\n"
    raw += f"\n{section_header}\n\n{addendum}\n"
    skill_md.write_text(raw, encoding="utf-8")
    return True


def sync_skill(name: str, upstream: Path, dry_run: bool = False) -> bool:
    """Sync a single upstream skill. No-op for custom skills (defense in depth).

    Preserves .badou-local.md/.badou-local.en.md addendum by extracting
    its user content BEFORE rmtree and re-injecting it into the freshly
    regenerated SKILL.md.

    Returns True if addendum drift was detected (either injection or
    restoration of .badou-local.* files happened / would happen), False
    if no drift. Used by --check-addendum to aggregate exit codes.
    """
    if name not in UPSTREAM_SKILLS:
        log(f"skip {name} (not in UPSTREAM_SKILLS allowlist)")
        return False
    src = upstream / name
    if not src.exists():
        log(f"WARN: upstream missing {name}; skipping")
        return False
    dst = SKILLS_DIR / name

    # Preserve addendum: extract BEFORE rmtree so we can re-inject after copytree.
    # Snapshot ALL .badou-local.* files (not just the first one) so we can
    # restore every one after copytree; upstream doesn't carry any of them.
    # The first non-empty one is also used as the addendum source for SKILL.md.
    addendum: str | None = None
    saved_locals: list[tuple[str, str]] = []
    if dst.exists():
        for local_name in (".badou-local.md", ".badou-local.en.md"):
            local_md = dst / local_name
            if local_md.exists():
                content = local_md.read_text(encoding="utf-8")
                saved_locals.append((local_name, content))
                if addendum is None:
                    candidate = extract_addendum(local_md)
                    if candidate:
                        addendum = candidate
                        log(f"preserved addendum from {local_name}")

    # Drift definition: skill has an addendum source (.badou-local.*) but
    # SKILL.md is missing the injected "## Badou Enterprise Addendum" section.
    # This means a prior sync was incomplete (or upstream was bumped and the
    # regenerated SKILL.md lost the section). Restoration of .badou-local.*
    # files is NOT drift — it's the design behavior of sync.
    has_addendum_section = False
    skill_md_path = dst / "SKILL.md"
    if skill_md_path.exists():
        has_addendum_section = "## Badou Enterprise Addendum" in skill_md_path.read_text(encoding="utf-8")
    drift = bool(addendum) and not has_addendum_section

    if dry_run:
        log(f"[dry-run] would sync {src} -> {dst}")
        if drift:
            log(f"[dry-run] would inject addendum into {name}/SKILL.md (drift)")
        if saved_locals:
            log(f"[dry-run] would restore {len(saved_locals)} addendum files")
        return drift

    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)

    # Restore all .badou-local.* files (upstream doesn't carry any of them).
    if saved_locals:
        for local_name, content in saved_locals:
            (dst / local_name).write_text(content, encoding="utf-8")
        log(f"restored {len(saved_locals)} addendum files")

    # Re-inject addendum into freshly-copied SKILL.md.
    if addendum:
        if inject_addendum(dst / "SKILL.md", addendum):
            log(f"injected addendum into {name}/SKILL.md")
        else:
            log(f"WARN: addendum already present in {name}/SKILL.md; "
                f"not double-appending (run sync --force-addendum to override)")

    log(f"synced {name}")
    return drift


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="Log what would happen without modifying files")
    parser.add_argument("--list-skills", action="store_true",
                        help="List 14+14 = 28 skills by category and exit")
    parser.add_argument("--check-addendum", action="store_true",
                        help="Verify addendum is in sync: exit 0 if all 14 "
                             "upstream skills' .badou-local.* files and "
                             "SKILL.md addendum are preserved (no drift); "
                             "exit 1 if any drift detected. Implies --dry-run.")
    parser.add_argument("--version", default=None,
                        help="Upstream superpowers version (default: latest in cache)")
    args = parser.parse_args()

    if args.list_skills:
        print("UPSTREAM_SKILLS (sync'd from upstream superpowers):")
        for n in sorted(UPSTREAM_SKILLS):
            print(f"  - {n}")
        print("\nCUSTOM_SKILLS (preserved, never touched by sync):")
        for n in sorted(CUSTOM_SKILLS):
            print(f"  - {n}")
        return 0

    upstream = find_upstream_cache()
    if upstream is None:
        log("ERROR: upstream superpowers cache not found")
        return 1

    rc = safety_check()
    if rc != 0:
        return rc

    # --check-addendum implies --dry-run (read-only verification).
    effective_dry_run = args.dry_run or args.check_addendum

    drift_count = 0
    drift_skills: list[str] = []
    for name in sorted(UPSTREAM_SKILLS):
        if sync_skill(name, upstream, dry_run=effective_dry_run):
            drift_count += 1
            drift_skills.append(name)

    if args.check_addendum:
        if drift_count > 0:
            log(f"DRIFT DETECTED: {drift_count} skill(s) would have "
                f"addendum injected or .badou-local.* restored: "
                f"{', '.join(drift_skills)}")
            log(f"run 'python3 badou-coding-sync.py' (no flags) to fix")
            return 1
        log("CHECK PASS: all 14 upstream skills' addendum is in sync")
        return 0

    log("sync complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())