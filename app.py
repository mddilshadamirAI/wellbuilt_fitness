# Apex Gym OS — single-file Streamlit gym management application
# Run: pip install streamlit pandas plotly
#      streamlit run app.py

from datetime import date, datetime, timedelta
from html import escape
import random
import uuid

import pandas as pd
import plotly.express as px
import streamlit as st

# ---------------------------------------------------------------------------
# Page configuration and theme
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Apex Gym OS",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="expanded",
)

BG = "#0E1117"
PANEL = "#111827"
PANEL2 = "#151D2B"
BORDER = "#263244"
TEXT = "#E5E7EB"
MUTED = "#94A3B8"
GREEN = "#10B981"
RED = "#EF4444"
AMBER = "#F59E0B"
BLUE = "#60A5FA"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root { color-scheme: dark; }
html, body, [data-testid="stAppViewContainer"] { background: #0E1117; color: #E5E7EB; }
[data-testid="stAppViewContainer"] * { font-family: Inter, sans-serif; }
[data-testid="stSidebar"] { background: #111827; border-right: 1px solid #263244; }
[data-testid="stHeader"] { background: rgba(14,17,23,0.85); }
.block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1500px; }
h1,h2,h3 { letter-spacing: -0.035em; }
h1 { font-weight: 800 !important; }
[data-testid="stMetric"] { background: #111827; border: 1px solid #263244; padding: 16px 18px; border-radius: 16px; }
[data-testid="stMetricLabel"] { color: #94A3B8 !important; font-size: .82rem; }
[data-testid="stMetricValue"] { color: #F8FAFC !important; font-weight: 800; }
[data-testid="stMetricDelta"] { font-size: .78rem; }
div[data-testid="stVerticalBlockBorderWrapper"] { border-color: #263244 !important; border-radius: 16px; }
.stButton > button { border-radius: 10px; font-weight: 650; min-height: 2.55rem; }
.stButton > button[kind="primary"] { background: #10B981; border: 1px solid #10B981; color: #07130F; }
.stButton > button[kind="primary"]:hover { background: #059669; border-color: #059669; }
.stTextInput input, .stNumberInput input, .stDateInput input, .stTimeInput input, .stSelectbox div[data-baseweb="select"] { background: #111827 !important; }
[data-testid="stDataFrame"] { border: 1px solid #263244; border-radius: 12px; overflow: hidden; }
.apex-brand { display:flex; align-items:center; gap:12px; padding: 8px 0 20px; }
.apex-mark { width:44px; height:44px; border-radius:13px; display:flex; align-items:center; justify-content:center; background:linear-gradient(135deg,#10B981,#047857); color:#03150E; font-size:23px; font-weight:900; }
.apex-name { font-size:19px; font-weight:850; color:#F8FAFC; line-height:1.1; }
.apex-sub { color:#94A3B8; font-size:10px; letter-spacing:.15em; margin-top:5px; }
.hero-kicker { color:#10B981; font-size:11px; font-weight:800; letter-spacing:.16em; text-transform:uppercase; }
.page-title { font-size:32px; font-weight:850; margin: 3px 0 4px; }
.page-subtitle { color:#94A3B8; margin-bottom:22px; font-size:13px; }
.panel-title { font-size:15px; font-weight:750; margin-bottom:3px; }
.panel-sub { color:#94A3B8; font-size:12px; margin-bottom:14px; }
.badge { display:inline-block; padding:4px 9px; border-radius:999px; font-size:10px; font-weight:800; letter-spacing:.04em; }
.badge-active { color:#6EE7B7; background:rgba(16,185,129,.13); border:1px solid rgba(16,185,129,.28); }
.badge-expired { color:#FCA5A5; background:rgba(239,68,68,.12); border:1px solid rgba(239,68,68,.28); }
.badge-pending { color:#FCD34D; background:rgba(245,158,11,.12); border:1px solid rgba(245,158,11,.28); }
.badge-neutral { color:#BFDBFE; background:rgba(96,165,250,.12); border:1px solid rgba(96,165,250,.28); }
.small-muted { color:#94A3B8; font-size:12px; }
.sidebar-note { border:1px solid #263244; background:#151D2B; border-radius:12px; padding:12px; color:#94A3B8; font-size:11px; }
hr { border-color:#263244 !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session state — sample data is created once per browser session
# ---------------------------------------------------------------------------
def init_state():
    if "members" not in st.session_state:
        today = date.today()
        sample = [
            ("M-1001", "Aarav Sharma", "9876543210", "Monthly", today + timedelta(days=19), 1800, "Active"),
            ("M-1002", "Priya Singh", "9876543211", "Quarterly", today + timedelta(days=52), 4800, "Active"),
            ("M-1003", "Kabir Khan", "9876543212", "Monthly", today - timedelta(days=5), 1800, "Expired"),
            ("M-1004", "Meera Patel", "9876543213", "Annual", today + timedelta(days=170), 16000, "Active"),
            ("M-1005", "Rohan Verma", "9876543214", "Monthly", today + timedelta(days=2), 1800, "Pending"),
            ("M-1006", "Ananya Das", "9876543215", "Quarterly", today - timedelta(days=12), 4800, "Expired"),
            ("M-1007", "Ishaan Roy", "9876543216", "Monthly", today + timedelta(days=28), 1800, "Active"),
            ("M-1008", "Sana Ali", "9876543217", "Monthly", today + timedelta(days=1), 1800, "Pending"),
            ("M-1009", "Dev Malhotra", "9876543218", "Annual", today + timedelta(days=250), 16000, "Active"),
            ("M-1010", "Nisha Gupta", "9876543219", "Quarterly", today + timedelta(days=10), 4800, "Active"),
        ]
        st.session_state.members = [
            {"id": x[0], "name": x[1], "phone": x[2], "plan": x[3], "expiry": x[4],
             "fee": x[5], "status": x[6], "joined": today - timedelta(days=90+i*8)}
            for i, x in enumerate(sample)
        ]
    if "attendance" not in st.session_state:
        st.session_state.attendance = [
            {"member_id": "M-1001", "name": "Aarav Sharma", "timestamp": datetime.now().replace(hour=6, minute=42, second=11)},
            {"member_id": "M-1004", "name": "Meera Patel", "timestamp": datetime.now().replace(hour=7, minute=5, second=23)},
            {"member_id": "M-1007", "name": "Ishaan Roy", "timestamp": datetime.now().replace(hour=8, minute=18, second=4)},
        ]
    if "classes" not in st.session_state:
        st.session_state.classes = [
            {"id": "CL-01", "name": "Strength & Conditioning", "trainer": "Arjun Mehta", "time": "06:30 AM", "capacity": 18, "enrolled": 14, "day": "Mon–Fri"},
            {"id": "CL-02", "name": "Yoga Flow", "trainer": "Riya Kapoor", "time": "08:00 AM", "capacity": 16, "enrolled": 11, "day": "Mon, Wed, Fri"},
            {"id": "CL-03", "name": "HIIT Burn", "trainer": "Vikram Joshi", "time": "06:00 PM", "capacity": 20, "enrolled": 18, "day": "Tue–Sat"},
            {"id": "CL-04", "name": "Boxing Fundamentals", "trainer": "Sameer Khan", "time": "07:15 PM", "capacity": 12, "enrolled": 7, "day": "Mon, Thu, Sat"},
        ]
    if "payments" not in st.session_state:
        st.session_state.payments = [
            {"id": "PAY-5001", "member_id": "M-1003", "member": "Kabir Khan", "amount": 1800, "due": date.today()-timedelta(days=5), "status": "Overdue"},
            {"id": "PAY-5002", "member_id": "M-1005", "member": "Rohan Verma", "amount": 1800, "due": date.today()+timedelta(days=2), "status": "Pending"},
            {"id": "PAY-5003", "member_id": "M-1006", "member": "Ananya Das", "amount": 4800, "due": date.today()-timedelta(days=12), "status": "Overdue"},
            {"id": "PAY-5004", "member_id": "M-1008", "member": "Sana Ali", "amount": 1800, "due": date.today()+timedelta(days=1), "status": "Pending"},
        ]
    if "expenses" not in st.session_state:
        st.session_state.expenses = 78500
    if "page" not in st.session_state:
        st.session_state.page = "Dashboard"

init_state()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
PLAN_DAYS = {"Monthly": 30, "Quarterly": 90, "Annual": 365}
PLAN_PRICE = {"Monthly": 1800, "Quarterly": 4800, "Annual": 16000}

def next_member_id():
    nums = []
    for m in st.session_state.members:
        try:
            nums.append(int(m["id"].split("-")[-1]))
        except (ValueError, IndexError):
            pass
    return f"M-{max(nums, default=1000)+1}"

def money(value):
    return f"₹{value:,.0f}"

def status_badge(status):
    cls = {"Active": "badge-active", "Expired": "badge-expired", "Pending": "badge-pending",
           "Overdue": "badge-expired", "Paid": "badge-active"}
    return f'<span class="badge {cls.get(status, "badge-neutral")}">{escape(str(status).upper())}</span>'

def page_header(kicker, title, subtitle):
    st.markdown(f'<div class="hero-kicker">{kicker}</div><div class="page-title">{title}</div><div class="page-subtitle">{subtitle}</div>', unsafe_allow_html=True)

def panel_heading(title, subtitle=""):
    st.markdown(f'<div class="panel-title">{title}</div><div class="panel-sub">{subtitle}</div>', unsafe_allow_html=True)

def member_df():
    rows = []
    for m in st.session_state.members:
        rows.append({**m, "expiry": m["expiry"].strftime("%d %b %Y"), "joined": m["joined"].strftime("%d %b %Y")})
    return pd.DataFrame(rows)

def current_active():
    return [m for m in st.session_state.members if m["status"] == "Active" and m["expiry"] >= date.today()]

def mrr():
    return sum(PLAN_PRICE.get(m["plan"], m["fee"]) for m in current_active())

def get_member(member_id):
    return next((m for m in st.session_state.members if m["id"] == member_id), None)

def mark_payment_paid(payment_id):
    payment = next((p for p in st.session_state.payments if p["id"] == payment_id), None)
    if not payment:
        return
    payment["status"] = "Paid"
    member = get_member(payment["member_id"])
    if member:
        member["status"] = "Active"
        member["expiry"] = max(member["expiry"], date.today()) + timedelta(days=PLAN_DAYS.get(member["plan"], 30))
        member["fee"] = payment["amount"]

def invoice_html(member):
    invoice_id = "INV-" + datetime.now().strftime("%y%m%d") + "-" + member["id"].split("-")[-1]
    invoice_date = date.today().strftime("%d %B %Y")
    expiry = member["expiry"].strftime("%d %B %Y")
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>{invoice_id}</title>
<style>body{{font-family:Arial,sans-serif;background:#f3f4f6;padding:32px;color:#111827}}.invoice{{max-width:720px;margin:auto;background:white;padding:40px;border-radius:16px}}header{{display:flex;justify-content:space-between;border-bottom:2px solid #10b981;padding-bottom:20px}}h1{{margin:0;color:#047857}}small{{color:#6b7280}}table{{width:100%;border-collapse:collapse;margin-top:28px}}td,th{{padding:14px;border-bottom:1px solid #e5e7eb;text-align:left}}.total{{text-align:right;font-size:24px;font-weight:bold;margin-top:24px}}.foot{{margin-top:36px;color:#6b7280;font-size:12px}}</style></head>
<body><div class="invoice"><header><div><h1>APEX GYM</h1><small>Membership & Fitness</small></div><div><b>INVOICE</b><br>{invoice_id}<br><small>{invoice_date}</small></div></header>
<p><b>Bill to:</b> {escape(member["name"])}<br><b>Member ID:</b> {escape(member["id"])}<br><b>Phone:</b> {escape(member["phone"])}</p>
<table><tr><th>Description</th><th>Membership</th><th>Expiry</th><th>Amount</th></tr><tr><td>Gym membership</td><td>{escape(member["plan"])}</td><td>{expiry}</td><td>{money(member["fee"])}</td></tr></table>
<div class="total">Total: {money(member["fee"])}</div><div class="foot">Thank you for choosing Apex Gym. This invoice was generated locally by Apex Gym OS.</div></div></body></html>"""

# ---------------------------------------------------------------------------
# Sidebar: branding, quick check-in, and navigation
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("""<div class="apex-brand"><div class="apex-mark">A</div><div><div class="apex-name">APEX GYM OS</div><div class="apex-sub">FITNESS MANAGEMENT</div></div></div>""", unsafe_allow_html=True)
    st.caption("WORKSPACE  /  MAIN")
    pages = ["Dashboard", "Members", "Payments", "Schedule & Trainers", "Attendance"]
    page = st.radio("Navigation", pages, label_visibility="collapsed", key="nav_radio")
    st.session_state.page = page
    st.divider()
    st.markdown("**⚡ Quick check-in**")
    active_members = current_active()
    checkin_options = {f'{m["id"]} · {m["name"]}': m["id"] for m in active_members}
    if checkin_options:
        chosen = st.selectbox("Select member", list(checkin_options.keys()), label_visibility="collapsed", key="quick_member")
        if st.button("＋  Check in member", type="primary", use_container_width=True):
            mid = checkin_options[chosen]
            mem = get_member(mid)
            st.session_state.attendance.insert(0, {"member_id": mid, "name": mem["name"], "timestamp": datetime.now()})
            st.toast(f'{mem["name"]} checked in', icon="✅")
            st.rerun()
    else:
        st.info("No active members available.")
    st.markdown('<div class="sidebar-note">● <b style="color:#10B981">System online</b><br>Local demo workspace · Data resets with a new session.</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
if page == "Dashboard":
    page_header("OVERVIEW", "Good afternoon, manager. 👋", "Here’s what’s happening at your gym today.")
    active_count = len(current_active())
    overdue_count = sum(p["status"] == "Overdue" for p in st.session_state.payments)
    today_visits = sum(a["timestamp"].date() == date.today() for a in st.session_state.attendance)
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Active members", f"{active_count:,}", delta="+8.2% this month")
    c2.metric("Monthly recurring revenue", money(mrr()), delta="+₹12,400")
    c3.metric("Overdue payments", f"{overdue_count}", delta=f"{overdue_count} need follow-up", delta_color="inverse")
    c4.metric("Daily visits", f"{today_visits}", delta="Live attendance")
    st.write("")
    left, right = st.columns([1.45, 1])
    with left:
        with st.container(border=True):
            panel_heading("Revenue vs. expenses", "Monthly performance · INR")
            months = ["May", "Jun", "Jul", "Aug", "Sep", "Oct"]
            revenue = [142000, 156000, 168500, 172000, 184500, max(mrr(), 191000)]
            expenses = [92000, 98500, 105000, 101500, 109000, st.session_state.expenses]
            chart_df = pd.DataFrame({"Month": months, "Revenue": revenue, "Expenses": expenses})
            fig = px.area(chart_df, x="Month", y=["Revenue", "Expenses"], markers=True,
                         color_discrete_sequence=[GREEN, AMBER])
            fig.update_layout(height=310, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor=PANEL,
                            plot_bgcolor=PANEL, font_color=TEXT, legend_title_text="",
                            yaxis=dict(gridcolor=BORDER, tickprefix="₹", zeroline=False),
                            xaxis=dict(gridcolor="rgba(0,0,0,0)", zeroline=False))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with right:
        with st.container(border=True):
            panel_heading("Peak hours occupancy", "Average floor utilization · today")
            hours = ["06 AM", "08 AM", "10 AM", "12 PM", "02 PM", "04 PM", "06 PM", "08 PM"]
            occupancy = [72, 88, 54, 31, 38, 62, 96, 79]
            occ_df = pd.DataFrame({"Hour": hours, "Occupancy": occupancy})
            fig2 = px.bar(occ_df, x="Hour", y="Occupancy", text="Occupancy",
                          color="Occupancy", color_continuous_scale=["#064E3B", GREEN])
            fig2.update_layout(height=310, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor=PANEL,
                              plot_bgcolor=PANEL, font_color=TEXT, coloraxis_showscale=False,
                              yaxis=dict(range=[0,100], ticksuffix="%", gridcolor=BORDER),
                              xaxis=dict(gridcolor="rgba(0,0,0,0)"))
            fig2.update_traces(texttemplate="%{text}%", textposition="outside", cliponaxis=False)
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
    st.write("")
    l,r = st.columns([1.15,1])
    with l:
        with st.container(border=True):
            panel_heading("Recent check-ins", "Latest activity from the gym floor")
            recent = st.session_state.attendance[:5]
            if recent:
                df = pd.DataFrame([{"Member": a["name"], "Member ID": a["member_id"],
                                   "Check-in": a["timestamp"].strftime("%d %b · %I:%M:%S %p")} for a in recent])
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No attendance records yet.")
    with r:
        with st.container(border=True):
            panel_heading("Renewals to watch", "Members expiring in the next 7 days")
            upcoming = [m for m in st.session_state.members if m["status"] != "Expired" and 0 <= (m["expiry"]-date.today()).days <= 7]
            if upcoming:
                for m in upcoming[:4]:
                    a,b = st.columns([3,1])
                    a.markdown(f"**{m['name']}**<br><span class='small-muted'>{m['id']} · {m['expiry'].strftime('%d %b')}</span>", unsafe_allow_html=True)
                    b.markdown(status_badge("Pending"), unsafe_allow_html=True)
            else:
                st.success("No renewals due in the next 7 days.")

# ---------------------------------------------------------------------------
# Member directory and registration
# ---------------------------------------------------------------------------
elif page == "Members":
    page_header("MEMBER MANAGEMENT", "Member directory", "Search, filter, register, and manage your gym community.")
    directory_tab, register_tab = st.tabs(["👥 Directory", "＋ Register member"])
    with directory_tab:
        f1,f2 = st.columns([1,2])
        status_filter = f1.selectbox("Membership status", ["All", "Active", "Expired", "Pending"])
        search = f2.text_input("Search name, member ID, or phone", placeholder="e.g. Aarav, M-1001, 9876…")
        filtered = []
        for m in st.session_state.members:
            if status_filter != "All" and m["status"] != status_filter:
                continue
            if search and search.lower() not in f'{m["name"]} {m["id"]} {m["phone"]}'.lower():
                continue
            filtered.append(m)
        if filtered:
            table = pd.DataFrame([{"Member ID":m["id"], "Name":m["name"], "Phone":m["phone"],
                "Plan":m["plan"], "Joined":m["joined"], "Expiry":m["expiry"], "Fee":m["fee"], "Status":m["status"]} for m in filtered])
            st.dataframe(table, use_container_width=True, hide_index=True,
                         column_config={"Fee": st.column_config.NumberColumn("Fee (₹)", format="₹%d"),
                                       "Status": st.column_config.TextColumn("Status")})
        else:
            st.info("No members match the selected filters.")
        st.caption(f"Showing {len(filtered)} of {len(st.session_state.members)} members")
        with st.expander("Member details / invoice"):
            options = {f'{m["id"]} · {m["name"]}':m["id"] for m in filtered}
            if options:
                selected = st.selectbox("Choose member", list(options.keys()), key="detail_member")
                m = get_member(options[selected])
                x,y,z = st.columns(3)
                x.write(f"**Plan**  \n{m['plan']}")
                y.write(f"**Expiry**  \n{m['expiry'].strftime('%d %b %Y')}")
                z.markdown(status_badge(m["status"]), unsafe_allow_html=True)
                html_doc = invoice_html(m)
                st.download_button("Download HTML invoice", html_doc, file_name=f"invoice_{m['id']}.html", mime="text/html")
                st.code(f"Member ID: {m['id']} | Phone: {m['phone']} | Fee: {money(m['fee'])}", language=None)
    with register_tab:
        with st.form("register_member", clear_on_submit=True):
            st.subheader("New member profile")
            a,b = st.columns(2)
            name = a.text_input("Full name *")
            phone = b.text_input("Phone number *", max_chars=15)
            c,d = st.columns(2)
            plan = c.selectbox("Membership plan", list(PLAN_DAYS.keys()))
            joined = d.date_input("Joining date", value=date.today())
            e,f = st.columns(2)
            fee = e.number_input("Membership fee (₹)", min_value=0, value=PLAN_PRICE[plan], step=100)
            status = f.selectbox("Initial status", ["Active", "Pending"])
            submitted = st.form_submit_button("Create member", type="primary", use_container_width=True)
        if submitted:
            clean_phone = "".join(ch for ch in phone if ch.isdigit() or ch == "+")
            if not name.strip():
                st.error("Please enter the member's full name.")
            elif len(clean_phone) < 10:
                st.error("Please enter a valid phone number (at least 10 digits).")
            elif any(m["phone"] == clean_phone for m in st.session_state.members):
                st.error("This phone number already exists in the member directory.")
            else:
                new_id = next_member_id()
                expiry = joined + timedelta(days=PLAN_DAYS[plan])
                new_member = {"id":new_id, "name":name.strip(), "phone":clean_phone, "plan":plan,
                              "expiry":expiry, "fee":int(fee), "status":status, "joined":joined}
                st.session_state.members.append(new_member)
                st.session_state.payments.append({"id":f"PAY-{uuid.uuid4().hex[:6].upper()}",
                    "member_id":new_id, "member":name.strip(), "amount":int(fee),
                    "due":joined, "status":"Pending"})
                st.success(f"Member created successfully · {new_id}")
                st.rerun()

# ---------------------------------------------------------------------------
# Payments, renewal actions, reminders, invoices
# ---------------------------------------------------------------------------
elif page == "Payments":
    page_header("BILLING & SUBSCRIPTIONS", "Payments & renewals", "Track collections, follow up on dues, and create member invoices.")
    overdue = sum(p["status"] == "Overdue" for p in st.session_state.payments)
    pending = sum(p["status"] == "Pending" for p in st.session_state.payments)
    a,b,c = st.columns(3)
    a.metric("Overdue", overdue)
    b.metric("Pending", pending)
    c.metric("Collected this month", money(sum(p["amount"] for p in st.session_state.payments if p["status"] == "Paid")))
    pay_tab, reminder_tab, invoice_tab = st.tabs(["💳 Due payments", "✉️ Reminders", "🧾 Invoice generator"])
    with pay_tab:
        due_payments = [p for p in st.session_state.payments if p["status"] in ("Overdue","Pending")]
        if due_payments:
            for p in due_payments:
                with st.container(border=True):
                    x,y,z,w = st.columns([2.2,1,1,1.2])
                    x.markdown(f"**{p['member']}**  \n<span class='small-muted'>{p['member_id']} · Due {p['due'].strftime('%d %b %Y')}</span>", unsafe_allow_html=True)
                    y.markdown(money(p["amount"]))
                    z.markdown(status_badge(p["status"]), unsafe_allow_html=True)
                    if w.button("✓ Mark paid", key=f"paid_{p['id']}", type="primary"):
                        mark_payment_paid(p["id"])
                        st.success(f"Payment recorded for {p['member']}")
                        st.rerun()
        else:
            st.success("All payment dues are cleared.")
        st.divider()
        with st.expander("Payment ledger"):
            ledger = pd.DataFrame([{"Payment ID":p["id"], "Member":p["member"], "Member ID":p["member_id"],
                "Amount (₹)":p["amount"], "Due date":p["due"], "Status":p["status"]} for p in st.session_state.payments])
            st.dataframe(ledger, use_container_width=True, hide_index=True)
    with reminder_tab:
        candidates = [p for p in st.session_state.payments if p["status"] in ("Overdue","Pending")]
        if candidates:
            selected_reminder = st.selectbox("Select renewal", [f'{p["member"]} · {p["member_id"]}' for p in candidates])
            target = candidates[[f'{p["member"]} · {p["member_id"]}' for p in candidates].index(selected_reminder)]
            days = (target["due"]-date.today()).days
            if days < 0:
                message = f"Hi {target['member']}, your Apex Gym membership payment of {money(target['amount'])} is overdue by {abs(days)} day(s). Please renew to keep your membership active. Thank you!"
            else:
                message = f"Hi {target['member']}, your Apex Gym membership payment of {money(target['amount'])} is due on {target['due'].strftime('%d %b')}. Please renew soon. Thank you!"
            st.text_area("Message preview", message, height=120)
            st.caption("Copy this message and send it using your preferred messaging app. No message is sent automatically.")
            st.button("Reminder prepared", disabled=True)
        else:
            st.success("No pending reminders.")
    with invoice_tab:
        choices = {f'{m["id"]} · {m["name"]}':m for m in st.session_state.members}
        if choices:
            chosen_member = st.selectbox("Member", list(choices.keys()), key="invoice_member")
            m = choices[chosen_member]
            st.markdown(f"**{m['name']}** · {m['plan']} · {money(m['fee'])}")
            st.download_button("Generate / download invoice (HTML)", invoice_html(m),
                file_name=f"Apex_invoice_{m['id']}.html", mime="text/html", type="primary")
            st.caption("Open the downloaded HTML in a browser and print it to PDF if needed.")

# ---------------------------------------------------------------------------
# Schedule and trainers
# ---------------------------------------------------------------------------
elif page == "Schedule & Trainers":
    page_header("FITNESS PROGRAMMING", "Schedule & trainers", "Manage group classes, instructors, and enrollment capacity.")
    classes_tab, add_tab = st.tabs(["📅 Class schedule", "＋ Add class"])
    with classes_tab:
        for cls in st.session_state.classes:
            with st.container(border=True):
                a,b = st.columns([3,1])
                a.markdown(f"**{cls['name']}**  \n<span class='small-muted'>{cls['id']} · {cls['day']} · {cls['time']}</span>", unsafe_allow_html=True)
                b.markdown(f"**{cls['enrolled']} / {cls['capacity']}**<br><span class='small-muted'>ENROLLED</span>", unsafe_allow_html=True)
                st.progress(min(cls["enrolled"]/max(cls["capacity"],1),1.0), text=f"Trainer: {cls['trainer']} · {max(cls['capacity']-cls['enrolled'],0)} spots remaining")
                col1,col2 = st.columns([1,5])
                if col1.button("＋ Enroll", key=f"enroll_{cls['id']}", disabled=cls["enrolled"] >= cls["capacity"]):
                    cls["enrolled"] += 1
                    st.toast(f"Enrollment added to {cls['name']}")
                    st.rerun()
                if cls["enrolled"] >= cls["capacity"]:
                    col2.markdown(status_badge("Full"), unsafe_allow_html=True)
    with add_tab:
        with st.form("new_class", clear_on_submit=True):
            st.subheader("Create group class")
            name = st.text_input("Class name *")
            trainer = st.text_input("Trainer name *")
            a,b = st.columns(2)
            class_day = a.selectbox("Schedule", ["Mon–Fri", "Mon, Wed, Fri", "Tue–Sat", "Mon, Thu, Sat", "Saturday", "Sunday"])
            class_time = b.time_input("Start time", value=datetime.strptime("06:30","%H:%M").time())
            c,d = st.columns(2)
            capacity = c.number_input("Maximum capacity", min_value=1, max_value=100, value=15)
            enrolled = d.number_input("Initial enrollment", min_value=0, max_value=int(capacity), value=0)
            create_class = st.form_submit_button("Add class", type="primary", use_container_width=True)
        if create_class:
            if not name.strip() or not trainer.strip():
                st.error("Class name and trainer are required.")
            else:
                st.session_state.classes.append({"id":f"CL-{uuid.uuid4().hex[:4].upper()}",
                    "name":name.strip(), "trainer":trainer.strip(), "time":class_time.strftime("%I:%M %p"),
                    "capacity":int(capacity), "enrolled":int(enrolled), "day":class_day})
                st.success("Class added to schedule.")
                st.rerun()

# ---------------------------------------------------------------------------
# Live attendance log
# ---------------------------------------------------------------------------
elif page == "Attendance":
    page_header("FLOOR ACTIVITY", "Live attendance log", "Every check-in is recorded with a local timestamp.")
    today_records = [a for a in st.session_state.attendance if a["timestamp"].date() == date.today()]
    a,b,c = st.columns(3)
    a.metric("Today's visits", len(today_records))
    c_unique = len(set(a["member_id"] for a in today_records))
    b.metric("Unique members", c_unique)
    c.metric("Latest check-in", today_records[0]["timestamp"].strftime("%I:%M %p") if today_records else "—")
    st.write("")
    with st.container(border=True):
        panel_heading("Attendance history", "Most recent first")
        if st.session_state.attendance:
            data = pd.DataFrame([{"Member":a["name"], "Member ID":a["member_id"],
                "Date":a["timestamp"].strftime("%d %b %Y"), "Time":a["timestamp"].strftime("%I:%M:%S %p"),
                "Timestamp":a["timestamp"].isoformat(timespec="seconds")} for a in st.session_state.attendance])
            st.dataframe(data, use_container_width=True, hide_index=True)
            csv = data.to_csv(index=False).encode("utf-8")
            st.download_button("Export attendance CSV", csv, "apex_attendance.csv", "text/csv")
        else:
            st.info("No check-ins recorded yet.")
    st.caption("Use the sidebar quick check-in to log a visit. Check-ins are stored in this Streamlit session.")

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown('<div class="small-muted">APEX GYM OS · Local session workspace · Built for gym operations</div>', unsafe_allow_html=True)
