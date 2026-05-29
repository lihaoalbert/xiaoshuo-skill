#!/usr/bin/env python3
"""Continuity database manager for fiction projects.
Usage:
  python3 continuity.py init <project_dir>        # Create empty DB from project setup
  python3 continuity.py update <project_dir> <ep> # Add/update episode entry
  python3 continuity.py check <project_dir>        # Run consistency checks
  python3 continuity.py report <project_dir>       # Generate human-readable summary
  python3 continuity.py foreshadowing <project_dir> # List stalled/overdue foreshadowing
"""

import json, sys, os
from datetime import date
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent.parent / "agents" / "continuity-schema.json"

def load_db(project_dir):
    db_path = Path(project_dir) / "continuity.json"
    if db_path.exists():
        with open(db_path) as f:
            return json.load(f)
    return None

def save_db(project_dir, db):
    db_path = Path(project_dir) / "continuity.json"
    db["last_updated"] = str(date.today())
    with open(db_path, 'w') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

def init_db(project_dir):
    """Create a new empty continuity database."""
    name = os.path.basename(project_dir)
    db = {
        "project": name,
        "last_updated": str(date.today()),
        "timeline_base": {"start": "2026", "current_day": 0, "current_episode": 0},
        "characters": {},
        "foreshadowing": [],
        "episodes": [],
        "props": [],
        "relationships": []
    }
    save_db(project_dir, db)
    print(f"Created continuity.json for {name}")
    return db

def check_db(project_dir):
    """Run consistency checks and report issues."""
    db = load_db(project_dir)
    if not db:
        print("No continuity.json found. Run 'init' first.")
        return

    issues = []

    # Check stalled foreshadowing
    for f in db["foreshadowing"]:
        if f["status"] == "active":
            last_prog = max([p["ep"] for p in f.get("progressions", [{"ep": f["established_ep"]}])], default=f["established_ep"])
            episodes_since = db["timeline_base"]["current_episode"] - last_prog
            if episodes_since > 4:
                issues.append({
                    "type": "stalled_foreshadowing",
                    "severity": "medium",
                    "item": f["name"],
                    "detail": f"Established Ep {f['established_ep']}, last progressed Ep {last_prog}, {episodes_since} episodes without update"
                })

    # Check props not seen recently
    for p in db["props"]:
        if p["type"] == "injury":
            episodes_since = db["timeline_base"]["current_episode"] - p["last_seen_ep"]
            if episodes_since > 2 and p["status"] != "healed":
                issues.append({
                    "type": "forgotten_injury",
                    "severity": "low",
                    "item": p["name"],
                    "detail": f"Last seen Ep {p['last_seen_ep']}, {episodes_since} episodes without mention. Status: {p['status']}"
                })

    # Report
    if issues:
        print(f"Found {len(issues)} issues:")
        for i in issues:
            print(f"  [{i['severity'].upper()}] {i['type']}: {i['item']} — {i['detail']}")
    else:
        print("All consistency checks passed.")

    return issues

def report_db(project_dir):
    """Generate human-readable summary."""
    db = load_db(project_dir)
    if not db:
        print("No continuity.json found.")
        return

    print(f"=== {db['project']} — Continuity Report ===")
    print(f"Episodes: {len(db['episodes'])} | Current Day: {db['timeline_base']['current_day']}")
    print(f"Active Foreshadowing: {len([f for f in db['foreshadowing'] if f['status'] == 'active'])}")
    print(f"Props/Injuries tracked: {len(db['props'])}")
    print()

    for ep in db["episodes"]:
        review = ep.get("review", {})
        status = "✅" if all(v == "pass" for v in review.values()) else "⚠️"
        print(f"  Ep{ep['ep']:02d} {status} {ep['title']}")

def foreshadowing_report(project_dir):
    """List foreshadowing status."""
    db = load_db(project_dir)
    if not db:
        return

    for f in db["foreshadowing"]:
        bar = "█" * len(f.get("progressions", [])) + "░" * (5 - len(f.get("progressions", [])))
        print(f"  [{f['status']}] {f['name']}  [{bar}]  (Ep{f['established_ep']} → {f['planned_reveal_ep']})")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "init":
        init_db(sys.argv[2] if len(sys.argv) > 2 else ".")
    elif cmd == "check":
        check_db(sys.argv[2] if len(sys.argv) > 2 else ".")
    elif cmd == "report":
        report_db(sys.argv[2] if len(sys.argv) > 2 else ".")
    elif cmd == "foreshadowing":
        foreshadowing_report(sys.argv[2] if len(sys.argv) > 2 else ".")
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
