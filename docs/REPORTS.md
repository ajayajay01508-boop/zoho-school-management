# Management reports and dashboard

These are build definitions. The reports have not been created or inspected in a live CRM organization.

| Report | Base data | Group and filter | Management metric |
|---|---|---|---|
| Admission funnel | Leads | Admission Status, enquiry date range | Enquiries by stage; confirmed divided by all enquiries in the same cohort |
| Admission exceptions | Leads | Admission Error is not empty, or Approved without Admitted Student | Failed or incomplete processing |
| Current class roster | Enrollments with Students and Class Sections | Enrollment Status=Current; year and class section | Current headcount without counting alumni |
| Attendance register | Attendance with Enrollments | Date, section, student | Daily present, late, absent and excused marks |
| Attendance coverage | Enrollments | Current year; Unmarked Days greater than zero | Missing marks that require teacher action |
| Student attendance | Enrollments | Student and academic year | Recorded attendance percentage, Marked Days, Unmarked Days |
| Subject performance | Results with Exam Papers | Published exams only; section and paper | Average marks and pass count per paper |
| Student exam totals | Results with Exam Papers | Student enrollment and examination | SUM Marks, SUM Max Marks Snapshot; weighted overall percentage |
| Fee position | Fee Invoices | Enrollment, year and Payment Status | Total fees, collected, outstanding and credits |
| Overdue fees | Fee Invoices | Due Date before today; Outstanding greater than zero | Outstanding by class and aging bucket |
| Installment ledger | Payments with Fee Invoices | Payment Date, invoice and state | Posted receipts; voided entries shown separately |
| Daily fee work queue | Fee Follow Ups | Review Date=today, Follow Up Status=Open | Assigned follow-up workload |

Dashboard layout: admission funnel and current student count on the first row, attendance coverage and recorded attendance on the second, examination performance on the third, fee collection and overdue workload on the fourth. Keep admission and fee exceptions reachable from the dashboard.

Use joined related records, not manual copies of student names. Do not sum Total Fee in a report that joins one invoice to multiple payments because that multiplies the invoice total. Use Fee Invoices as the base for fee totals, and Payments as the base for receipt totals. Show the CRM Reconciled At timestamp alongside cached fee figures and run reconciliation before the demo.

For unequal paper maxima, calculate overall percent as 100 × SUM(Marks) / SUM(Max Marks Snapshot). If the CRM report builder cannot represent the ratio accurately in the available edition, show both sums and use a custom dashboard function or exported verified calculation; do not substitute AVG(Percentage). Zero eligible attendance days and zero maximum exam marks must display N/A, not a misleading zero.

Attendance policy is explicit: Present and Late contribute one numerator unit, Present/Late/Absent contribute one denominator unit, Excused contributes neither. Unmarked teaching days are displayed separately and not automatically labelled absent.
