import unittest
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from reference.domain import School,RuleError,Forbidden,Conflict,money,email_key

class DomainTests(unittest.TestCase):
    def setUp(self):
        self.s=School()
        self.s.add_guardian("parent.a@example.test")
        self.s.add_guardian("parent.b@example.test")
        self.args=("LEAD1","Aarav Demo","2026-27","10A","2026-06-01","2027-03-31","parent.a@example.test")
        self.sid,self.eid=self.s.admit(*self.args)
        self.other,self.other_eid=self.s.admit("LEAD2","Diya Demo","2026-27","10B","2026-06-01","2027-03-31","parent.b@example.test")
        self.s.invoice("I1",self.eid,50000,"2026-09-01")
        self.s.paper("MATH","10A","2026-09-01",100,35)

    def test_admission_retry_keeps_student_and_enrollment(self):
        self.assertEqual(self.s.admit(*self.args),(self.sid,self.eid))
        self.assertEqual(self.s.db.execute("SELECT COUNT(*) FROM students").fetchone()[0],2)

    def test_unapproved_admission_rejected(self):
        with self.assertRaises(RuleError): self.s.admit(*self.args,approved=False)

    def test_unverified_parent_cannot_receive_access(self):
        self.s.add_guardian("parent.a@example.test",verified=False)
        with self.assertRaises(Forbidden): self.s.admit(*self.args)

    def test_admission_conflicting_retry_is_rejected(self):
        args=list(self.args);args[1]="Different Child"
        with self.assertRaises(Conflict): self.s.admit(*args)

    def test_cross_parent_student_access_denied(self):
        with self.assertRaises(Forbidden): self.s.allow("parent.a@example.test",self.other)

    def test_cross_parent_enrollment_access_denied(self):
        with self.assertRaises(Forbidden): self.s.allow("parent.a@example.test",self.sid,self.other_eid)

    def test_parent_case_normalization(self):
        self.assertTrue(self.s.allow("  PARENT.A@EXAMPLE.TEST ",self.sid,self.eid))

    def test_revocation_takes_effect_on_next_request(self):
        self.s.db.execute("UPDATE grants SET enabled=0 WHERE student=?",(self.sid,))
        with self.assertRaises(Forbidden): self.s.allow("parent.a@example.test",self.sid)

    def test_portal_disable_denies_access(self):
        self.s.add_guardian("parent.a@example.test",enabled=False)
        with self.assertRaises(Forbidden): self.s.allow("parent.a@example.test",self.sid)

    def test_promotion_preserves_history_and_retries(self):
        eid=self.s.promote(self.sid,"2027-28","11A","2027-06-01","2028-03-31")
        self.assertNotEqual(eid,self.eid)
        self.assertEqual(eid,self.s.promote(self.sid,"2027-28","11A","2027-06-01","2028-03-31"))
        rows=self.s.db.execute("SELECT current FROM enrollments WHERE student=?",(self.sid,)).fetchall()
        self.assertEqual(sum(r[0] for r in rows),1)
        self.assertEqual(len(rows),2)

    def test_overlapping_promotion_rejected(self):
        with self.assertRaises(RuleError): self.s.promote(self.sid,"2027-28","11A","2027-03-01","2028-03-31")

    def test_attendance_zero_denominator_is_not_zero_percent(self):
        self.assertIsNone(self.s.attendance(self.eid)["percent"])

    def test_attendance_duplicate_and_conflict(self):
        self.s.school_day("10A","2026-09-21")
        self.s.mark(self.eid,"2026-09-21","Present")
        self.s.mark(self.eid,"2026-09-21","Present")
        with self.assertRaises(Conflict): self.s.mark(self.eid,"2026-09-21","Absent")
        self.assertEqual(self.s.attendance(self.eid)["marked"],1)

    def test_attendance_holiday_rejected(self):
        with self.assertRaises(RuleError): self.s.mark(self.eid,"2026-09-20","Present")

    def test_attendance_future_rejected(self):
        self.s.school_day("10A","2026-09-23")
        with self.assertRaises(RuleError): self.s.mark(self.eid,"2026-09-23","Present")

    def test_attendance_before_enrollment_rejected(self):
        self.s.school_day("10A","2026-05-01")
        with self.assertRaises(RuleError): self.s.mark(self.eid,"2026-05-01","Present")

    def test_attendance_excused_late_and_unmarked(self):
        for day in [17,18,19,20,21]: self.s.school_day("10A",f"2026-09-{day}")
        for day,status in [(17,"Present"),(18,"Absent"),(19,"Late"),(20,"Excused")]: self.s.mark(self.eid,f"2026-09-{day}",status)
        self.assertEqual(self.s.attendance(self.eid),dict(percent=Decimal("66.67"),marked=4,unmarked=1))

    def test_result_above_maximum_rejected(self):
        with self.assertRaises(RuleError): self.s.result(self.eid,"MATH",101)

    def test_result_negative_rejected(self):
        with self.assertRaises(RuleError): self.s.result(self.eid,"MATH",-1)

    def test_result_wrong_section_rejected(self):
        with self.assertRaises(RuleError): self.s.result(self.other_eid,"MATH",50)

    def test_absence_must_have_zero_marks(self):
        with self.assertRaises(RuleError): self.s.result(self.eid,"MATH",10,True)
        self.s.result(self.eid,"MATH",0,True)

    def test_result_duplicate_and_conflict(self):
        self.s.result(self.eid,"MATH",80);self.s.result(self.eid,"MATH",80)
        with self.assertRaises(Conflict): self.s.result(self.eid,"MATH",81)

    def test_weighted_performance_not_average_of_percentages(self):
        self.s.paper("SCIENCE","10A","2026-09-01",50,18)
        self.s.result(self.eid,"MATH",80);self.s.result(self.eid,"SCIENCE",25)
        self.assertEqual(self.s.performance(self.eid)["percent"],Decimal("70.00"))

    def test_unpublished_results_hidden_and_published_locked(self):
        self.s.result(self.eid,"MATH",80)
        self.assertEqual(self.s.performance(self.eid,published_only=True)["papers"],0)
        self.s.db.execute("UPDATE papers SET published=1 WHERE id='MATH'")
        self.assertEqual(self.s.performance(self.eid,published_only=True)["papers"],1)
        with self.assertRaises(RuleError): self.s.result(self.eid,"MATH",81)

    def test_payment_installments_and_exact_settlement(self):
        self.s.pay("I1","TXN1",20000,"2026-09-20")
        self.assertEqual(self.s.fees("I1")["status"],"Part Paid")
        self.s.pay("I1","TXN2",30000,"2026-09-21")
        self.assertEqual(self.s.fees("I1")["status"],"Paid")

    def test_concurrent_payment_retries_count_once(self):
        with ThreadPoolExecutor(max_workers=8) as executor:
            list(executor.map(lambda _:self.s.pay("I1","TXN1",20000,"2026-09-20"),range(20)))
        self.assertEqual(self.s.fees("I1")["collected"],Decimal(20000))

    def test_duplicate_payment_different_amount_rejected(self):
        self.s.pay("I1","TXN1",20000,"2026-09-20")
        with self.assertRaises(Conflict): self.s.pay("I1","TXN1",10000,"2026-09-20")

    def test_overpayment_is_visible_credit(self):
        self.s.pay("I1","TXN1",55000,"2026-09-20")
        balance=self.s.fees("I1")
        self.assertEqual((balance["outstanding"],balance["credit"],balance["status"]),(0,5000,"Credit"))

    def test_void_keeps_audit_history_and_reconciles(self):
        self.s.pay("I1","TXN1",20000,"2026-09-20")
        with self.assertRaises(Forbidden): self.s.void("TXN1","Wrong invoice")
        self.s.void("TXN1","Wrong invoice",admin=True)
        self.assertEqual(self.s.fees("I1")["collected"],0)
        self.assertEqual(self.s.db.execute("SELECT COUNT(*) FROM payments").fetchone()[0],1)
        with self.assertRaises(Conflict): self.s.pay("I1","TXN1",20000,"2026-09-20")

    def test_invalid_money_inputs_rejected(self):
        for v in ["NaN","Infinity","-1","1.001","1e999","not-a-number"]:
            with self.subTest(v=v),self.assertRaises(RuleError): money(v)

    def test_zero_payment_rejected(self):
        with self.assertRaises(RuleError): self.s.pay("I1","TXN1",0,"2026-09-20")

    def test_daily_followup_is_deduplicated(self):
        self.assertEqual(self.s.overdue(),1)
        self.assertEqual(self.s.overdue(),0)

    def test_paid_invoice_not_chased(self):
        self.s.pay("I1","TXN1",50000,"2026-09-20")
        self.assertEqual(self.s.overdue(),0)

    def test_due_today_is_not_overdue(self):
        self.s.db.execute("UPDATE invoices SET due='2026-09-22'")
        self.assertEqual(self.s.overdue(),0)

if __name__=="__main__": unittest.main()
