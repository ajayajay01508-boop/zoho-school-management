"""Executable business-rule reference, NOT a Zoho or Deluge runtime.

SQLite transactions let tests exercise idempotency and race conditions locally.
Passing these tests does not prove that the corresponding Zoho setup works.
"""
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from hashlib import sha256
from threading import RLock
import json
import sqlite3

class RuleError(ValueError): pass
class Forbidden(RuleError): pass
class Conflict(RuleError): pass

def email_key(email):
    return sha256(email.strip().lower().encode()).hexdigest()

def money(value):
    try: amount=Decimal(str(value))
    except InvalidOperation: raise RuleError("Invalid amount") from None
    if not amount.is_finite() or amount < 0 or amount > Decimal("9999999999.99"):
        raise RuleError("Invalid amount")
    if amount != amount.quantize(Decimal("0.01")): raise RuleError("At most two decimal places")
    return amount

def percent(n,d):
    return None if d==0 else (Decimal(n)*100/Decimal(d)).quantize(Decimal("0.01"),rounding=ROUND_HALF_UP)

class School:
    def __init__(self, today=date(2026,9,22)):
        self.today=today
        self.db=sqlite3.connect(":memory:",check_same_thread=False)
        self.db.row_factory=sqlite3.Row
        self.lock=RLock()
        self.db.executescript("""
          PRAGMA foreign_keys=ON;
          CREATE TABLE students(id INTEGER PRIMARY KEY AUTOINCREMENT, lead TEXT UNIQUE, name TEXT);
          CREATE TABLE enrollments(id INTEGER PRIMARY KEY, student INTEGER REFERENCES students,
            year TEXT, section TEXT, start TEXT, end TEXT, current INTEGER,
            UNIQUE(student,year));
          CREATE UNIQUE INDEX one_current ON enrollments(student) WHERE current=1;
          CREATE TABLE guardians(email_hash TEXT PRIMARY KEY, verified INTEGER, enabled INTEGER);
          CREATE TABLE grants(email_hash TEXT REFERENCES guardians,student INTEGER REFERENCES students,
            enabled INTEGER,PRIMARY KEY(email_hash,student));
          CREATE TABLE days(section TEXT,day TEXT,PRIMARY KEY(section,day));
          CREATE TABLE attendance(enrollment INTEGER REFERENCES enrollments, day TEXT, status TEXT,
            PRIMARY KEY(enrollment,day));
          CREATE TABLE papers(id TEXT PRIMARY KEY,section TEXT,day TEXT,maximum TEXT,passing TEXT,published INTEGER);
          CREATE TABLE results(enrollment INTEGER REFERENCES enrollments,paper TEXT REFERENCES papers,
            marks TEXT,absent INTEGER,maximum TEXT,passing TEXT,PRIMARY KEY(enrollment,paper));
          CREATE TABLE invoices(id TEXT PRIMARY KEY,enrollment INTEGER REFERENCES enrollments,total TEXT,due TEXT);
          CREATE TABLE payments(reference TEXT PRIMARY KEY,invoice TEXT REFERENCES invoices,
            amount TEXT,day TEXT,state TEXT,void_reason TEXT);
          CREATE TABLE followups(invoice TEXT REFERENCES invoices,day TEXT,balance TEXT,
            PRIMARY KEY(invoice,day));
        """)

    def add_guardian(self,email,verified=True,enabled=True):
        with self.lock,self.db:
            self.db.execute("INSERT OR REPLACE INTO guardians VALUES(?,?,?)",(email_key(email),verified,enabled))

    def admit(self,lead,name,year,section,start,end,parent,approved=True):
        if not approved: raise RuleError("Admission not approved")
        if date.fromisoformat(start)>date.fromisoformat(end): raise RuleError("Invalid enrollment dates")
        with self.lock,self.db:
            guardian=self.db.execute("SELECT * FROM guardians WHERE email_hash=?",(email_key(parent),)).fetchone()
            if not guardian or not guardian["verified"]: raise Forbidden("Guardian not verified")
            student=self.db.execute("SELECT * FROM students WHERE lead=?",(lead,)).fetchone()
            if student and student["name"]!=name: raise Conflict("Admission retry differs")
            if not student:
                sid=self.db.execute("INSERT INTO students(lead,name) VALUES(?,?)",(lead,name)).lastrowid
            else: sid=student["id"]
            existing=self.db.execute("SELECT * FROM enrollments WHERE student=? AND year=?",(sid,year)).fetchone()
            if existing:
                if (existing["section"],existing["start"],existing["end"])!=(section,start,end): raise Conflict("Enrollment retry differs")
                eid=existing["id"]
            else:
                eid=self.db.execute("INSERT INTO enrollments(student,year,section,start,end,current) VALUES(?,?,?,?,?,1)",(sid,year,section,start,end)).lastrowid
            self.db.execute("INSERT OR IGNORE INTO grants VALUES(?,?,1)",(email_key(parent),sid))
            return sid,eid

    def promote(self,sid,year,section,start,end):
        if date.fromisoformat(start)>date.fromisoformat(end): raise RuleError("Invalid dates")
        with self.lock,self.db:
            existing=self.db.execute("SELECT * FROM enrollments WHERE student=? AND year=?",(sid,year)).fetchone()
            if existing:
                if (existing["section"],existing["start"],existing["end"])!=(section,start,end): raise Conflict("Promotion differs")
                return existing["id"]
            previous=self.db.execute("SELECT * FROM enrollments WHERE student=? AND current=1",(sid,)).fetchone()
            if not previous or start<=previous["end"]: raise RuleError("Overlapping enrollment")
            self.db.execute("UPDATE enrollments SET current=0 WHERE id=?",(previous["id"],))
            return self.db.execute("INSERT INTO enrollments(student,year,section,start,end,current) VALUES(?,?,?,?,?,1)",(sid,year,section,start,end)).lastrowid

    def allow(self,email,sid,eid=None):
        row=self.db.execute("SELECT 1 FROM guardians g JOIN grants a USING(email_hash) WHERE g.email_hash=? AND g.verified=1 AND g.enabled=1 AND a.enabled=1 AND a.student=?",(email_key(email),sid)).fetchone()
        if not row: raise Forbidden("No access")
        if eid is not None and not self.db.execute("SELECT 1 FROM enrollments WHERE id=? AND student=?",(eid,sid)).fetchone():
            raise Forbidden("No access")
        return True

    def school_day(self,section,day):
        date.fromisoformat(day)
        with self.db: self.db.execute("INSERT OR IGNORE INTO days VALUES(?,?)",(section,day))

    def mark(self,eid,day,status):
        if status not in {"Present","Absent","Late","Excused"}: raise RuleError("Bad status")
        d=date.fromisoformat(day)
        with self.lock,self.db:
            e=self.db.execute("SELECT * FROM enrollments WHERE id=?",(eid,)).fetchone()
            if not e or not e["start"]<=day<=e["end"] or d>self.today: raise RuleError("Outside enrollment")
            if not self.db.execute("SELECT 1 FROM days WHERE section=? AND day=?",(e["section"],day)).fetchone(): raise RuleError("Not school day")
            prior=self.db.execute("SELECT status FROM attendance WHERE enrollment=? AND day=?",(eid,day)).fetchone()
            if prior and prior[0]!=status: raise Conflict("Attendance retry differs")
            self.db.execute("INSERT OR IGNORE INTO attendance VALUES(?,?,?)",(eid,day,status))

    def attendance(self,eid):
        e=self.db.execute("SELECT * FROM enrollments WHERE id=?",(eid,)).fetchone()
        rows=self.db.execute("SELECT status FROM attendance WHERE enrollment=?",(eid,)).fetchall()
        statuses=[r[0] for r in rows]
        expected=self.db.execute("SELECT COUNT(*) FROM days WHERE section=? AND day BETWEEN ? AND ?",(e["section"],e["start"],min(e["end"],self.today.isoformat()))).fetchone()[0]
        return dict(percent=percent(sum(s in {"Present","Late"} for s in statuses),sum(s!="Excused" for s in statuses)),marked=len(rows),unmarked=expected-len(rows))

    def paper(self,pid,section,day,maximum,passing,published=False):
        maximum,passing=money(maximum),money(passing)
        date.fromisoformat(day)
        if maximum<=0 or passing>maximum: raise RuleError("Invalid marks scale")
        with self.db: self.db.execute("INSERT INTO papers VALUES(?,?,?,?,?,?)",(pid,section,day,str(maximum),str(passing),published))

    def result(self,eid,pid,marks,absent=False):
        marks=money(marks)
        with self.lock,self.db:
            p=self.db.execute("SELECT * FROM papers WHERE id=?",(pid,)).fetchone()
            e=self.db.execute("SELECT * FROM enrollments WHERE id=?",(eid,)).fetchone()
            if not p or not e or p["section"]!=e["section"]: raise RuleError("Section mismatch")
            if p["published"]: raise RuleError("Published exam locked")
            if not e["start"]<=p["day"]<=min(e["end"],self.today.isoformat()): raise RuleError("Exam outside enrollment")
            if marks>Decimal(p["maximum"]) or (absent and marks!=0): raise RuleError("Invalid marks")
            prior=self.db.execute("SELECT * FROM results WHERE enrollment=? AND paper=?",(eid,pid)).fetchone()
            if prior and (Decimal(prior["marks"])!=marks or bool(prior["absent"])!=absent): raise Conflict("Result retry differs")
            self.db.execute("INSERT OR IGNORE INTO results VALUES(?,?,?,?,?,?)",(eid,pid,str(marks),absent,p["maximum"],p["passing"]))

    def performance(self,eid,published_only=False):
        rows=self.db.execute("SELECT r.*,p.published FROM results r JOIN papers p ON p.id=r.paper WHERE enrollment=?",(eid,)).fetchall()
        if published_only: rows=[r for r in rows if r["published"]]
        total=sum((Decimal(r["marks"]) for r in rows),Decimal(0))
        maximum=sum((Decimal(r["maximum"]) for r in rows),Decimal(0))
        return dict(marks=total,maximum=maximum,percent=percent(total,maximum),papers=len(rows))

    def invoice(self,iid,eid,total,due):
        total=money(total); date.fromisoformat(due)
        with self.db: self.db.execute("INSERT INTO invoices VALUES(?,?,?,?)",(iid,eid,str(total),due))

    def pay(self,iid,reference,amount,day):
        amount=money(amount)
        if amount<=0 or date.fromisoformat(day)>self.today: raise RuleError("Invalid payment")
        reference=reference.upper()
        with self.lock,self.db:
            prior=self.db.execute("SELECT * FROM payments WHERE reference=?",(reference,)).fetchone()
            if prior:
                if (prior["invoice"],Decimal(prior["amount"]),prior["day"],prior["state"])!=(iid,amount,day,"Posted"): raise Conflict("Payment retry differs")
                return
            self.db.execute("INSERT INTO payments VALUES(?,?,?,?,'Posted',NULL)",(reference,iid,str(amount),day))

    def void(self,reference,reason,admin=False):
        if not admin or not reason.strip(): raise Forbidden("Admin and reason required")
        with self.lock,self.db: self.db.execute("UPDATE payments SET state='Void',void_reason=? WHERE reference=?",(reason,reference.upper()))

    def fees(self,iid):
        invoice=self.db.execute("SELECT * FROM invoices WHERE id=?",(iid,)).fetchone()
        total=Decimal(invoice["total"])
        collected=sum((Decimal(r[0]) for r in self.db.execute("SELECT amount FROM payments WHERE invoice=? AND state='Posted'",(iid,))),Decimal(0))
        outstanding=max(Decimal(0),total-collected)
        credit=max(Decimal(0),collected-total)
        status="Credit" if credit else "Paid" if outstanding==0 else "Part Paid" if collected else "Unpaid"
        return dict(total=total,collected=collected,outstanding=outstanding,credit=credit,status=status)

    def overdue(self):
        count=0
        with self.lock,self.db:
            for invoice in self.db.execute("SELECT id FROM invoices WHERE due < ?",(self.today.isoformat(),)).fetchall():
                balance=self.fees(invoice["id"])["outstanding"]
                if balance>0:
                    count+=self.db.execute("INSERT OR IGNORE INTO followups VALUES(?,?,?)",(invoice["id"],self.today.isoformat(),str(balance))).rowcount
        return count

if __name__=="__main__":
    s=School(); s.add_guardian("parent@example.test")
    sid,eid=s.admit("LEAD-DEMO","Demo Student","2026-27","10A","2026-06-01","2027-03-31","parent@example.test")
    s.school_day("10A","2026-09-21"); s.mark(eid,"2026-09-21","Present")
    s.invoice("DEMO-INV",eid,50000,"2026-09-01"); s.pay("DEMO-INV","DEMO-PAY",20000,"2026-09-20")
    print(json.dumps({"runtime":"LOCAL REFERENCE ONLY","student_id":sid,"attendance":s.attendance(eid),"fees":s.fees("DEMO-INV"),"new_followups":s.overdue()},default=str,indent=2))
