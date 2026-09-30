"""CRM V8 metadata provisioning. Defaults to an offline plan; never deletes.

Live calls require --apply and environment credentials. This does not install
Deluge, permissions, workflows, Creator pages, reports, or the CRM webform.
"""
import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_DOMAINS = {"www.zohoapis.com","www.zohoapis.in","www.zohoapis.eu",
    "www.zohoapis.com.au","www.zohoapis.jp","www.zohoapis.ca","www.zohoapis.sa"}

class APIError(RuntimeError): pass

class CRM:
    def __init__(self, domain, token):
        p = urlparse(domain)
        if p.scheme != "https" or p.netloc not in ALLOWED_DOMAINS or p.path not in ("", "/") or p.query or p.fragment:
            raise ValueError("Use an exact official Zoho API domain without a path")
        self.base = domain.rstrip("/")+"/crm/v8"
        self.token = token

    def call(self, method, path, payload=None):
        data = json.dumps(payload).encode() if payload is not None else None
        req = Request(self.base+path, data=data, method=method,
                      headers={"Authorization":"Zoho-oauthtoken "+self.token,"Content-Type":"application/json"})
        try:
            with urlopen(req, timeout=30) as response:
                raw = response.read()
                result = json.loads(raw) if raw else {}
        except HTTPError as e:
            # Do not print response bodies, auth headers or record contents.
            raise APIError(f"Zoho returned HTTP {e.code} for {method} {path}. Inspect the org and rerun; writes are not blindly retried.") from None
        if result.get("status")=="error": raise APIError(result.get("code","API_ERROR"))
        return result

def field_payload(f, module_ids):
    p = {"field_label":f["field_label"],"data_type":f["data_type"]}
    if "unique" in f: p["unique"] = f["unique"]
    if f["data_type"]=="lookup":
        p["lookup"] = {"module":{"id":module_ids[f["target"]],"api_name":f["target"]},"display_label":f["field_label"]}
    if f["data_type"]=="picklist":
        p["pick_list_values"] = [{"display_value":v,"actual_value":v} for v in f["values"]]
    if f["data_type"]=="text": p["length"]=200
    if f["data_type"]=="integer": p["length"]=9
    if f["data_type"] in ("double","percent"):
        p.update(length=12,decimal_place=2)
    if f["data_type"]=="currency":
        p.update(length=16,decimal_place=3,currency={"rounding_option":"round_off","precision":2})
    return p

def check_results(result, key):
    rows = result.get(key, [])
    if not rows or any(r.get("status") != "success" for r in rows):
        codes = [r.get("code","MISSING_RESULT") for r in rows]
        raise APIError("Metadata write failed: "+", ".join(codes))

def provision(api, spec, profile_id):
    # Restrict newly created modules to the selected deployment admin profile.
    modules = {m["api_name"]:m for m in api.call("GET","/settings/modules")["modules"]}
    for m in spec["modules"]:
        if m["api_name"] in modules: continue
        display = {"field_label":"Student ID" if m["api_name"]=="Students" else m["singular_label"]+" Name","data_type":"text"}
        if m["auto_prefix"]:
            display.update(data_type="autonumber",auto_number={"prefix":m["auto_prefix"],"start_number":1001})
        body = {"modules":[{"plural_label":m["plural_label"],"singular_label":m["singular_label"],"api_name":m["api_name"],"profiles":[{"id":profile_id}],"display_field":display}]}
        check_results(api.call("POST","/settings/modules",body),"modules")
        print("Created module", m["api_name"])
    modules = {m["api_name"]:m for m in api.call("GET","/settings/modules")["modules"]}
    ids = {k:v["id"] for k,v in modules.items()}
    for m in spec["modules"]+[{"api_name":"Leads","fields":spec["leads_fields"]}]:
        path = "/settings/fields?"+urlencode({"module":m["api_name"]})
        existing = {f["api_name"]:f for f in api.call("GET",path)["fields"]}
        for f in m["fields"]:
            if f["api_name"] in existing:
                old=existing[f["api_name"]]
                if old["data_type"]!=f["data_type"]: raise APIError("Type conflict: "+m["api_name"]+"."+f["api_name"])
                if f.get("unique") and not old.get("unique"): raise APIError("Missing uniqueness on "+f["api_name"])
                if f.get("target") and old.get("lookup",{}).get("module",{}).get("api_name")!=f["target"]:
                    raise APIError("Lookup target conflict: "+f["api_name"])
                continue
            # One field per call trades speed for clear, resumable failure boundaries.
            check_results(api.call("POST",path,{"fields":[field_payload(f,ids)]}),"fields")
            created = {x["api_name"]:x for x in api.call("GET",path)["fields"]}
            if f["api_name"] not in created:
                raise APIError("Generated API name differs for "+m["api_name"]+"."+f["api_name"]+". Set its API name in CRM before continuing.")
            print("Created field",m["api_name"]+"."+f["api_name"])
    print("Metadata installed. Continue with docs/DEPLOYMENT.md. Live verification is still required.")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--apply",action="store_true",help="Create missing CRM metadata in the selected org")
    args=parser.parse_args()
    spec=json.loads((ROOT/"schema/crm_schema.json").read_text())
    if not args.apply:
        print(json.dumps({"mode":"OFFLINE PLAN","custom_modules":len(spec["modules"]),"custom_fields":sum(len(m["fields"]) for m in spec["modules"])+len(spec["leads_fields"]),"module_names":[m["api_name"] for m in spec["modules"]],"external_changes":False},indent=2))
        return
    required=["ZOHO_ACCESS_TOKEN","ZOHO_API_DOMAIN","ZOHO_ADMIN_PROFILE_ID"]
    if any(not os.environ.get(k) for k in required):
        raise SystemExit("Set "+", ".join(required)+" in your local environment. Do not paste credentials in chat.")
    provision(CRM(os.environ["ZOHO_API_DOMAIN"],os.environ["ZOHO_ACCESS_TOKEN"]),spec,os.environ["ZOHO_ADMIN_PROFILE_ID"])

if __name__=="__main__":
    try: main()
    except (APIError,ValueError) as e: sys.exit(str(e))
