"""
Latency benchmark for POST /api/process (or /process).

Sends all 5 large HRMS files to the running backend and reports timing.
Run:  python mock_data/benchmark.py
"""

import time
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("pip install requests")
    sys.exit(1)

BASE_URL = "http://localhost:8000"
FILES_DIR = Path(__file__).parent / "large"

files = sorted(FILES_DIR.glob("HRMS_*.xlsx"))
if not files:
    print(f"No files found in {FILES_DIR}. Run generate_large.py first.")
    sys.exit(1)

print(f"Found {len(files)} HRMS files:")
for f in files:
    print(f"  {f.name}  ({f.stat().st_size/1024/1024:.1f} MB)")

# ── Check backend is alive ────────────────────────────────────────────────────
try:
    r = requests.get(f"{BASE_URL}/docs", timeout=5)
    print(f"\nBackend reachable at {BASE_URL}")
except Exception as e:
    print(f"\nBackend not reachable at {BASE_URL}: {e}")
    sys.exit(1)

# ── Build multipart payload ───────────────────────────────────────────────────
def make_payload():
    handles = []
    file_tuples = []
    for f in files:
        fh = open(f, "rb")
        handles.append(fh)
        file_tuples.append(("hrms_files", (f.name, fh,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")))
    data = {
        "payroll_start": "2025-09-01",
        "payroll_end":   "2026-01-31",
    }
    return file_tuples, data, handles

# ── Run benchmark ─────────────────────────────────────────────────────────────
RUNS = 3
timings = []

for i in range(1, RUNS + 1):
    file_tuples, data, handles = make_payload()
    print(f"\nRun {i}/{RUNS} — uploading {len(files)} files × 50k rows ...")
    t0 = time.perf_counter()
    try:
        resp = requests.post(f"{BASE_URL}/api/process", files=file_tuples, data=data, timeout=300)
        elapsed = time.perf_counter() - t0
        for fh in handles:
            fh.close()

        if resp.status_code == 200:
            payload = resp.json()
            snapshots = len(payload.get("snapshots", []))
            overview  = len(payload.get("overview_table", []))
            pair_keys = list(payload.get("pair_tables", {}).keys())
            timings.append(elapsed)
            print(f"  ✓  {elapsed:.2f}s  |  {snapshots} snapshots  |  {overview} overview rows  |  pairs: {pair_keys}")
        else:
            print(f"  ✗  HTTP {resp.status_code}: {resp.text[:300]}")
    except Exception as e:
        elapsed = time.perf_counter() - t0
        for fh in handles:
            fh.close()
        print(f"  ✗  Error after {elapsed:.2f}s: {e}")

# ── Summary ───────────────────────────────────────────────────────────────────
if timings:
    print(f"\n{'='*50}")
    print(f"Runs completed : {len(timings)}/{RUNS}")
    print(f"Min latency    : {min(timings):.2f}s")
    print(f"Max latency    : {max(timings):.2f}s")
    print(f"Avg latency    : {sum(timings)/len(timings):.2f}s")
    total_rows = len(files) * 50_000
    avg = sum(timings)/len(timings)
    print(f"Throughput     : {total_rows/avg:,.0f} rows/sec  ({total_rows:,} rows in {avg:.2f}s)")
