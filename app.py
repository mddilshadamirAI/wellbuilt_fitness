import streamlit as st, sqlite3, hashlib, secrets, pandas as pd
from datetime import date, datetime, timedelta
from urllib.parse import quote
from pathlib import Path

DB = Path("apex_fit.db")

st.set_page_config(
    page_title="Apex Fit Gym OS",
    page_icon="🏋️",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=Space+Grotesk:wght@600;700&display=swap');

.stApp {
    background: radial-gradient(ellipse at 15% 0%, #172b3b, #080d14 48%);
    color: #edf5fb;
    font-family: Inter;
}

.block-container {
    max-width: 1450px;
    padding-top: 1.5rem;
}

h1,h2,h3 {
    font-family: 'Space Grotesk';
    letter-spacing: -.03em;
}

[data-testid=stSidebar] {
    background: #0b121a;
    border-right: 1px solid #283847;
}

[data-testid=stMetric] {
    background: linear-gradient(145deg,#162431,#101923);
    border: 1px solid #2b3c4b;
    padding: 16px;
    border-radius: 15px;
}

.stButton>button {
    border-radius: 10px;
    border: 1px solid #334654;
    background: #172431;
    color: #f0f6fb;
    font-weight: 600;
}

.stButton>button[kind=primary] {
    background: #b7f34a;
    color: #091018;
    border: 0;
}

[data-testid=stForm] {
    background: #101923;
    border: 1px solid #2a3b49;
    border-radius: 15px;
    padding: 16px;
}

.apex {
    background: linear-gradient(115deg,#172b39,#101923 65%,#18251b);
    border: 1px solid #304554;
    border-radius: 22px;
    padding: 26px;
    margin-bottom: 18px;
}

.kicker {
    color: #b7f34a;
    font-size: .72rem;
    font-weight: 800;
    letter-spacing: .16em;
}

.sub {
    color: #9eb2c3;
}

.chip {
    color: #b7f34a;
    border: 1px solid #b7f34a55;
    background: #b7f34a15;
    padding: 4px 9px;
    border-radius: 30px;
    font-size: .72rem;
}

.card {
    background: #111c26;
    border: 1px solid #2b3c4b;
    border-radius: 15px;
    padding: 15px;
}
</style>
""", unsafe_allow_html=True)


# DATABASE

def db():
    c = sqlite3.connect(DB, check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c


def init():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS owner(
            id INTEGER PRIMARY KEY,
            gym TEXT,
            owner TEXT,
            user TEXT UNIQUE,
            salt TEXT,
            hash TEXT
        );

        CREATE TABLE IF NOT EXISTS members(
            id INTEGER PRIMARY KEY,
            name TEXT,
            phone TEXT,
            email TEXT,
            age INTEGER,
            goal TEXT,
            emergency TEXT,
            plan TEXT,
            fee REAL,
            start TEXT,
            end TEXT,
            slot TEXT,
            trainer TEXT,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS payments(
            id INTEGER PRIMARY KEY,
            member INTEGER,
            amount REAL,
            date TEXT,
            method TEXT,
            note TEXT,
            FOREIGN KEY(member) REFERENCES members(id)
        );

        CREATE TABLE IF NOT EXISTS attendance(
            id INTEGER PRIMARY KEY,
            member INTEGER,
            checkin TEXT,
            checkout TEXT,
            FOREIGN KEY(member) REFERENCES members(id)
        );

        CREATE TABLE IF NOT EXISTS leads(
            id INTEGER PRIMARY KEY,
            name TEXT,
            phone TEXT,
            goal TEXT,
            source TEXT,
            status TEXT,
            follow TEXT,
            note TEXT
        );

        CREATE TABLE IF NOT EXISTS trainers(
            id INTEGER PRIMARY KEY,
            name TEXT,
            phone TEXT,
            specialty TEXT,
            shift TEXT,
            fee REAL
        );

        CREATE TABLE IF NOT EXISTS expenses(
            id INTEGER PRIMARY KEY,
            title TEXT,
            category TEXT,
            amount REAL,
            date TEXT,
            note TEXT
        );

        CREATE TABLE IF NOT EXISTS plans(
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            days INTEGER,
            price REAL
        );

        CREATE TABLE IF NOT EXISTS routines(
            id INTEGER PRIMARY KEY,
            title TEXT,
            level TEXT,
            goal TEXT,
            days TEXT,
            details TEXT
        );
        """)

        if not c.execute("SELECT count(*) FROM plans").fetchone()[0]:
            c.executemany(
                "INSERT INTO plans(name,days,price) VALUES(?,?,?)",
                [
                    ("Monthly",30,1500),
                    ("Quarterly",90,4000),
                    ("Half-yearly",180,7000),
                    ("Annual",365,12000)
                ]
            )

        if not c.execute("SELECT count(*) FROM routines").fetchone()[0]:
            c.executemany(
                "INSERT INTO routines(title,level,goal,days,details) VALUES(?,?,?,?,?)",
                [
                    (
                        "Full Body Foundation",
                        "Starter",
                        "General fitness",
                        "3 days",
                        "Squat pattern, push, pull, hinge, core. Learn technique and train comfortably."
                    ),
                    (
                        "Beginner Fat Loss",
                        "Starter",
                        "Fat loss",
                        "3 days",
                        "Full body resistance + low-impact cardio; build consistency."
                    ),
                    (
                        "Upper / Lower Split",
                        "Medioker",
                        "Strength",
                        "4 days",
                        "Upper A, lower A, upper B, lower B; gradual progressive overload."
                    ),
                    (
                        "Muscle Builder",
                        "Medioker",
                        "Muscle gain",
                        "4 days",
                        "Push, pull, legs and full body with recovery days."
                    ),
                    (
                        "Strength Performance",
                        "Pro",
                        "Strength",
                        "5 days",
                        "Compound lifts, accessory work and planned recovery; coach supervised."
                    ),
                    (
                        "Athletic Conditioning",
                        "Pro",
                        "Conditioning",
                        "5 days",
                        "Strength, mobility and conditioning adjusted to recovery."
                    )
                ]
            )


def q(sql, args=()):
    with db() as c:
        return pd.read_sql_query(sql, c, params=args)


def run(sql, args=()):
    with db() as c:
        c.execute(sql, args)
        c.commit()


def h(p, s):
    return hashlib.pbkdf2_hmac(
        "sha256",
        p.encode(),
        bytes.fromhex(s),
        240000
    ).hex()


def money(x):
    return f"₹{float(x or 0):,.0f}"


def left(x):
    try:
        return (
            date.fromisoformat(str(x)[:10])
            - date.today()
        ).days
    except:
        return 999


def wa(phone, msg):
    d = "".join(
        ch for ch in str(phone or "")
        if ch.isdigit()
    )

    if len(d) == 10:
        d = "91" + d

    return (
        f"https://wa.me/{d}?text={quote(msg)}"
        if d else ""
    )


# INITIALIZE

init()

if "uid" not in st.session_state:
    st.session_state.uid = None


# AUTHENTICATION

if st.session_state.uid is None:

    st.markdown("""
    <div class="apex">
        <div class="kicker">APEX FIT · GYM OPERATING SYSTEM</div>
        <h1>Run your gym.<br>Know your numbers.</h1>
        <p class="sub">
            Member records · fees · attendance · workouts · follow-ups.
        </p>
    </div>
    """, unsafe_allow_html=True)

    owners = q("SELECT * FROM owner")

    if owners.empty:

        with st.form("setup"):

            gym = st.text_input("Gym name")
            owner = st.text_input("Owner")
            user = st.text_input("Username")

            pw = st.text_input(
                "Password (8+ chars)",
                type="password"
            )

            confirm = st.text_input(
                "Confirm password",
                type="password"
            )

            go = st.form_submit_button(
                "Create account",
                type="primary"
            )

        if go:

            if not all([gym, owner, user, pw]) or len(pw) < 8:
                st.error(
                    "Complete all fields; password must be 8+ characters."
                )

            elif pw != confirm:
                st.error("Passwords do not match.")

            else:

                salt = secrets.token_bytes(16).hex()

                try:
                    run(
                        "INSERT INTO owner(gym,owner,user,salt,hash) VALUES(?,?,?,?,?)",
                        (
                            gym,
                            owner,
                            user,
                            salt,
                            h(pw, salt)
                        )
                    )

                    st.success("Account created, sign in.")
                    st.rerun()

                except sqlite3.IntegrityError:
                    st.error("Username already exists.")

    else:

        with st.form("login"):

            user = st.text_input("Username")

            pw = st.text_input(
                "Password",
                type="password"
            )

            go = st.form_submit_button(
                "Sign in",
                type="primary"
            )

        if go:

            o = q(
                "SELECT * FROM owner WHERE user=?",
                (user,)
            )

            if not o.empty and h(pw, o.iloc[0].salt) == o.iloc[0]["hash"]:

                st.session_state.uid = int(o.iloc[0].id)
                st.rerun()

            else:
                st.error("Incorrect username or password.")

    st.stop()


# MAIN DATA

owner = q(
    "SELECT * FROM owner WHERE id=?",
    (st.session_state.uid,)
).iloc[0]

today = date.today()

members = q("SELECT * FROM members ORDER BY name")
plans = q("SELECT * FROM plans")
trainers = q("SELECT * FROM trainers")

pages = [
    "Overview",
    "Members & Fees",
    "Attendance",
    "Leads & Follow-ups",
    "Trainers",
    "Workout & Practice",
    "Expenses",
    "Reports / Backup"
]


# SIDEBAR

with st.sidebar:

    st.markdown("## 🟩 APEX FIT")
    st.caption(owner.gym)

    page = st.radio(
        "Workspace",
        pages
    )

    if st.button("Log out"):
        st.session_state.uid = None
        st.rerun()


# DASHBOARD DATA

month = today.replace(day=1).isoformat()

collection = q(
    "SELECT COALESCE(sum(amount),0) v FROM payments WHERE date>=?",
    (month,)
).iloc[0,0]

cost = q(
    "SELECT COALESCE(sum(amount),0) v FROM expenses WHERE date>=?",
    (month,)
).iloc[0,0]

active = (
    members[members.end >= today.isoformat()]
    if len(members)
    else members
)

due = (
    members[
        members.end.apply(
            lambda x: 0 <= left(x) <= 7
        )
    ]
    if len(members)
    else members
)


def stitle(k, t, s=None):

    st.markdown(
        f'<div class="kicker">{k}</div>'
        f'<h2>{t}</h2>'
        f'{("<p class=sub>"+s+"</p>") if s else ""}',
        unsafe_allow_html=True
    )


# OVERVIEW

if page == "Overview":

    st.markdown(
        f"""
        <div class="apex">
            <div class="kicker">
                GYM COMMAND CENTER · {today:%A, %d %B %Y}
            </div>
            <h1>Welcome, {owner.owner.split()[0]}.</h1>
            <p class="sub">
                Start with renewals, new enquiries and daily attendance.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    a,b,c,d = st.columns(4)

    a.metric("Active members", len(active))
    b.metric("Renewals due · 7 days", len(due))
    c.metric("Collected this month", money(collection))
    d.metric("Expenses this month", money(cost))

    a,b,c = st.columns(3)

    a.metric(
        "Net recorded cash",
        money(collection-cost)
    )

    b.metric(
        "Members in database",
        len(members)
    )

    c.metric(
        "Leads",
        len(q("SELECT * FROM leads"))
    )

    st.divider()

    stitle(
        "DAILY ACTION CENTER",
        "Renewals to follow up"
    )

    if due.empty:
        st.success(
            "No memberships expiring in the next 7 days."
        )

    for _,m in due.iterrows():

        n = left(m.end)

        st.markdown(
            f"""
            <div class="card">
                <b>{m["name"]}</b> ·
                <span class=chip>
                    {"DUE TODAY" if n==0 else str(n)+" days left"}
                </span>
                <p class=sub>
                    {m.plan} · {m.phone or "phone missing"}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        link = wa(
            m.phone,
            f"Hi {m['name']}, your membership at {owner.gym} is due "
            f"{'today' if n==0 else f'in {n} days'}. "
            "Reply if you would like to renew."
        )

        if link:
            st.markdown(
                f"[Open WhatsApp reminder ↗]({link})"
            )

    st.caption(
        "Messages are pre-filled; review and send manually."
    )


# MEMBERS AND FEES

elif page == "Members & Fees":

    stitle(
        "MEMBER MANAGEMENT",
        "Member records & fee tracking",
        "Keep personal details, membership dates, fee, preferred time, trainer and emergency contact together."
    )

    with st.expander("＋ Register member", expanded=True):

        with st.form("addmember"):

            a,b,c = st.columns(3)

            name = a.text_input("Full name *")
            phone = b.text_input("Phone / WhatsApp")
            email = c.text_input("Email")

            age = a.number_input(
                "Age",
                min_value=0,
                max_value=100,
                value=25
            )

            goal = b.selectbox(
                "Fitness goal",
                [
                    "General fitness",
                    "Weight loss",
                    "Muscle gain",
                    "Strength",
                    "Mobility"
                ]
            )

            emergency = c.text_input("Emergency contact")

            slot = a.selectbox(
                "Training time",
                [
                    "Morning 5–9 AM",
                    "Late morning 9–12",
                    "Afternoon 12–4",
                    "Evening 4–8",
                    "Night 8–10",
                    "Flexible"
                ]
            )

            plan = b.selectbox(
                "Plan",
                plans.name.tolist()
            )

            start = c.date_input(
                "Start",
                today
            )

            days = int(
                plans[plans.name == plan].iloc[0].days
            )

            end = a.date_input(
                "Expiry",
                start + timedelta(days=days)
            )

            fee = b.number_input(
                "Membership fee ₹",
                min_value=0.,
                value=float(
                    plans[plans.name == plan].iloc[0].price
                ),
                step=100.
            )

            trainer = c.selectbox(
                "Trainer",
                ["Unassigned"] + trainers.name.tolist()
            )

            notes = st.text_area(
                "Coaching notes (consent-based)"
            )

            save = st.form_submit_button(
                "Save member",
                type="primary"
            )

        if save:

            if not name.strip() or end < start:

                st.error("Enter name and valid dates.")

            else:

                run(
                    """
                    INSERT INTO members(
                        name,phone,email,age,goal,emergency,
                        plan,fee,start,end,slot,trainer,notes
                    )
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        name,
                        phone,
                        email,
                        age,
                        goal,
                        emergency,
                        plan,
                        fee,
                        start.isoformat(),
                        end.isoformat(),
                        slot,
                        trainer,
                        notes
                    )
                )

                st.success("Member saved.")
                st.rerun()

    st.divider()

    st.subheader("Member directory")

    search = st.text_input(
        "Search member by name or phone"
    )

    data = q(
        "SELECT * FROM members ORDER BY name"
    )

    if search:

        data = data[
            data.name.str.contains(
                search,
                case=False,
                na=False
            )
            |
            data.phone.fillna("").str.contains(
                search,
                case=False,
                na=False
            )
        ]

    st.dataframe(
        data,
        use_container_width=True,
        hide_index=True
    )

    if len(data):

        mid = st.selectbox(
            "Select member",
            data.id.tolist(),
            format_func=lambda x:
                f'{data[data.id==x].iloc[0]["name"]} #{x}'
        )

        m = q(
            "SELECT * FROM members WHERE id=?",
            (int(mid),)
        ).iloc[0]

        st.markdown(
            f"""
            <div class="apex">
                <div class="kicker">MEMBER PROFILE</div>
                <h2>{m["name"]}</h2>
                <p class="sub">
                    {m.plan} · {m.slot} · {m.trainer}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        a,b,c,d = st.columns(4)

        a.metric("Membership fee", money(m.fee))
        b.metric("Expiry", m.end)
        c.metric("Days remaining", left(m.end))
        d.metric("Goal", m.goal)

        st.subheader("Record payment")

        with st.form("payment"):

            amount = st.number_input(
                "Amount ₹",
                min_value=1.,
                value=float(m.fee)
            )

            day = st.date_input(
                "Payment date",
                today
            )

            method = st.selectbox(
                "Method",
                [
                    "Cash",
                    "UPI",
                    "Card",
                    "Bank transfer",
                    "Other"
                ]
            )

            note = st.text_input(
                "Reference / period"
            )

            save = st.form_submit_button(
                "Record payment"
            )

        if save:

            run(
                """
                INSERT INTO payments(member,amount,date,method,note)
                VALUES(?,?,?,?,?)
                """,
                (
                    int(mid),
                    amount,
                    day.isoformat(),
                    method,
                    note
                )
            )

            st.success("Payment recorded.")
            st.rerun()

        hist = q(
            """
            SELECT date,amount,method,note
            FROM payments
            WHERE member=?
            ORDER BY date DESC
            """,
            (int(mid),)
        )

        st.subheader("Payment history")

        st.dataframe(
            hist,
            use_container_width=True,
            hide_index=True
        )

        with st.expander("Edit member"):

            with st.form("edit"):

                n = st.text_input(
                    "Name",
                    m.name
                )

                p = st.text_input(
                    "Phone",
                    m.phone or ""
                )

                f = st.number_input(
                    "Fee",
                    min_value=0.,
                    value=float(m.fee)
                )

                e = st.date_input(
                    "Expiry",
                    date.fromisoformat(m.end)
                )

                sl = st.text_input(
                    "Time slot",
                    m.slot or "Flexible"
                )

                tr = st.text_input(
                    "Trainer",
                    m.trainer or "Unassigned"
                )

                nt = st.text_area(
                    "Notes",
                    m.notes or ""
                )

                u = st.form_submit_button(
                    "Save edits"
                )

            if u:

                run(
                    """
                    UPDATE members
                    SET name=?,phone=?,fee=?,end=?,
                        slot=?,trainer=?,notes=?
                    WHERE id=?
                    """,
                    (
                        n,
                        p,
                        f,
                        e.isoformat(),
                        sl,
                        tr,
                        nt,
                        int(mid)
                    )
                )

                st.success("Updated.")
                st.rerun()

    with st.expander("Membership plan settings"):

        with st.form("plan"):

            n = st.text_input("Plan name")

            d = st.number_input(
                "Duration days",
                min_value=1,
                value=30
            )

            p = st.number_input(
                "Price ₹",
                min_value=0.,
                value=1500.
            )

            add = st.form_submit_button(
                "Add plan"
            )

        if add:

            try:

                run(
                    "INSERT INTO plans(name,days,price) VALUES(?,?,?)",
                    (n,int(d),p)
                )

                st.success("Added.")
                st.rerun()

            except sqlite3.IntegrityError:

                st.error("Plan exists.")

        st.dataframe(
            plans,
            use_container_width=True,
            hide_index=True
        )


# ATTENDANCE

elif page == "Attendance":

    stitle(
        "ATTENDANCE",
        "Check-in desk",
        "Track visits and current gym occupancy."
    )

    act = q(
        "SELECT id,name FROM members WHERE end>=?",
        (today.isoformat(),)
    )

    if len(act):

        mid = st.selectbox(
            "Member",
            act.id.tolist(),
            format_func=lambda x:
                f'{act[act.id==x].iloc[0]["name"]} #{x}'
        )

        if st.button(
            "Check in",
            type="primary"
        ):

            if len(
                q(
                    "SELECT id FROM attendance WHERE member=? AND checkout IS NULL",
                    (int(mid),)
                )
            ):

                st.warning("Already checked in.")

            else:

                run(
                    "INSERT INTO attendance(member,checkin) VALUES(?,?)",
                    (
                        int(mid),
                        datetime.now().isoformat()
                    )
                )

                st.success("Checked in.")
                st.rerun()

    opened = q(
        """
        SELECT a.id,m.name,a.checkin
        FROM attendance a
        JOIN members m ON m.id=a.member
        WHERE checkout IS NULL
        """
    )

    st.subheader("Currently in gym")

    for _,r in opened.iterrows():

        a,b = st.columns([4,1])

        a.write(
            f'**{r["name"]}** · {r.checkin}'
        )

        if b.button(
            "Check out",
            key=str(r.id)
        ):

            run(
                "UPDATE attendance SET checkout=? WHERE id=?",
                (
                    datetime.now().isoformat(),
                    int(r.id)
                )
            )

            st.rerun()

    st.subheader("Recent attendance")

    hist = q(
        """
        SELECT m.name,a.checkin,a.checkout
        FROM attendance a
        JOIN members m ON m.id=a.member
        ORDER BY a.id DESC
        LIMIT 200
        """
    )

    st.dataframe(
        hist,
        use_container_width=True,
        hide_index=True
    )


# LEADS

elif page == "Leads & Follow-ups":

    stitle(
        "SALES PIPELINE",
        "Convert enquiries into memberships"
    )

    with st.form("lead"):

        a,b,c = st.columns(3)

        n = a.text_input("Name *")
        p = b.text_input("Phone")

        g = c.selectbox(
            "Interest",
            [
                "Membership",
                "Weight loss",
                "Muscle gain",
                "Personal training",
                "Other"
            ]
        )

        src = a.selectbox(
            "Source",
            [
                "Walk-in",
                "Instagram",
                "Facebook",
                "Google",
                "Referral",
                "Website",
                "Other"
            ]
        )

        status = b.selectbox(
            "Stage",
            [
                "New",
                "Contacted",
                "Trial booked",
                "Trial completed",
                "Negotiating",
                "Won",
                "Lost"
            ]
        )

        follow = c.date_input(
            "Follow-up date",
            today
        )

        note = st.text_input("Notes")

        save = st.form_submit_button(
            "Add lead",
            type="primary"
        )

    if save:

        if not n.strip():

            st.error("Name required.")

        else:

            run(
                """
                INSERT INTO leads(
                    name,phone,goal,source,status,follow,note
                )
                VALUES(?,?,?,?,?,?,?)
                """,
                (
                    n,
                    p,
                    g,
                    src,
                    status,
                    follow.isoformat(),
                    note
                )
            )

            st.success("Lead added.")
            st.rerun()

    data = q(
        "SELECT * FROM leads ORDER BY follow"
    )

    st.dataframe(
        data,
        use_container_width=True,
        hide_index=True
    )

    if len(data):

        lid = st.selectbox(
            "Update lead",
            data.id.tolist(),
            format_func=lambda x:
                f'{data[data.id==x].iloc[0]["name"]} · '
                f'{data[data.id==x].iloc[0]["status"]}'
        )

        l = data[data.id==lid].iloc[0]

        with st.form("leadupdate"):

            ns = st.selectbox(
                "Stage",
                [
                    "New",
                    "Contacted",
                    "Trial booked",
                    "Trial completed",
                    "Negotiating",
                    "Won",
                    "Lost"
                ]
            )

            nf = st.date_input(
                "Follow-up",
                date.fromisoformat(l.follow)
                if l.follow else today
            )

            nn = st.text_input(
                "Notes",
                l.note or ""
            )

            u = st.form_submit_button(
                "Update"
            )

        if u:

            run(
                "UPDATE leads SET status=?,follow=?,note=? WHERE id=?",
                (
                    ns,
                    nf.isoformat(),
                    nn,
                    int(lid)
                )
            )

            st.success("Updated.")
            st.rerun()

        link = wa(
            l.phone,
            f"Hi {l['name']}, thanks for enquiring about {owner.gym}. "
            "Would you like to visit for a trial?"
        )

        if link:

            st.markdown(
                f"[Open WhatsApp follow-up ↗]({link})"
            )


# TRAINERS

elif page == "Trainers":

    stitle(
        "TEAM",
        "Trainer directory"
    )

    with st.form("trainer"):

        a,b,c = st.columns(3)

        n = a.text_input("Trainer name")
        p = b.text_input("Phone")

        s = c.selectbox(
            "Specialty",
            [
                "General fitness",
                "Strength",
                "Weight loss",
                "Yoga / mobility",
                "Personal training",
                "Other"
            ]
        )

        shift = a.text_input(
            "Shift",
            "Morning"
        )

        fee = b.number_input(
            "Monthly pay ₹",
            min_value=0.
        )

        save = st.form_submit_button(
            "Add trainer"
        )

    if save:

        if n.strip():

            run(
                "INSERT INTO trainers(name,phone,specialty,shift,fee) VALUES(?,?,?,?,?)",
                (
                    n,
                    p,
                    s,
                    shift,
                    fee
                )
            )

            st.success("Added.")
            st.rerun()

    data = q(
        "SELECT * FROM trainers"
    )

    st.dataframe(
        data,
        use_container_width=True,
        hide_index=True
    )


# WORKOUT LIBRARY

elif page == "Workout & Practice":

    stitle(
        "EXERCISE LIBRARY",
        "Practice with proper form",
        "Starter · Medioker · Pro workout paths and equipment technique references."
    )

    tabs = st.tabs(
        [
            "Starter",
            "Medioker",
            "Pro",
            "Equipment guide"
        ]
    )

    routines = q(
        "SELECT * FROM routines"
    )

    for tab,level in zip(
        tabs[:3],
        ["Starter","Medioker","Pro"]
    ):

        with tab:

            st.markdown(
                f'<span class=chip>{level.upper()} · ROUTINES</span>',
                unsafe_allow_html=True
            )

            for _,r in routines[
                routines.level==level
            ].iterrows():

                st.markdown(
                    f"""
                    <div class=card>
                        <b>{r["title"]}</b>
                        <p class=sub>
                            {r.goal} · {r.days}
                        </p>
                        {r.details}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                st.write("")

    with tabs[3]:

        equipment = [

            (
                "Treadmill",
                "Cardio · walking/running",
                "Start slow, attach safety clip, increase speed gradually.",
                "https://images.unsplash.com/photo-1538805060514-97d9cc17730c?auto=format&fit=crop&w=1200&q=80"
            ),

            (
                "Dumbbells",
                "Free weights · strength",
                "Brace core, keep wrists stable, lower under control; avoid swinging.",
                "https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?auto=format&fit=crop&w=1200&q=80"
            ),

            (
                "Cable station",
                "Resistance training",
                "Check pin and attachments; use smooth reps, don't jerk the stack.",
                "https://images.unsplash.com/photo-1599058917212-d750089bc07e?auto=format&fit=crop&w=1200&q=80"
            ),

            (
                "Leg press",
                "Lower body machine",
                "Keep back supported and knees unlocked; use comfortable range.",
                "https://images.unsplash.com/photo-1579758629938-03607ccdbaba?auto=format&fit=crop&w=1200&q=80"
            ),

            (
                "Bench press",
                "Upper body strength",
                "Use a spotter for challenging loads; keep feet planted and wrists stacked.",
                "https://images.unsplash.com/photo-1534368270820-9de3d805e3bb?auto=format&fit=crop&w=1200&q=80"
            ),

            (
                "Stationary bike",
                "Low-impact cardio",
                "Adjust seat so knee stays slightly bent at pedal bottom.",
                "https://images.unsplash.com/photo-1591741535018-d042a5e7b5b3?auto=format&fit=crop&w=1200&q=80"
            )
        ]

        for i in range(0,len(equipment),2):

            cols = st.columns(2)

            for col,item in zip(
                cols,
                equipment[i:i+2]
            ):

                with col:

                    st.markdown(
                        '<div class=card>',
                        unsafe_allow_html=True
                    )

                    st.image(
                        item[3],
                        use_container_width=True
                    )

                    st.markdown(
                        f'**{item[0]}** · {item[1]}'
                    )

                    st.write(item[2])

                    st.markdown(
                        '</div>',
                        unsafe_allow_html=True
                    )

                    st.write("")

    st.warning(
        "Image references are illustrative. Coaches should demonstrate exact machine setup. Stop if an exercise causes pain."
    )

    with st.expander("Add custom gym routine"):

        with st.form("routine"):

            title = st.text_input("Routine name")

            level = st.selectbox(
                "Level",
                ["Starter","Medioker","Pro"]
            )

            goal = st.text_input("Goal")
            days = st.text_input("Schedule")
            details = st.text_area("Instructions")

            save = st.form_submit_button(
                "Save routine"
            )

        if save:

            run(
                "INSERT INTO routines(title,level,goal,days,details) VALUES(?,?,?,?,?)",
                (
                    title,
                    level,
                    goal,
                    days,
                    details
                )
            )

            st.success("Routine saved.")
            st.rerun()


# EXPENSES

elif page == "Expenses":

    stitle(
        "CASH FLOW",
        "Gym expenses"
    )

    with st.form("expense"):

        a,b,c = st.columns(3)

        n = a.text_input("Expense name")

        cat = b.selectbox(
            "Category",
            [
                "Rent",
                "Trainer salary",
                "Electricity",
                "Equipment",
                "Maintenance",
                "Marketing",
                "Other"
            ]
        )

        amount = c.number_input(
            "Amount ₹",
            min_value=1.
        )

        day = a.date_input(
            "Date",
            today
        )

        note = b.text_input("Note")

        save = st.form_submit_button(
            "Save expense"
        )

    if save:

        if n.strip():

            run(
                "INSERT INTO expenses(title,category,amount,date,note) VALUES(?,?,?,?,?)",
                (
                    n,
                    cat,
                    amount,
                    day.isoformat(),
                    note
                )
            )

            st.success("Saved.")
            st.rerun()

    data = q(
        "SELECT * FROM expenses ORDER BY date DESC"
    )

    st.dataframe(
        data,
        use_container_width=True,
        hide_index=True
    )


# REPORTS AND BACKUP

elif page == "Reports / Backup":

    stitle(
        "REPORTS",
        "Your recorded business numbers"
    )

    total = q(
        "SELECT COALESCE(sum(amount),0) v FROM payments"
    ).iloc[0,0]

    exp = q(
        "SELECT COALESCE(sum(amount),0) v FROM expenses"
    ).iloc[0,0]

    a,b,c,d = st.columns(4)

    a.metric(
        "Lifetime collections",
        money(total)
    )

    b.metric(
        "Expenses",
        money(exp)
    )

    c.metric(
        "Net recorded cash",
        money(total-exp)
    )

    d.metric(
        "Members",
        len(members)
    )

    p = q(
        "SELECT date,SUM(amount) amount FROM payments GROUP BY date ORDER BY date"
    )

    if len(p):

        p.date = pd.to_datetime(p.date)

        st.subheader("Collections by date")

        st.line_chart(
            p.set_index("date").amount
        )

    for table in [
        "members",
        "payments",
        "attendance",
        "leads",
        "trainers",
        "expenses",
        "plans",
        "routines"
    ]:

        data = q(
            f"SELECT * FROM {table}"
        )

        st.download_button(
            f"Export {table}.csv",
            data.to_csv(index=False).encode(),
            f"{table}.csv",
            "text/csv",
            key=table
        )

    if DB.exists():

        st.download_button(
            "Download database backup",
            DB.read_bytes(),
            f"apex_fit_backup_{today}.db",
            "application/octet-stream"
        )

    st.warning(
        "Sensitive member/payment data: secure backups. Use persistent database hosting before using with real customers."
    )


# FOOTER

st.sidebar.divider()

st.sidebar.caption(
    "APEX FIT · gym owner MVP"
)

st.sidebar.caption(
    "WhatsApp messages are reviewed and sent manually."
)
