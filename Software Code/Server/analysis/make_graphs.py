"""
Eyeora / SentinelVision - Graph Generator (Auto)

This script:
✅ Finds latest CSV inside core/data/reports (any name)
✅ If no CSV exists, uses latest analytics_*_summary.txt
✅ Generates easy project graphs
✅ Saves graphs into core/data/reports/graphs
"""

from pathlib import Path
import re

import pandas as pd
import matplotlib.pyplot as plt


# ---------------------------------------------------
# Resolve paths
# ---------------------------------------------------
THIS_FILE = Path(__file__).resolve()
SERVER_ROOT = THIS_FILE.parents[1]  # .../Software Code/Server

REPORTS_DIR = SERVER_ROOT / "core" / "data" / "reports"
OUT_DIR = REPORTS_DIR / "graphs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

print("📁 Reports Dir:", REPORTS_DIR)
print("📊 Graph Output Dir:", OUT_DIR)


# ---------------------------------------------------
# Helper: find latest file by modified time
# ---------------------------------------------------
def latest_file(directory: Path, pattern: str):
    files = list(directory.glob(pattern))
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


# ---------------------------------------------------
# 1) Try to find the latest CSV in reports/
# ---------------------------------------------------
latest_csv = latest_file(REPORTS_DIR, "*.csv")

if latest_csv:
    print("✅ Found CSV:", latest_csv.name)
    df = pd.read_csv(latest_csv)

    # --- You must have at least one of these columns to plot meaningful graphs ---
    print("📌 Columns found:", list(df.columns))

    # ---------------------------------------------------
    # GRAPH A: count per frame if frame_id exists
    # ---------------------------------------------------
    if "frame_id" in df.columns:
        plt.figure(figsize=(8, 4))
        df.groupby("frame_id").size().plot(kind="line")
        plt.title("Detections per Frame")
        plt.xlabel("Frame ID")
        plt.ylabel("Detections")
        plt.tight_layout()
        plt.savefig(OUT_DIR / "detections_per_frame.png")
        plt.show()
    else:
        print("⚠️ frame_id not found → skipping detections_per_frame graph")

    # ---------------------------------------------------
    # GRAPH B: Normal vs Threat if is_abnormal exists
    # ---------------------------------------------------
    if "is_abnormal" in df.columns:
        plt.figure(figsize=(6, 4))
        df["is_abnormal"].value_counts().rename({False: "Normal", True: "Threat"}).plot(
            kind="bar"
        )
        plt.title("Normal vs Threat Detections")
        plt.ylabel("Count")
        plt.tight_layout()
        plt.savefig(OUT_DIR / "normal_vs_threat.png")
        plt.show()
    else:
        print("⚠️ is_abnormal not found → skipping normal_vs_threat graph")

    # ---------------------------------------------------
    # GRAPH C: Threat confidence distribution
    # ---------------------------------------------------
    if "confidence" in df.columns and "is_abnormal" in df.columns:
        threats = df[df["is_abnormal"] == True]
        if not threats.empty:
            plt.figure(figsize=(6, 4))
            threats["confidence"].hist(bins=12)
            plt.title("Threat Confidence Distribution")
            plt.xlabel("Confidence")
            plt.ylabel("Frequency")
            plt.tight_layout()
            plt.savefig(OUT_DIR / "threat_confidence.png")
            plt.show()
        else:
            print("⚠️ No threat rows found → skipping threat_confidence graph")
    else:
        print("⚠️ confidence/is_abnormal not found → skipping threat_confidence graph")

    print("✅ Graphs created from CSV successfully!")
    raise SystemExit(0)


# ---------------------------------------------------
# 2) If no CSV found: use latest analytics_*_summary.txt
# ---------------------------------------------------
latest_summary = latest_file(REPORTS_DIR, "analytics_*_summary.txt")

if not latest_summary:
    raise FileNotFoundError(
        f"❌ No CSV or analytics_*_summary.txt found inside:\n{REPORTS_DIR}"
    )

print("✅ No CSV found. Using summary:", latest_summary.name)

text = latest_summary.read_text(encoding="utf-8", errors="ignore")

# Extract numbers from summary text (flexible patterns)
def extract_float(label_patterns):
    for pat in label_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return float(m.group(1))
    return None

total_visitors = extract_float([r"total_visitors\s*[:=]\s*([0-9.]+)", r"visitors\s*[:=]\s*([0-9.]+)"])
purchasers = extract_float([r"purchasers\s*[:=]\s*([0-9.]+)"])
conversion_rate = extract_float([r"conversion_rate\s*[:=]\s*([0-9.]+)"])
avg_duration = extract_float([r"avg_visit_duration\s*[:=]\s*([0-9.]+)", r"avg_duration\s*[:=]\s*([0-9.]+)"])

# Build a tiny dataframe for plotting
metrics = {
    "Total Visitors": total_visitors or 0,
    "Purchasers": purchasers or 0,
    "Conversion Rate (%)": conversion_rate or 0,
    "Avg Duration (s)": avg_duration or 0,
}

print("📌 Extracted metrics:", metrics)

# ---------------------------------------------------
# GRAPH 1: Key Metrics Bar Chart
# ---------------------------------------------------
plt.figure(figsize=(8, 4))
plt.bar(metrics.keys(), metrics.values())
plt.title("Analytics Summary Metrics")
plt.xticks(rotation=20, ha="right")
plt.tight_layout()
plt.savefig(OUT_DIR / "summary_metrics.png")
plt.show()

# ---------------------------------------------------
# GRAPH 2: Visitors vs Purchasers
# ---------------------------------------------------
plt.figure(figsize=(6, 4))
plt.bar(["Visitors", "Purchasers"], [metrics["Total Visitors"], metrics["Purchasers"]])
plt.title("Visitors vs Purchasers")
plt.tight_layout()
plt.savefig(OUT_DIR / "visitors_vs_purchasers.png")
plt.show()

print("✅ Graphs created from summary.txt successfully!")
print(f"📁 Saved in: {OUT_DIR}")
