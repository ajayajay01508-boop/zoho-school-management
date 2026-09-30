"""Change hardcoded Deluge API endpoints to the org's official data centre."""
import argparse
from pathlib import Path
from provision import ALLOWED_DOMAINS

parser=argparse.ArgumentParser()
parser.add_argument("domain",choices=sorted(ALLOWED_DOMAINS))
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
for file in (root/"deluge").rglob("*.deluge"):
    text=file.read_text()
    for domain in ALLOWED_DOMAINS:
        text=text.replace("https://"+domain+"/crm/","https://"+args.domain+"/crm/")
    file.write_text(text)
print("Configured Deluge for",args.domain)
