"""Deterministic CRM metadata specification. No network calls."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def field(name, kind="text", *, required=True, unique=False, target=None, values=None, note=""):
    result = dict(api_name=name, field_label=name.replace("_", " "), data_type=kind,
                  required=required, note=note)
    if unique: result["unique"] = {"case_sensitive": False}
    if target: result["target"] = target
    if values: result["values"] = values.split("|")
    return result

def lookup(name, target, **kw): return field(name, "lookup", target=target, **kw)
def choice(name, values, **kw): return field(name, "picklist", values=values, **kw)
def key(name="Record_Key"): return field(name, unique=True)
def date(name, **kw): return field(name, "date", **kw)
def money(name, **kw): return field(name, "currency", **kw)
def flag(name, **kw): return field(name, "boolean", **kw)

MODULES = []
def module(api, singular, fields, prefix=None, purpose=""):
    MODULES.append(dict(api_name=api, singular_label=singular,
        plural_label=api.replace("_", " "), auto_prefix=prefix, purpose=purpose, fields=fields))

module("Academic_Years", "Academic Year", [key(),date("Start_Date"),date("End_Date"),flag("Is_Current")], purpose="Academic year boundaries")
module("School_Classes", "School Class", [key(),field("Sort_Order","integer")], purpose="Reusable grades")
module("Class_Sections", "Class Section", [key(),lookup("Academic_Year","Academic_Years"),lookup("School_Class","School_Classes"),field("Section_Label")], purpose="A class section for one academic year")
module("Subjects", "Subject", [key()], purpose="Subject catalogue")
module("Teachers", "Teacher", [key(),field("Email","email"),flag("Is_Active")], purpose="Teacher roster")
module("Teaching_Assignments", "Teaching Assignment", [key(),lookup("Class_Section","Class_Sections"),lookup("Subject","Subjects"),lookup("Teacher","Teachers")], purpose="Subject and teacher allocation for a section")
module("Guardians", "Guardian", [field("Email_Key",unique=True,required=False,note="SHA256 of trimmed lowercase Email; populated before verification"),field("Email","email"),flag("Identity_Verified"),flag("Portal_Enabled")], purpose="Verified parent identity; admin managed")
module("Students", "Student", [key("Admission_Key"),field("Full_Name"),date("Date_Of_Birth"),choice("Student_Status","Active|Withdrawn|Graduated")], prefix="STU", purpose="One permanent student identity; Name is the generated Student ID")
module("Student_Guardians", "Student Guardian", [key(),lookup("Student","Students"),lookup("Guardian","Guardians"),choice("Relationship","Parent|Legal Guardian"),flag("Access_Enabled")], purpose="Many to many verified parent access grants")
module("Enrollments", "Enrollment", [key(),key("Active_Key"),lookup("Student","Students"),lookup("Class_Section","Class_Sections"),date("Start_Date"),date("End_Date"),choice("Enrollment_Status","Current|Completed|Withdrawn"),field("Attendance_Percent","percent",required=False),field("Marked_Days","integer",required=False),field("Unmarked_Days","integer",required=False)], prefix="ENR", purpose="Immutable historical enrollment with explicit attendance interval")
module("School_Days", "School Day", [key(),lookup("Class_Section","Class_Sections"),date("School_Date")], purpose="Teaching day calendar; weekends and holidays exist only if explicitly configured")
module("Attendance", "Attendance Entry", [key(),lookup("Enrollment","Enrollments"),date("Attendance_Date"),choice("Attendance_Status","Present|Absent|Late|Excused"),field("Present_Units","double"),field("Eligible_Units","integer")], prefix="ATT", purpose="Exactly one daily mark per enrollment")
module("Examinations", "Examination", [key(),lookup("Class_Section","Class_Sections"),date("Exam_Date"),flag("Is_Published")], purpose="Examination event for one section")
module("Exam_Papers", "Exam Paper", [key(),lookup("Examination","Examinations"),lookup("Teaching_Assignment","Teaching_Assignments"),field("Max_Marks","double"),field("Pass_Marks","double")], purpose="Subject paper with its own marks scale")
module("Results", "Result", [key(),lookup("Enrollment","Enrollments"),lookup("Exam_Paper","Exam_Papers"),field("Marks","double"),flag("Was_Absent"),field("Max_Marks_Snapshot","double"),field("Pass_Marks_Snapshot","double"),field("Percentage","percent"),choice("Outcome","Pass|Fail|Absent")], prefix="RES", purpose="Student paper result; scale snapshots prevent retroactive distortion")
module("Fee_Invoices", "Fee Invoice", [key(),lookup("Enrollment","Enrollments"),money("Total_Fee"),date("Due_Date"),money("Amount_Collected",required=False),money("Outstanding",required=False),money("Credit_Balance",required=False),choice("Payment_Status","Unpaid|Part Paid|Paid|Credit",required=False),field("Reconciled_At","datetime",required=False)], prefix="INV", purpose="A charge with derived ledger totals")
module("Payments", "Payment", [key("Payment_Reference"),lookup("Fee_Invoice","Fee_Invoices"),money("Amount"),date("Payment_Date"),choice("Payment_State","Posted|Void"),field("Void_Reason",required=False)], prefix="PAY", purpose="Append only installment ledger; voids require administrator reason")
module("Fee_Follow_Ups", "Fee Follow Up", [key(),lookup("Fee_Invoice","Fee_Invoices"),date("Review_Date"),money("Balance_At_Review"),choice("Follow_Up_Status","Open|Resolved"),field("Resolution_Note",required=False)], prefix="FLW", purpose="Deduplicated daily overdue work queue")

LEAD_FIELDS = [field("Child_Name"),date("Child_DOB"),date("Enrollment_Start",required=False,note="Required before approval; supports midyear admissions"),choice("Admission_Status","New|Contacted|Visit Scheduled|Documents Pending|Approved|Confirmed|Rejected"),lookup("Requested_Section","Class_Sections",required=False),lookup("Verified_Guardian","Guardians",required=False),lookup("Admitted_Student","Students",required=False),field("Admission_Error",required=False),flag("Parent_Consent")]

def build():
    spec = dict(version=1, timezone="Asia/Kolkata", currency="INR", live_deployed=False,
                modules=MODULES, leads_fields=LEAD_FIELDS)
    (ROOT/"schema/crm_schema.json").write_text(json.dumps(spec,indent=2)+"\n")
    lines=["# CRM field dictionary", "", "API names are exact contracts. Mandatory flags require layout configuration in Zoho after provisioning.","", "The Students display field `Name` is an auto-number labelled Student ID. Never calculate IDs with record counts.", ""]
    for m in MODULES + [dict(api_name="Leads", purpose="Admission enquiry", fields=LEAD_FIELDS)]:
        lines += ["## "+m["api_name"],m["purpose"],"", "| Field | Type | Required | Constraint or relation |", "|---|---|---|---|"]
        for f in m["fields"]:
            detail=f.get("target") or ", ".join(f.get("values",[])) or f.get("note","")
            if f.get("unique"): detail="Unique; "+detail
            lines.append(f'| {f["api_name"]} | {f["data_type"]} | {"Yes" if f["required"] else "No"} | {detail} |')
        lines.append("")
    (ROOT/"docs/FIELD_DICTIONARY.md").write_text("\n".join(lines))
    print(f"Generated {len(MODULES)} modules and {sum(len(m['fields']) for m in MODULES)+len(LEAD_FIELDS)} custom fields")

if __name__ == "__main__": build()
