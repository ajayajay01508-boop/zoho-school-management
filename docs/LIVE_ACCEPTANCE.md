# Live acceptance and submission gate

All cases below are **NOT RUN IN ZOHO**. The local evidence covers only the Python reference model and source-package checks. Replace status with Pass or Fail only after execution in the actual CRM and parent portal; include the observed record ID or screenshot reference.

| ID | Test | Expected outcome |
|---|---|---|
| Z01 | Create modules and fields | API names, lookups, unique keys and required layouts match the schema |
| Z02 | Compile every CRM and Creator function | No compiler errors; actual return types verified |
| Z03 | Submit real published CRM webform | Exactly one New Lead; no student or portal grant created automatically |
| Z04 | Reject an enquiry | Lead retained as Rejected; no student created |
| Z05 | Approve a complete enquiry | One Student, one enrollment, verified relationship, Confirmed Lead |
| Z06 | Repeat the approval operation | Same student/enrollment; no duplicate |
| Z07 | Approve with missing consent or unverified guardian | Rejected before student creation; meaningful error |
| Z08 | Midyear admission | Attendance starts on the supplied Enrollment Start, not the beginning of the year |
| Z09 | Valid daily attendance | Record stored with correct unique key and computed units |
| Z10 | Duplicate attendance from two submissions | One daily mark; contradictory status rejected |
| Z11 | Future, out-of-range, invalid date or nonteaching day | No attendance record written |
| Z12 | Present, Late, Absent, Excused and one missing day | 66.67% over three eligible marked days; one unmarked day |
| Z13 | Invalid or wrong-section exam marks | Rejected before insertion |
| Z14 | Repeated result request | Exact retry ignored; conflicting marks rejected |
| Z15 | Mixed paper maxima | 80/100 and 25/50 aggregate to 70%, not 65% |
| Z16 | Unpublished and published examination | Hidden from parent before publication; write locked after publication |
| Z17 | Fee installments 20000 and 30000 against 50000 | Part Paid then Paid; history retained |
| Z18 | Concurrent same payment reference | One payment; changing amount with same reference rejected |
| Z19 | Overpayment 55000 against 50000 | Outstanding zero, credit 5000, Credit status |
| Z20 | Void by admin with reason | History retained; totals recomputed; no normal user can void |
| Z21 | Parent A sign-in | Only A's children and their records visible |
| Z22 | Tamper sid to parent B's student | Access denied before student data query |
| Z23 | Tamper eid to a different student's enrollment | Access denied |
| Z24 | Anonymous page, generic API and raw form access | No student records or server connection access |
| Z25 | Disable grant or Guardian; change email | Next page request denied; re-verification required |
| Z26 | Seed HTML/script-like text in a child name | Displayed as escaped text; no execution |
| Z27 | More than ten payments or attendance rows | Next/Previous paginate correctly without dropping records |
| Z28 | Simulated CRM connection failure | Error message; no foreign or stale fallback records |
| Z29 | Promotion and retry | Prior year retained; single current enrollment; same retry reuses new enrollment |
| Z30 | Interrupt promotion between writes | Error and recoverable state; same-pair retry succeeds |
| Z31 | Run overdue batch twice | One invoice-date item; settled invoices excluded |
| Z32 | Force a batch failure and resume | Cursor does not skip failed work |
| Z33 | Summary race or void repair | Reconciliation matches posted ledger sums |
| Z34 | Teacher, admission, finance and unauthorized user | Each permitted operation works; forbidden direct/API writes fail |
| Z35 | All reports and dashboard | Roster, sums and attendance match source records |
| Z36 | Reviewer links in independent authorized session | CRM, parent portal and webform are accessible as intended |

## Evidence checklist

Record the actual CRM organization URL, Creator portal URL and published webform URL. Capture CRM module relationships, approval result, duplicate rejection, attendance summary, exam results, installment ledger, fee work queue and two different parent views. Redact real email addresses and avoid screenshots of authentication or tokens. Use synthetic student data only.

Record the account edition, region, timezone, tested user profiles, date and untested limitations. The SQL reference uses database transactions for some tests, while Deluge spans separate CRM calls; local concurrency success is not proof of CRM atomicity. Run the live retry and race scenarios independently.

## Completion decision

The assignment can be described as completed only after the live CRM, parent application and real webform work and the account-specific security checks pass. Source files, plans, screenshots of a mock app, or the 42 local checks alone do not satisfy the employer's live-access requirements. No live completion is currently recorded.
