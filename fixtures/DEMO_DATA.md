# Synthetic demonstration data

Use this scenario only in the evaluation organization. `example.test` is not a deliverable email domain; replace those addresses with controlled test mailboxes when you invite portal users. Do not invite actual parents or use real child data.

| Record | Example values |
|---|---|
| Academic year | AY2026, Name 2026 to 2027, 2026-06-01 to 2027-03-31 |
| Following year | AY2027, Name 2027 to 2028, 2027-06-01 to 2028-03-31 |
| School classes | Class 10, Class 11 |
| Sections | 10A and 10B in AY2026; 11A in AY2027 |
| Subjects | Mathematics, Science |
| Teachers | Teacher Demo One and Teacher Demo Two; active |
| Teaching assignments | 10A Mathematics with Teacher One; 10A Science with Teacher Two |
| Guardian A | Parent A Demo, parent.a@example.test; initially unverified and disabled |
| Guardian B | Parent B Demo, parent.b@example.test; initially unverified and disabled |
| Leads for A | Aarav Demo and Anika Demo; two separate enquiries |
| Lead for B | Diya Demo; third enquiry |
| Student dates of birth | 2011-01-15, 2011-06-20, 2011-04-10 respectively |
| Enrollment start | 2026-06-01 for each demonstration lead |
| School days | 2026-09-17 through 2026-09-21 explicitly listed for the test section |
| Attendance for Aarav | Present on 17, Absent on 18, Late on 19, Excused on 20, no mark on 21 |
| Exam | Midterm Demo, 10A, 2026-09-01, initially unpublished |
| Papers | Mathematics maximum 100/pass 35; Science maximum 50/pass 18 |
| Aarav results | Mathematics 80; Science 25; neither absent |
| Invoice | TERM1, total INR 50000, due 2026-09-01 |
| Payments | DEMO-TXN-001 INR 20000 on 2026-09-20; DEMO-TXN-002 INR 30000 on 2026-09-21 |

Create masters before dependent records. For ordinary text-name modules supply Name. Auto-number modules generate Name. Record keys should be chosen consistently: a Section key combines year and class/section; Teaching Assignment combines section and subject; School Day combines actual section CRM ID and date; Exam Paper combines exam and teaching assignment. Unique keys are case-insensitive.

Run guardian normalization before enabling verified access. Do not set a hash of a fabricated mailbox and then pretend it has been verified. For the real portal test, separately verify controlled mailboxes and create the grants. Enter the three child Leads through the public admission form where possible, then assign sections and approve.

Expected calculations: recorded attendance 2/3 = 66.67%, four marked days, one unmarked day; weighted exam score 105/150 = 70%; initial fee status Unpaid, after first installment Part Paid with INR 30000 outstanding, after second installment Paid. Run the overdue feature before the final payment to demonstrate a work item. Promoting Aarav to AY2027 must preserve the old attendance, results and fee history.

The reference test date is fixed at 22 September 2026 for reproducibility; live scripts use the organization's current date. Use the selected test dates consistently when comparing evidence.
