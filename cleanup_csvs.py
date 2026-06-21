"""
Delete existing CSV and summary files from the repository root.
Run: python cleanup_csvs.py
This script will prompt for confirmation before deleting files.
"""
import os, glob

patterns = [
    "orders_*.csv",
    "option_chain_summary_*.csv",
    "trading_signals_*.csv",
    "trading_summary.json",
    "trades_history.json",
]

files = []
for p in patterns:
    files.extend(glob.glob(p))

if not files:
    print("No matching files found in repository root.")
    raise SystemExit(0)

print("Files to delete:")
for f in files:
    print(f)

ans = input("Delete these files? Type 'yes' to confirm: ")
if ans.strip().lower() == 'yes':
    for f in files:
        try:
            os.remove(f)
            print(f"Deleted: {f}")
        except Exception as e:
            print(f"Failed to delete {f}: {e}")
    print("Done")
else:
    print("Aborted")
