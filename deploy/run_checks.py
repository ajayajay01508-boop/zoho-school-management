"""Reproducible local evidence; explicitly excludes live Zoho validation."""
import datetime
import json
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
result=subprocess.run([sys.executable,"-m","unittest","discover","-s","tests","-v"],cwd=ROOT,text=True,capture_output=True)
text=result.stdout+result.stderr
(ROOT/"evidence/local-test-results.txt").write_text("LOCAL PYTHON REFERENCE AND PACKAGE TESTS ONLY\nNot Deluge runtime, Zoho integration, or live security tests.\n\n"+text)
summary={"generated_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"local_tests_passed":result.returncode==0,"zoho_deluge_compiled":False,"zoho_crm_deployed":False,"creator_deployed":False,"webform_live":False,"submission_sent":False}
(ROOT/"evidence/verification-status.json").write_text(json.dumps(summary,indent=2)+"\n")
print(text)
sys.exit(result.returncode)
