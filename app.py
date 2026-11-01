# Apex Gym OS — single-gym MVP with persistent SQLite storage
# Install: pip install -r requirements.txt
# Run: streamlit run app.py
# First launch creates a local SQLite database and a setup screen for the owner account.

import streamlit as st
import sqlite3
import hashlib
import hmac
import secrets
import csv
import io
from datetime import date, datetime, timedelta
from pathlib import Path
import html

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "apex_gym.db"
APP_NAME = "Apex Gym OS"

st.set_page_config(page_title=APP_NAME, page_icon="🏋️", layout="wide")

# ---------- UI theme ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,[data-testid="stAppViewContainer"]{background:#0E1117;color:#E5E7EB}
[data-testid="stAppViewContainer"] *{font-family:Inter,sans-serif}
[data-testid="stSidebar"]{background:#111827;border-right:1px solid #263244}
.block-container{padding-top:1.4rem;max-width:1500px}
[data-testid="stMetric"]{background:#111827;border:1px solid #263244;padding:15px;border-radius:14px}
[data-testid="stMetricLabel"]{color:#94A3B8!important}
[data-testid="stMetricValue"]{color:#F8FAFC!important;font-weight:800}
.stButton>button{border-radius:10px;font-weight:650}
.stButton>button[kind="primary"]{background:#10B981;color:#06130D;border:1px solid #10B981}
input,textarea{background:#111827!important}
.apex-brand{display:flex;align-items:center;gap:11px;padding:5px 0 18px}
.apex-logo{width:42px;height:42px;border-radius:12px;background:#10B981;color:#052014;font-weight:900;font-size:23px;display:grid;place-items:center}
.apex-title{font-weight:850;font-size:18px;color:#F8FAFC}.apex-sub{font-size:10px;letter-spacing:.15em;color:#94A3B8}
.kicker{font-size:10px;color:#10B981;font-weight:800;letter-spacing:.16em}
.page-title{font-size:31px;font-weight:850;letter-spacing:-.04em;margin:2px 0}
.page-sub{color:#94A3B8;font-size:13px;margin-bottom:20px}
</style>
""", unsafe_allow_html=True)

# ---------- Database ----------
def connect():
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with connect() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS users(
          id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
          password_hash TEXT NOT NULL, salt TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS plans(
          id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL,
          duration_days INTEGER NOT NULL CHECK(duration_days > 0),
          price INTEGER NOT NULL CHECK(price >= 0), active INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS members(
          id INTEGER PRIMARY KEY AUTOINCREMENT, member_code TEXT UNIQUE NOT NULL,
          name TEXT NOT NULL, phone TEXT NOT NULL, email TEXT DEFAULT '',
          plan_id INTEGER REFERENCES plans(id), joined_on TEXT NOT NULL,
          expires_on TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Active',
          notes TEXT DEFAULT '', created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS payments(
          id INTEGER PRIMARY KEY AUTOINCREMENT, receipt_no TEXT UNIQUE NOT NULL,
          member_id INTEGER NOT NULL REFERENCES members(id), amount INTEGER NOT NULL CHECK(amount >= 0),
          method TEXT NOT NULL, paid_on TEXT NOT NULL, period_start TEXT, period_end TEXT,
          note TEXT DEFAULT '', created_by TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS attendance(
          id INTEGER PRIMARY KEY AUTOINCREMENT, member_id INTEGER NOT NULL REFERENCES members(id),
          checkin_at TEXT NOT NULL, checkout_at TEXT, method TEXT NOT NULL DEFAULT 'Manual');
        CREATE TABLE IF NOT EXISTS expenses(
          id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, category TEXT NOT NULL,
          amount INTEGER NOT NULL CHECK(amount >= 0), spent_on TEXT NOT NULL, note TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS trainers(
          id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, phone TEXT DEFAULT '',
          specialty TEXT DEFAULT '', active INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS classes(
          id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
          trainer_id INTEGER REFERENCES trainers(id), day_label TEXT NOT NULL,
          start_time TEXT NOT NULL, capacity INTEGER NOT NULL CHECK(capacity > 0),
          active INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS enrollments(
          id INTEGER PRIMARY KEY AUTOINCREMENT, class_id INTEGER NOT NULL REFERENCES classes(id),
          member_id INTEGER NOT NULL REFERENCES members(id), enrolled_at TEXT NOT NULL,
          UNIQUE(class_id,member_id));
        CREATE TABLE IF NOT EXISTS audit_log(
          id INTEGER PRIMARY KEY AUTOINCREMENT, actor TEXT NOT NULL, action TEXT NOT NULL,
          entity TEXT NOT NULL, entity_id TEXT NOT NULL, created_at TEXT NOT NULL);
        """)
        if con.execute("SELECT COUNT(*) FROM plans").fetchone()[0] == 0:
            con.executemany("INSERT INTO plans(name,duration_days,price) VALUES(?,?,?)",
                            [("Monthly",30,1800),("Quarterly",90,4800),("Annual",365,16000)])

def audit(actor, action, entity, entity_id):
    with connect() as con:
        con.execute("INSERT INTO audit_log(actor,action,entity,entity_id,created_at) VALUES(?,?,?,?,?)",
                   (actor,action,entity,str(entity_id),datetime.now().isoformat(timespec="seconds")))

def setting(key):
    with connect() as con:
        row = con.execute("SELECT value FROM settings WHERE key=?",(key,)).fetchone()
        return row["value"] if row else None

def set_setting(key, value):
    with connect() as con:
        con.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(key,str(value)))

def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 310000).hex()
    return digest, salt

def verify_password(password, salt, expected):
    actual, _ = hash_password(password, salt)
    return hmac.compare_digest(actual, expected)

def money(n):
    return f"₹{int(n):,}"

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def today_iso():
    return date.today().isoformat()

def member_code(next_id):
    return f"APX-{next_id:05d}"

def query(sql, params=()):
    with connect() as con:
        return con.execute(sql, params).fetchall()

def execute(sql, params=()):
    with connect() as con:
        cur = con.execute(sql, params)
        return cur.lastrowid

def header(kicker, title, subtitle):
    st.markdown(f'<div class="kicker">{kicker}</div><div class="page-title">{title}</div><div class="page-sub">{subtitle}</div>',unsafe_allow_html=True)

def setup_required():
    return query("SELECT COUNT(*) AS n FROM users")[0]["n"] == 0

init_db()

# ---------- First-run owner setup ----------
if setup_required():
    st.markdown('<div class="apex-brand"><div class="apex-logo">A</div><div><div class="apex-title">APEX GYM OS</div><div class="apex-sub">SINGLE GYM WORKSPACE</div></div></div>',unsafe_allow_html=True)
    st.title("Create your gym owner account")
    st.info("First launch only. Create the owner login before using the application. Keep your password safe.")
    with st.form("owner_setup"):
        username = st.text_input("Owner username", value="owner").strip().lower()
        password = st.text_input("Password", type="password")
        confirm = st.text_input("Confirm password", type="password")
        gym_name = st.text_input("Gym name", value="Apex Fitness")
        submitted = st.form_submit_button("Create owner account", type="primary")
    if submitted:
        if len(username) < 3 or not username.replace("_","").isalnum():
            st.error("Username must be at least 3 characters and use letters, numbers, or underscore.")
        elif len(password) < 12:
            st.error("Use a password with at least 12 characters.")
        elif password != confirm:
            st.error("Passwords do not match.")
        elif not gym_name.strip():
            st.error("Gym name is required.")
        else:
            digest, salt = hash_password(password)
            execute("INSERT INTO users(username,password_hash,salt,created_at) VALUES(?,?,?,?)",(username,digest,salt,now_iso()))
            set_setting("gym_name",gym_name.strip())
            audit(username,"created owner account","user",username)
            st.success("Owner account created. Sign in to continue.")
            st.session_state.pop("authenticated",None)
            st.rerun()
    st.stop()

# ---------- Login ----------
if not st.session_state.get("authenticated"):
    st.markdown('<div class="apex-brand"><div class="apex-logo">A</div><div><div class="apex-title">APEX GYM OS</div><div class="apex-sub">GYM OPERATIONS</div></div></div>',unsafe_allow_html=True)
    st.title("Owner sign in")
    with st.form("login"):
        username = st.text_input("Username").strip().lower()
        password = st.text_input("Password",type="password")
        submitted = st.form_submit_button("Sign in",type="primary")
    if submitted:
        user = query("SELECT * FROM users WHERE username=?",(username,))
        if user and verify_password(password,user[0]["salt"],user[0]["password_hash"]):
            st.session_state.authenticated = True
            st.session_state.username = username
            st.rerun()
        else:
            st.error("Invalid username or password.")
    st.caption("This is a single-gym MVP. Use HTTPS and private hosting before entering real member data.")
    st.stop()

actor = st.session_state.username
gym_name = setting("gym_name") or "Apex Fitness"

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown(f'<div class="apex-brand"><div class="apex-logo">A</div><div><div class="apex-title">APEX GYM OS</div><div class="apex-sub">{html.escape(gym_name.upper())}</div></div></div>',unsafe_allow_html=True)
    page = st.radio("Navigation",["Dashboard","Members","Payments","Attendance","Plans & Trainers","Expenses","Settings"])
    st.divider()
    st.markdown("**Quick check-in**")
    search_member = st.text_input("Member code / phone",placeholder="APX-00001 or phone",key="quick_lookup")
    if st.button("Check in",type="primary",use_container_width=True):
        m = query("SELECT id,member_code,name,status,expires_on FROM members WHERE member_code=? OR phone=? LIMIT 1",(search_member.strip(),search_member.strip()))
        if not m:
            st.error("Member not found.")
        elif m[0]["status"] != "Active" or m[0]["expires_on"] < today_iso():
            st.warning("Membership is not active. Renew before check-in.")
        else:
            execute("INSERT INTO attendance(member_id,checkin_at,method) VALUES(?,?,?)",(m[0]["id"],now_iso(),"Sidebar"))
            audit(actor,"check-in","member",m[0]["id"])
            st.success(f'{m[0]["name"]} checked in')
            st.rerun()
    st.divider()
    st.caption(f"Signed in as **{actor}**")
    if st.button("Sign out",use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

# ---------- Dashboard ----------
if page == "Dashboard":
    header("LIVE OPERATIONS","Gym dashboard","Real metrics calculated from your local SQLite records.")
    active = query("SELECT COUNT(*) n FROM members WHERE status='Active' AND expires_on>=?",(today_iso(),))[0]["n"]
    overdue = query("SELECT COUNT(*) n FROM members WHERE status='Active' AND expires_on<?",(today_iso(),))[0]["n"]
    month_start = date.today().replace(day=1).isoformat()
    collected = query("SELECT COALESCE(SUM(amount),0) n FROM payments WHERE paid_on>=?",(month_start,))[0]["n"]
    visits = query("SELECT COUNT(*) n FROM attendance WHERE date(checkin_at)=?",(today_iso(),))[0]["n"]
    dues = query("""SELECT COUNT(*) n FROM members m WHERE m.status='Active' AND m.expires_on BETWEEN ? AND ?""",
                 (today_iso(),(date.today()+timedelta(days=7)).isoformat()))[0]["n"]
    c1,c2,c3,c4,c5=st.columns(5)
    c1.metric("Active members",active)
    c2.metric("Collected this month",money(collected))
    c3.metric("Expired memberships",overdue)
    c4.metric("Today's check-ins",visits)
    c5.metric("Renewals in 7 days",dues)
    left,right=st.columns(2)
    with left:
        st.subheader("Collections · last 6 months")
        rows=query("""SELECT substr(paid_on,1,7) month, SUM(amount) amount FROM payments
                     WHERE paid_on>=date('now','-5 months','start of month') GROUP BY substr(paid_on,1,7) ORDER BY month""")
        df=pd.DataFrame([dict(r) for r in rows])
        if not df.empty:
            st.bar_chart(df.set_index("month"),height=280)
        else: st.info("No payment history yet. Record a payment to start your real reports.")
    with right:
        st.subheader("Attendance · last 14 days")
        rows=query("""SELECT date(checkin_at) day,COUNT(*) visits FROM attendance
                     WHERE checkin_at>=datetime('now','-13 days') GROUP BY date(checkin_at) ORDER BY day""")
        df=pd.DataFrame([dict(r) for r in rows])
        if not df.empty: st.line_chart(df.set_index("day"),height=280)
        else: st.info("No attendance yet. Use quick check-in.")
    st.subheader("Renewals coming up")
    rows=query("""SELECT member_code,name,phone,expires_on FROM members
                  WHERE status='Active' AND expires_on BETWEEN ? AND ? ORDER BY expires_on LIMIT 10""",
               (today_iso(),(date.today()+timedelta(days=14)).isoformat()))
    if rows: st.dataframe(pd.DataFrame([dict(r) for r in rows]),use_container_width=True,hide_index=True)
    else: st.success("No renewals due in the next 14 days.")

# ---------- Members ----------
elif page=="Members":
    header("MEMBER RECORDS","Members","Create, find, update, and deactivate real member records.")
    tab1,tab2,tab3=st.tabs(["Directory","Register member","Member profile"])
    with tab1:
        q=st.text_input("Search by name, code, or phone")
        status=st.selectbox("Status",["All","Active","Inactive"])
        sql="SELECT m.member_code,m.name,m.phone,m.email,p.name plan,m.joined_on,m.expires_on,m.status FROM members m LEFT JOIN plans p ON p.id=m.plan_id WHERE 1=1"
        params=[]
        if status!="All": sql+=" AND m.status=?";params.append(status)
        if q: sql+=" AND (m.name LIKE ? OR m.member_code LIKE ? OR m.phone LIKE ?)";params += [f"%{q}%"]*3
        sql+=" ORDER BY m.id DESC"
        rows=query(sql,params)
        if rows: st.dataframe(pd.DataFrame([dict(r) for r in rows]),use_container_width=True,hide_index=True)
        else: st.info("No matching members.")
        st.caption(f"{len(rows)} result(s)")
    with tab2:
        plans=query("SELECT id,name,duration_days,price FROM plans WHERE active=1 ORDER BY price")
        with st.form("register"):
            name=st.text_input("Full name *")
            phone=st.text_input("Phone *")
            email=st.text_input("Email (optional)")
            plan_choice=st.selectbox("Plan",plans,format_func=lambda p:f'{p["name"]} · {money(p["price"])} / {p["duration_days"]} days')
            joined=st.date_input("Start date",date.today())
            notes=st.text_area("Notes (optional)")
            save=st.form_submit_button("Register member",type="primary")
        if save:
            phone_clean="".join(x for x in phone if x.isdigit() or x=="+")
            if not name.strip() or len(phone_clean)<10: st.error("Name and valid phone (10+ digits) are required.")
            elif query("SELECT id FROM members WHERE phone=?",(phone_clean,)): st.error("Phone already exists.")
            else:
                with connect() as con:
                    cur=con.execute("INSERT INTO members(member_code,name,phone,email,plan_id,joined_on,expires_on,status,notes,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                       ("TEMP",name.strip(),phone_clean,email.strip(),plan_choice["id"],joined.isoformat(),
                        (joined+timedelta(days=plan_choice["duration_days"])).isoformat(),"Active",notes.strip(),now_iso()))
                    mid=cur.lastrowid; code=member_code(mid)
                    con.execute("UPDATE members SET member_code=? WHERE id=?",(code,mid))
                audit(actor,"registered member","member",mid)
                st.success(f"Member registered: {code}")
                st.rerun()
    with tab3:
        members=query("SELECT id,member_code,name,phone FROM members ORDER BY id DESC")
        if members:
            choice=st.selectbox("Choose member",members,format_func=lambda m:f'{m["member_code"]} · {m["name"]}')
            m=query("""SELECT m.*,p.name plan_name,p.duration_days,p.price plan_price FROM members m LEFT JOIN plans p ON p.id=m.plan_id WHERE m.id=?""",(choice["id"],))[0]
            a,b,c=st.columns(3);a.metric("Member ID",m["member_code"]);b.metric("Plan",m["plan_name"] or "—");c.metric("Expires",m["expires_on"])
            st.write(f"**{m['name']}** · {m['phone']} · {m['email'] or 'No email'}")
            st.caption(f"Joined {m['joined_on']} · Status: {m['status']}")
            with st.expander("Edit profile"):
                with st.form(f"edit_{m['id']}"):
                    new_name=st.text_input("Name",m["name"]);new_phone=st.text_input("Phone",m["phone"])
                    new_email=st.text_input("Email",m["email"]);new_notes=st.text_area("Notes",m["notes"])
                    active=st.selectbox("Status",["Active","Inactive"],index=0 if m["status"]=="Active" else 1)
                    update=st.form_submit_button("Save changes")
                if update:
                    if not new_name.strip() or len("".join(ch for ch in new_phone if ch.isdigit()))<10: st.error("Name and valid phone required.")
                    else:
                        execute("UPDATE members SET name=?,phone=?,email=?,notes=?,status=? WHERE id=?",
                                (new_name.strip(),new_phone.strip(),new_email.strip(),new_notes.strip(),active,m["id"]))
                        audit(actor,"updated member","member",m["id"]);st.success("Saved");st.rerun()
            st.subheader("Payment history")
            pays=query("SELECT receipt_no,amount,method,paid_on,period_start,period_end FROM payments WHERE member_id=? ORDER BY id DESC",(m["id"],))
            if pays: st.dataframe(pd.DataFrame([dict(p) for p in pays]),use_container_width=True,hide_index=True)
            else: st.info("No recorded payments.")
            st.subheader("Attendance history")
            ats=query("SELECT checkin_at,checkout_at,method FROM attendance WHERE member_id=? ORDER BY id DESC LIMIT 20",(m["id"],))
            if ats: st.dataframe(pd.DataFrame([dict(x) for x in ats]),use_container_width=True,hide_index=True)
            else: st.info("No attendance recorded.")

# ---------- Payments ----------
elif page=="Payments":
    header("PAYMENTS","Payments & renewals","Record money received; each receipt is saved in the database.")
    t1,t2,t3=st.tabs(["Record payment","Payment ledger","Renew membership"])
    members=query("SELECT id,member_code,name,phone,plan_id,expires_on FROM members ORDER BY name")
    plans=query("SELECT id,name,duration_days,price FROM plans WHERE active=1 ORDER BY price")
    with t1:
        if members:
            with st.form("payment_form"):
                m=st.selectbox("Member",members,format_func=lambda x:f'{x["member_code"]} · {x["name"]}')
                amount=st.number_input("Amount received (₹)",min_value=0,step=100,value=1800)
                method=st.selectbox("Payment method",["Cash","UPI","Card","Bank transfer","Other"])
                paid_on=st.date_input("Payment date",date.today())
                note=st.text_input("Reference / note")
                submit=st.form_submit_button("Save payment & receipt",type="primary")
            if submit:
                receipt=f"APX-R-{datetime.now().strftime('%y%m%d')}-{secrets.token_hex(3).upper()}"
                execute("INSERT INTO payments(receipt_no,member_id,amount,method,paid_on,note,created_by) VALUES(?,?,?,?,?,?,?)",
                        (receipt,m["id"],int(amount),method,paid_on.isoformat(),note.strip(),actor))
                audit(actor,"recorded payment","payment",receipt)
                st.success(f"Payment saved. Receipt: {receipt}")
                st.rerun()
        else: st.warning("Register a member first.")
    with t2:
        rows=query("""SELECT p.receipt_no,m.member_code,m.name,p.amount,p.method,p.paid_on,p.note
                     FROM payments p JOIN members m ON m.id=p.member_id ORDER BY p.id DESC""")
        if rows:
            df=pd.DataFrame([dict(r) for r in rows]);st.dataframe(df,use_container_width=True,hide_index=True)
            st.download_button("Export payment ledger CSV",df.to_csv(index=False).encode(),"apex_payments.csv","text/csv")
        else: st.info("No payments recorded.")
    with t3:
        if members and plans:
            member=st.selectbox("Member to renew",members,format_func=lambda x:f'{x["member_code"]} · {x["name"]}',key="renew_member")
            plan=st.selectbox("Renewal plan",plans,format_func=lambda x:f'{x["name"]} · {money(x["price"])}')
            start=st.date_input("Renewal start",date.fromisoformat(member["expires_on"]) if member["expires_on"]>=today_iso() else date.today())
            if st.button("Apply renewal",type="primary"):
                end=start+timedelta(days=plan["duration_days"])
                execute("UPDATE members SET plan_id=?,joined_on=CASE WHEN joined_on IS NULL THEN ? ELSE joined_on END,expires_on=?,status='Active' WHERE id=?",
                        (plan["id"],start.isoformat(),end.isoformat(),member["id"]))
                audit(actor,"renewed membership","member",member["id"])
                st.success(f"Membership renewed through {end.isoformat()}. Record payment separately in Record payment.")
                st.rerun()

# ---------- Attendance ----------
elif page=="Attendance":
    header("CHECK-IN","Attendance","Check members in and out, then review or export attendance.")
    t1,t2=st.tabs(["Check-in / check-out","Attendance log"])
    with t1:
        members=query("SELECT id,member_code,name,phone,status,expires_on FROM members ORDER BY name")
        if members:
            m=st.selectbox("Member",members,format_func=lambda x:f'{x["member_code"]} · {x["name"]}')
            if st.button("Check in",type="primary"):
                if m["status"]!="Active" or m["expires_on"]<today_iso(): st.error("Membership expired or inactive. Renew first.")
                else:
                    execute("INSERT INTO attendance(member_id,checkin_at,method) VALUES(?,?,?)",(m["id"],now_iso(),"Manual"))
                    audit(actor,"check-in","member",m["id"]);st.success("Check-in recorded");st.rerun()
            open_visit=query("SELECT id,checkin_at FROM attendance WHERE member_id=? AND checkout_at IS NULL ORDER BY id DESC LIMIT 1",(m["id"],))
            if open_visit:
                st.caption(f'Open visit since {open_visit[0]["checkin_at"]}')
                if st.button("Check out"):
                    execute("UPDATE attendance SET checkout_at=? WHERE id=?",(now_iso(),open_visit[0]["id"]))
                    audit(actor,"check-out","attendance",open_visit[0]["id"]);st.success("Check-out recorded");st.rerun()
            else: st.caption("No open visit for this member.")
    with t2:
        rows=query("""SELECT a.id,m.member_code,m.name,a.checkin_at,a.checkout_at,a.method FROM attendance a
                     JOIN members m ON m.id=a.member_id ORDER BY a.id DESC LIMIT 500""")
        if rows:
            df=pd.DataFrame([dict(r) for r in rows]);st.dataframe(df,use_container_width=True,hide_index=True)
            st.download_button("Export attendance CSV",df.to_csv(index=False).encode(),"apex_attendance.csv","text/csv")
        else: st.info("No attendance records.")

# ---------- Plans and trainers ----------
elif page=="Plans & Trainers":
    header("SETUP","Plans & trainers","Maintain the membership plans and instructor directory used by the gym.")
    tp,tt=st.tabs(["Membership plans","Trainers"])
    with tp:
        rows=query("SELECT * FROM plans ORDER BY active DESC,price")
        if rows: st.dataframe(pd.DataFrame([dict(r) for r in rows]),use_container_width=True,hide_index=True)
        with st.form("plan_add"):
            st.subheader("Add plan")
            name=st.text_input("Plan name");days=st.number_input("Duration in days",min_value=1,max_value=3650,value=30);price=st.number_input("Price ₹",min_value=0,step=100)
            add=st.form_submit_button("Save plan")
        if add:
            try:
                execute("INSERT INTO plans(name,duration_days,price) VALUES(?,?,?)",(name.strip(),int(days),int(price)))
                audit(actor,"created plan","plan",name);st.success("Plan added");st.rerun()
            except sqlite3.IntegrityError: st.error("Plan name already exists.")
        if rows:
            plan=st.selectbox("Plan to deactivate",rows,format_func=lambda x:f'{x["name"]} · {money(x["price"])}')
            if st.button("Deactivate selected plan"):
                execute("UPDATE plans SET active=0 WHERE id=?",(plan["id"],));audit(actor,"deactivated plan","plan",plan["id"]);st.rerun()
    with tt:
        rows=query("SELECT * FROM trainers ORDER BY active DESC,name")
        if rows: st.dataframe(pd.DataFrame([dict(r) for r in rows]),use_container_width=True,hide_index=True)
        with st.form("trainer_add"):
            name=st.text_input("Trainer name");phone=st.text_input("Phone");specialty=st.text_input("Specialty")
            add=st.form_submit_button("Add trainer")
        if add:
            if not name.strip(): st.error("Trainer name required.")
            else:
                tid=execute("INSERT INTO trainers(name,phone,specialty) VALUES(?,?,?)",(name.strip(),phone.strip(),specialty.strip()))
                audit(actor,"created trainer","trainer",tid);st.success("Trainer added");st.rerun()

# ---------- Expenses ----------
elif page=="Expenses":
    header("COST CONTROL","Expenses","Record actual operating costs to calculate net cash flow.")
    with st.form("expense_add"):
        title=st.text_input("Expense description")
        category=st.selectbox("Category",["Rent","Utilities","Payroll","Equipment","Maintenance","Marketing","Other"])
        amount=st.number_input("Amount ₹",min_value=0,step=100)
        spent=date.today()
        spent=st.date_input("Date",spent)
        note=st.text_input("Notes")
        add=st.form_submit_button("Record expense",type="primary")
    if add:
        if not title.strip(): st.error("Description required.")
        else:
            eid=execute("INSERT INTO expenses(title,category,amount,spent_on,note) VALUES(?,?,?,?,?)",(title.strip(),category,int(amount),spent.isoformat(),note.strip()))
            audit(actor,"recorded expense","expense",eid);st.success("Expense recorded");st.rerun()
    month_start=date.today().replace(day=1).isoformat()
    totals=query("SELECT COALESCE(SUM(amount),0) n FROM expenses WHERE spent_on>=?",(month_start,))[0]["n"]
    received=query("SELECT COALESCE(SUM(amount),0) n FROM payments WHERE paid_on>=?",(month_start,))[0]["n"]
    a,b,c=st.columns(3);a.metric("Expenses this month",money(totals));b.metric("Collections this month",money(received));c.metric("Net cash flow",money(received-totals))
    rows=query("SELECT id,title,category,amount,spent_on,note FROM expenses ORDER BY spent_on DESC,id DESC")
    if rows:
        df=pd.DataFrame([dict(r) for r in rows]);st.dataframe(df,use_container_width=True,hide_index=True)
        st.download_button("Export expenses CSV",df.to_csv(index=False).encode(),"apex_expenses.csv","text/csv")
    else: st.info("No expenses recorded.")

# ---------- Settings / backup ----------
elif page=="Settings":
    header("ADMIN","Settings & backup","Manage gym identity and export a database backup.")
    current=setting("gym_name") or "Apex Fitness"
    with st.form("gym_settings"):
        name=st.text_input("Gym display name",current)
        save=st.form_submit_button("Save settings",type="primary")
    if save and name.strip():
        set_setting("gym_name",name.strip());audit(actor,"updated gym name","setting","gym_name");st.success("Gym name updated");st.rerun()
    st.subheader("Database backup")
    st.warning("The backup contains member names, phone numbers, payment records, and attendance. Store it securely.")
    if st.button("Prepare SQLite backup"):
        with connect() as source:
            target=sqlite3.connect(":memory:")
            source.backup(target)
            data=target.serialize()
            target.close()
        st.download_button("Download database backup",data,"apex_gym_backup.sqlite","application/octet-stream")
    st.subheader("Security notes")
    st.markdown("""
    - This MVP uses a local SQLite file and a single owner account.
    - Passwords are stored as PBKDF2-SHA256 hashes with random salts.
    - Do not commit `apex_gym.db` to GitHub.
    - Before public deployment, use HTTPS, private hosting, regular backups, and a production database with access controls.
    - This application does not process online payments or send WhatsApp messages.
    """)

st.markdown("<hr><span style='color:#94A3B8;font-size:11px'>APEX GYM OS · Single-gym MVP · SQLite persistent storage</span>",unsafe_allow_html=True)
