import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from config import JOB_DATA_DIR

# Find the most recent results file
files = sorted(os.listdir(JOB_DATA_DIR))
latest = os.path.join(JOB_DATA_DIR, files[-1])

print(f"Reading: {latest}\n")

with open(latest, "r", encoding="utf-8") as f:
    jobs = json.load(f)

for i, job in enumerate(jobs):
    print(f"{i+1}. {job['title']} @ {job['company']} ({job['source']})")

