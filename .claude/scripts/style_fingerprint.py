#!/usr/bin/env python3
"""Style fingerprint extractor for fiction quality assurance.

Usage:
  python3 style_fingerprint.py baseline <episode_file>     # Extract baseline fingerprint
  python3 style_fingerprint.py compare <baseline> <ep_file> # Compare against baseline
  python3 style_fingerprint.py batch <project_episodes_dir> # Analyze all episodes

The fingerprint captures 12 dimensions of writing style — not quality, but consistency.
Deviations > 1.5σ from baseline are flagged for review.
"""

import json, sys, re, os
from pathlib import Path
from collections import Counter

def extract_fingerprint(text):
    """Extract style metrics from episode text."""
    # Strip markdown headers and scene markers
    clean = re.sub(r'#.*?\n', '', text)
    clean = re.sub(r'\[场景：[^\]]+\]', '', clean)
    clean = re.sub(r'\[([^\]]+)\]', '', clean)  # stage directions

    # Split into lines
    lines = [l.strip() for l in clean.split('\n') if l.strip() and not l.startswith('---') and l != '（第' and '完）' not in l]

    # Dialogue lines (角色名：content)
    dialogue_lines = [l for l in lines if re.match(r'^[^\s(]+[：:].+', l)]
    # Inner monologue
    os_lines = [l for l in dialogue_lines if '(内心 OS)' in l or '(内心OS)' in l]
    # Spoken dialogue
    spoken_lines = [l for l in dialogue_lines if '(内心' not in l]

    # Stage direction blocks
    action_blocks = re.findall(r'\[([^\]]+)\]', text)

    # Character line counts
    characters = Counter()
    for l in spoken_lines:
        m = re.match(r'^([^：:(]+)[：:]', l)
        if m:
            name = m.group(1).strip()
            if not any(kw in name for kw in ['App', 'AI', '小孩声', '女声', '男人声', '邻居']):
                characters[name] += 1

    # Metrics
    total_chars = len(clean.replace('\n', ''))
    dialogue_chars = sum(len(l) for l in spoken_lines)
    action_chars = sum(len(a) for a in action_blocks)
    os_chars = sum(len(l) for l in os_lines)

    # Count jokes (lines with clear comedy beats)
    joke_indicators = ['(内心 OS)', '——', '...', '突然', '愣了一下', '笑', '差评', 'BATNA', '威胁等级']
    joke_count = sum(1 for l in spoken_lines + os_lines if any(ind in l for ind in joke_indicators))

    return {
        "total_chars": total_chars,
        "dialogue_ratio": round(dialogue_chars / max(total_chars, 1), 3),
        "action_ratio": round(action_chars / max(total_chars, 1), 3),
        "os_ratio": round(os_chars / max(dialogue_chars, 1), 3),
        "spoken_line_count": len(spoken_lines),
        "os_line_count": len(os_lines),
        "avg_spoken_line_chars": round(sum(len(l) for l in spoken_lines) / max(len(spoken_lines), 1), 1),
        "avg_os_line_chars": round(sum(len(l) for l in os_lines) / max(len(os_lines), 1), 1),
        "joke_density": round(joke_count / max(total_chars / 100, 1), 1),
        "character_count": len(characters),
        "top_characters": dict(characters.most_common(4)),
        "scene_count": len(re.findall(r'\[场景：', text)) or text.count('---') // 2 + 1,
    }

def compare_fingerprints(baseline, current, ep_num):
    """Compare current episode against baseline. Flag deviations > 1.5 threshold."""
    deviations = []
    thresholds = {
        "total_chars": 0.5,       # 50% change = big
        "dialogue_ratio": 0.15,
        "os_ratio": 0.20,
        "joke_density": 1.5,      # jokes per 100 chars
        "spoken_line_count": 0.40,
    }

    for key, threshold in thresholds.items():
        if key not in baseline or key not in current:
            continue
        base_val = baseline[key]
        curr_val = current[key]
        if base_val == 0:
            continue
        deviation = abs(curr_val - base_val) / base_val
        if deviation > threshold:
            direction = "↑" if curr_val > base_val else "↓"
            deviations.append({
                "metric": key,
                "baseline": base_val,
                "current": curr_val,
                "deviation_pct": round(deviation * 100, 1),
                "direction": direction,
                "severity": "high" if deviation > threshold * 1.5 else "medium"
            })

    return {
        "episode": ep_num,
        "deviations": deviations,
        "verdict": "consistent" if len([d for d in deviations if d["severity"] == "high"]) == 0 else "needs_review"
    }

def batch_analyze(episodes_dir):
    """Analyze all episodes in directory, using Ep1 as baseline."""
    files = sorted(Path(episodes_dir).glob("*.md"))
    if not files:
        print("No episode files found.")
        return

    baseline = None
    results = []

    for f in files:
        ep_match = re.search(r'(\d+)', f.stem)
        ep_num = int(ep_match.group(1)) if ep_match else 0

        with open(f) as fh:
            text = fh.read()

        fp = extract_fingerprint(text)

        if ep_num == 1:
            baseline = fp
            print(f"=== BASELINE (Ep 1: {f.name}) ===")
            print(json.dumps(fp, indent=2, ensure_ascii=False))
            print()
        elif baseline:
            result = compare_fingerprints(baseline, fp, ep_num)
            results.append(result)

            status = "✅" if result["verdict"] == "consistent" else "⚠️"
            print(f"{status} Ep{ep_num:02d} {f.name}: ", end="")
            if result["deviations"]:
                print(f"{len(result['deviations'])} deviations")
                for d in result["deviations"]:
                    print(f"    {d['direction']} {d['metric']}: {d['baseline']}→{d['current']} ({d['deviation_pct']}%) [{d['severity']}]")
            else:
                print("no significant deviations")

    # Summary
    warnings = [r for r in results if r["verdict"] == "needs_review"]
    print(f"\n=== SUMMARY ===")
    print(f"Total episodes: {len(files)}")
    print(f"Consistent: {len(results) - len(warnings)}")
    print(f"Needs review: {len(warnings)}")
    if warnings:
        print(f"Review episodes: {[r['episode'] for r in warnings]}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "baseline":
        with open(sys.argv[2]) as f:
            fp = extract_fingerprint(f.read())
        print(json.dumps(fp, indent=2, ensure_ascii=False))
    elif cmd == "compare":
        with open(sys.argv[2]) as f:
            baseline = json.load(f)
        with open(sys.argv[3]) as f:
            current = extract_fingerprint(f.read())
        ep = int(re.search(r'(\d+)', sys.argv[3]).group(1)) if re.search(r'(\d+)', sys.argv[3]) else 0
        result = compare_fingerprints(baseline, current, ep)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif cmd == "batch":
        batch_analyze(sys.argv[2] if len(sys.argv) > 2 else ".")
    else:
        print(f"Unknown command: {cmd}")
