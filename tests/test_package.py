import json
import unittest
from pathlib import Path
from deploy.provision import field_payload, CRM, check_results, APIError

ROOT=Path(__file__).resolve().parents[1]

class PackageTests(unittest.TestCase):
    def setUp(self): self.schema=json.loads((ROOT/"schema/crm_schema.json").read_text())
    def test_all_lookup_targets_exist(self):
        modules={m["api_name"] for m in self.schema["modules"]}
        for m in self.schema["modules"]:
            for f in m["fields"]:
                if "target" in f:self.assertIn(f["target"],modules)
    def test_unique_field_limits(self):
        for m in self.schema["modules"]:
            self.assertLessEqual(sum(bool(f.get("unique")) for f in m["fields"]),2,m["api_name"])
    def test_modules_and_field_names_are_unique(self):
        names=[m["api_name"] for m in self.schema["modules"]]
        self.assertEqual(len(names),len(set(names)))
        for m in self.schema["modules"]:
            fields=[f["api_name"] for f in m["fields"]]
            self.assertEqual(len(fields),len(set(fields)))
    def test_provision_payload_includes_lookup_and_currency_dependencies(self):
        ids={m["api_name"]:str(i+1) for i,m in enumerate(self.schema["modules"])}
        for m in self.schema["modules"]:
            for f in m["fields"]:
                payload=field_payload(f,ids)
                if f["data_type"]=="lookup":self.assertEqual(payload["lookup"]["module"]["api_name"],f["target"])
                if f["data_type"]=="currency":self.assertIn("rounding_option",payload["currency"])
    def test_api_client_rejects_non_zoho_hosts_and_paths(self):
        for url in ["http://www.zohoapis.in","https://www.zohoapis.in.evil.test","https://example.test","https://www.zohoapis.in/crm","https://www.zohoapis.in?token=x"]:
            with self.subTest(url=url),self.assertRaises(ValueError):CRM(url,"dummy")
    def test_metadata_partial_failure_is_not_success(self):
        with self.assertRaises(APIError):check_results({"fields":[{"status":"success"},{"status":"error","code":"INVALID_DATA"}]},"fields")
    def test_parent_identity_is_not_a_page_argument(self):
        source=(ROOT/"deluge/creator/03_parent_data.deluge").read_text()
        self.assertIn("thisapp.portal.loginUserEmailid()",source)
        self.assertNotIn("input.email",source)
        self.assertIn("if(!allowedEnrollment)",source)
    def test_no_claim_of_live_verification_in_schema(self):
        self.assertIs(self.schema["live_deployed"],False)

if __name__=="__main__":unittest.main()
