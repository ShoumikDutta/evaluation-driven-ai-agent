import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agents.single_agent import run_task

query = " ".join(sys.argv[1:]) or "Run a CRM data quality audit and show severity split."
print(json.dumps(run_task(query), indent=2))
