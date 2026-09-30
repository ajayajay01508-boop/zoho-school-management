"""Wrap an unmodified Zoho-generated webform in a simple school landing page.

Requires an actual form export from the target CRM organization. No fake IDs.
"""
import argparse
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

class FormInspector(HTMLParser):
    def __init__(self):super().__init__();self.actions=[];self.fields=set()
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=="form":self.actions.append(a.get("action",""))
        if tag=="input":self.fields.add(a.get("name",""))

def assemble(source,target):
    raw=Path(source).read_text(encoding="utf-8")
    parsed=FormInspector();parsed.feed(raw)
    valid_hosts={"crm.zoho.com","crm.zoho.in","crm.zoho.eu","crm.zoho.com.au","crm.zoho.jp","crm.zoho.ca","crm.zoho.sa"}
    if len(parsed.actions)!=1:raise ValueError("Expected exactly one exported Zoho CRM form")
    url=urlparse(parsed.actions[0])
    if url.scheme!="https" or url.hostname not in valid_hosts or not url.path.endswith("/WebToLeadForm"):
        raise ValueError("Use the official CRM WebToLeadForm export for your organization")
    if not {"xnQsjsdp","xmIwtLD","actionType"}.issubset(parsed.fields):
        raise ValueError("Missing Zoho-generated form routing fields")
    if "<html" in raw.lower():raise ValueError("Export the form embed snippet, not a complete HTML page")
    html='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>School admission enquiry</title><style>body{font-family:Arial,sans-serif;background:#f3f6f9;color:#183044;margin:0;padding:30px}main{max-width:800px;margin:auto;background:white;padding:30px;border-radius:12px}p{line-height:1.5}footer{font-size:12px;color:#526575;margin-top:24px}</style></head><body><main><h1>School admission enquiry</h1><p>Tell our admission team about your child. Submitting an enquiry does not confirm admission.</p>'''+raw+'''<footer>School Management System · Prepared for Ajay S</footer></main></body></html>'''
    Path(target).write_text(html,encoding="utf-8")

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("exported_form");parser.add_argument("output")
    args=parser.parse_args();assemble(args.exported_form,args.output)
    print("Created",args.output,"from the supplied Zoho form. Test its public URL before submission.")
