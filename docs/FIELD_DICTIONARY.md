# CRM field dictionary

API names are exact contracts. Mandatory flags require layout configuration in Zoho after provisioning.

The Students display field `Name` is an auto-number labelled Student ID. Never calculate IDs with record counts.

## Academic_Years
Academic year boundaries

| Field | Type | Required | Constraint or relation |
|---|---|---|---|
| Record_Key | text | Yes | Unique;  |
| Start_Date | date | Yes |  |
| End_Date | date | Yes |  |
| Is_Current | boolean | Yes |  |

## School_Classes
Reusable grades

| Field | Type | Required | Constraint or relation |
|---|---|---|---|
| Record_Key | text | Yes | Unique;  |
| Sort_Order | integer | Yes |  |

## Class_Sections
A class section for one academic year

| Field | Type | Required | Constraint or relation |
|---|---|---|---|
| Record_Key | text | Yes | Unique;  |
| Academic_Year | lookup | Yes | Academic_Years |
| School_Class | lookup | Yes | School_Classes |
| Section_Label | text | Yes |  |

## Subjects
Subject catalogue

| Field | Type | Required | Constraint or relation |
|---|---|---|---|
| Record_Key | text | Yes | Unique;  |

## Teachers
Teacher roster

| Field | Type | Required | Constraint or relation |
|---|---|---|---|
| Record_Key | text | Yes | Unique;  |
| Email | email | Yes |  |
| Is_Active | boolean | Yes |  |

## Teaching_Assignments
Subject and teacher allocation for a section

| Field | Type | Required | Constraint or relation |
|---|---|---|---|
| Record_Key | text | Yes | Unique;  |
| Class_Section | lookup | Yes | Class_Sections |
| Subject | lookup | Yes | Subjects |
| Teacher | lookup | Yes | Teachers |

## Guardians
Verified parent identity; admin managed

| Field | Type | Required | Constraint or relation |
|---|---|---|---|
| Email_Key | text | No | Unique; SHA256 of trimmed lowercase Email; populated before verification |
| Email | email | Yes |  |
| Identity_Verified | boolean | Yes |  |
| Portal_Enabled | boolean | Yes |  |

## Students
One permanent student identity; Name is the generated Student ID

| Field | Type | Required | Constraint or relation |
|---|---|---|---|
| Admission_Key | text | Yes | Unique;  |
| Full_Name | text | Yes |  |
| Date_Of_Birth | date | Yes |  |
| Student_Status | picklist | Yes | Active, Withdrawn, Graduated |

## Student_Guardians
Many to many verified parent access grants

| Field | Type | Required | Constraint or relation |
|---|---|---|---|
| Record_Key | text | Yes | Unique;  |
| Student | lookup | Yes | Students |
| Guardian | lookup | Yes | Guardians |
| Relationship | picklist | Yes | Parent, Legal Guardian |
| Access_Enabled | boolean | Yes |  |

## Enrollments
Immutable historical enrollment with explicit attendance interval

| Field | Type | Required | Constraint or relation |
|---|---|---|---|
| Record_Key | text | Yes | Unique;  |
| Active_Key | text | Yes | Unique;  |
| Student | lookup | Yes | Students |
| Class_Section | lookup | Yes | Class_Sections |
| Start_Date | date | Yes |  |
| End_Date | date | Yes |  |
| Enrollment_Status | picklist | Yes | Current, Completed, Withdrawn |
| Attendance_Percent | percent | No |  |
| Marked_Days | integer | No |  |
| Unmarked_Days | integer | No |  |

## School_Days
Teaching day calendar; weekends and holidays exist only if explicitly configured

| Field | Type | Required | Constraint or relation |
|---|---|---|---|
| Record_Key | text | Yes | Unique;  |
| Class_Section | lookup | Yes | Class_Sections |
| School_Date | date | Yes |  |

## Attendance
Exactly one daily mark per enrollment

| Field | Type | Required | Constraint or relation |
|---|---|---|---|
| Record_Key | text | Yes | Unique;  |
| Enrollment | lookup | Yes | Enrollments |
| Attendance_Date | date | Yes |  |
| Attendance_Status | picklist | Yes | Present, Absent, Late, Excused |
| Present_Units | double | Yes |  |
| Eligible_Units | integer | Yes |  |

## Examinations
Examination event for one section

| Field | Type | Required | Constraint or relation |
|---|---|---|---|
| Record_Key | text | Yes | Unique;  |
| Class_Section | lookup | Yes | Class_Sections |
| Exam_Date | date | Yes |  |
| Is_Published | boolean | Yes |  |

## Exam_Papers
Subject paper with its own marks scale

| Field | Type | Required | Constraint or relation |
|---|---|---|---|
| Record_Key | text | Yes | Unique;  |
| Examination | lookup | Yes | Examinations |
| Teaching_Assignment | lookup | Yes | Teaching_Assignments |
| Max_Marks | double | Yes |  |
| Pass_Marks | double | Yes |  |

## Results
Student paper result; scale snapshots prevent retroactive distortion

| Field | Type | Required | Constraint or relation |
|---|---|---|---|
| Record_Key | text | Yes | Unique;  |
| Enrollment | lookup | Yes | Enrollments |
| Exam_Paper | lookup | Yes | Exam_Papers |
| Marks | double | Yes |  |
| Was_Absent | boolean | Yes |  |
| Max_Marks_Snapshot | double | Yes |  |
| Pass_Marks_Snapshot | double | Yes |  |
| Percentage | percent | Yes |  |
| Outcome | picklist | Yes | Pass, Fail, Absent |

## Fee_Invoices
A charge with derived ledger totals

| Field | Type | Required | Constraint or relation |
|---|---|---|---|
| Record_Key | text | Yes | Unique;  |
| Enrollment | lookup | Yes | Enrollments |
| Total_Fee | currency | Yes |  |
| Due_Date | date | Yes |  |
| Amount_Collected | currency | No |  |
| Outstanding | currency | No |  |
| Credit_Balance | currency | No |  |
| Payment_Status | picklist | No | Unpaid, Part Paid, Paid, Credit |
| Reconciled_At | datetime | No |  |

## Payments
Append only installment ledger; voids require administrator reason

| Field | Type | Required | Constraint or relation |
|---|---|---|---|
| Payment_Reference | text | Yes | Unique;  |
| Fee_Invoice | lookup | Yes | Fee_Invoices |
| Amount | currency | Yes |  |
| Payment_Date | date | Yes |  |
| Payment_State | picklist | Yes | Posted, Void |
| Void_Reason | text | No |  |

## Fee_Follow_Ups
Deduplicated daily overdue work queue

| Field | Type | Required | Constraint or relation |
|---|---|---|---|
| Record_Key | text | Yes | Unique;  |
| Fee_Invoice | lookup | Yes | Fee_Invoices |
| Review_Date | date | Yes |  |
| Balance_At_Review | currency | Yes |  |
| Follow_Up_Status | picklist | Yes | Open, Resolved |
| Resolution_Note | text | No |  |

## Leads
Admission enquiry

| Field | Type | Required | Constraint or relation |
|---|---|---|---|
| Child_Name | text | Yes |  |
| Child_DOB | date | Yes |  |
| Enrollment_Start | date | No | Required before approval; supports midyear admissions |
| Admission_Status | picklist | Yes | New, Contacted, Visit Scheduled, Documents Pending, Approved, Confirmed, Rejected |
| Requested_Section | lookup | No | Class_Sections |
| Verified_Guardian | lookup | No | Guardians |
| Admitted_Student | lookup | No | Students |
| Admission_Error | text | No |  |
| Parent_Consent | boolean | Yes |  |
