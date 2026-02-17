import re
import random
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt

# keep max samples per day (adjust if needed)
MAX_SAMPLES = 200000

# Log format looks like:
# [pid: ...] <ip> ... [Tue Feb 10 14:47:06 2026] GET /... => generated ... in 2740 msecs
# Use a greedy prefix so we capture the *last* [...] date block before GET.
pattern = re.compile(
    r".*\[(?P<date>(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+[A-Za-z]{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\s+\d{4})\]\s+GET\s+(?P<path>/[^\s]*)\s+=> generated .* in (?P<time>\d+) msecs"
)

# reservoir per day
samples = defaultdict(list)
counts = defaultdict(int)

def reservoir_add(day, value):
    counts[day] += 1
    c = counts[day]

    if len(samples[day]) < MAX_SAMPLES:
        samples[day].append(value)
    else:
        # replace elements with decreasing probability
        j = random.randint(0, c - 1)
        if j < MAX_SAMPLES:
            samples[day][j] = value


def _default_log_file() -> Path | None:
    downloads = Path.home() / "Downloads"
    if not downloads.exists():
        return None
    # Prefer the exact historical naming scheme, but fall back to any similar file.
    matches = list(downloads.glob("orumsV3_spoken.log-*"))
    if not matches:
        matches = list(downloads.glob("*orumsV3_spoken*"))
    matches = sorted(matches, key=lambda p: p.stat().st_mtime, reverse=True)
    return matches[0] if matches else None


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute homepage response-time percentiles from a log file.")
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Path to the log file. If omitted, uses the newest ~/Downloads/orumsV3_spoken.log-* file.",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=MAX_SAMPLES,
        help="Max reservoir samples per day (default: %(default)s).",
    )
    parser.add_argument(
        "--days",
        type=str,
        default="10,11,12,13,14,15",
        help="Comma-separated day-of-month numbers to include for Feb (default: %(default)s).",
    )
    parser.add_argument(
        "--homepage-match",
        choices=["strict", "allow-query"],
        default="allow-query",
        help="Homepage matching: strict='/' only; allow-query='/' and '/?…' (default: %(default)s).",
    )
    parser.add_argument(
        "--plot",
        choices=["compare", "hist", "both", "none"],
        default="compare",
        help="Plot type (default: %(default)s).",
    )
    return parser.parse_args()


args = _parse_args()
MAX_SAMPLES = args.max_samples
days = {int(x.strip()) for x in args.days.split(",") if x.strip()}

def _is_homepage(path: str) -> bool:
    if args.homepage_match == "strict":
        return path == "/"
    # allow-query
    return path == "/" or path.startswith("/?")

log_file = Path(args.log_file).expanduser() if args.log_file else _default_log_file()
if not log_file or not log_file.exists():
    downloads = Path.home() / "Downloads"
    default_hint = downloads / "orumsV3_spoken.log-*"
    raise SystemExit(
        "Log file not found.\n"
        f"Tried auto-detecting the newest file matching `{default_hint}`.\n"
        "Pass it explicitly, e.g.:\n"
        "  python log.py --log-file ~/Downloads/orumsV3_spoken.log-20260215\n"
    )


with open(log_file, "r", errors="ignore") as f:
    for line in f:
        m = pattern.search(line)
        if not m:
            continue

        path = m.group("path").strip()

        # homepage only
        if not _is_homepage(path):
            continue

        raw_date = m.group("date")
        response_time = int(m.group("time"))

        dt = datetime.strptime(raw_date, "%a %b %d %H:%M:%S %Y")

        # only Feb 10–15
        if dt.month == 2 and dt.day in days:
            day_key = dt.strftime("%Y-%m-%d")
            reservoir_add(day_key, response_time)


# compute percentiles & print a comparison table
print("\n📊 Homepage response-time percentiles (Feb comparison)\n")
print(f"Log file: {log_file}")
print(f"Homepage match: {args.homepage_match}")
print("")

ordered_days = [f"2026-02-{d:02d}" for d in sorted(days)]

rows = []
results = {}  # day -> np.ndarray (for optional plotting)

for day in ordered_days:
    arr_list = samples.get(day, [])
    if not arr_list:
        rows.append((day, 0, counts.get(day, 0), None, None, None))
        continue

    arr = np.array(arr_list)
    results[day] = arr

    p50 = float(np.percentile(arr, 50))
    p80 = float(np.percentile(arr, 80))
    p90 = float(np.percentile(arr, 90))
    rows.append((day, len(arr), counts.get(day, len(arr)), p50, p80, p90))

header = ("Date", "samples_used", "total_seen", "p50_ms", "p80_ms", "p90_ms")
print(f"{header[0]:<12} {header[1]:>12} {header[2]:>10} {header[3]:>10} {header[4]:>10} {header[5]:>10}")
print("-" * 70)
for (day, n, total, p50, p80, p90) in rows:
    if p50 is None:
        print(f"{day:<12} {n:>12} {total:>10} {'-':>10} {'-':>10} {'-':>10}")
    else:
        print(f"{day:<12} {n:>12} {total:>10} {p50:>10.1f} {p80:>10.1f} {p90:>10.1f}")


def _plot_histograms() -> None:
    for day, arr in results.items():
        plt.figure()
        plt.hist(arr, bins=40)
        plt.title(f"Homepage Response Time Distribution ({day})")
        plt.xlabel("Response Time (ms)")
        plt.ylabel("Requests")
        plt.grid(True)


def _plot_comparison() -> None:
    xs = []
    p50s = []
    p80s = []
    p90s = []
    for (day, n, _total, p50, p80, p90) in rows:
        if n == 0:
            continue
        xs.append(day)
        p50s.append(p50)
        p80s.append(p80)
        p90s.append(p90)

    if not xs:
        return

    plt.figure()
    plt.plot(xs, p50s, marker="o", label="P50")
    plt.plot(xs, p80s, marker="o", label="P80")
    plt.plot(xs, p90s, marker="o", label="P90")
    plt.title("Homepage Response Time Percentiles (Feb 10–15)")
    plt.xlabel("Date")
    plt.ylabel("Response time (ms)")
    plt.grid(True)
    plt.legend()
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()


if args.plot in ("hist", "both"):
    _plot_histograms()
if args.plot in ("compare", "both"):
    _plot_comparison()
if args.plot != "none":
    plt.show()
