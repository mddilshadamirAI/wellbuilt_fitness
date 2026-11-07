 <div align="center">

# 🏋️ APEX FIT GYM OS
### Gym Management & Business Operations System

---

### 🌐 OVERVIEW

**Apex Fit Gym OS** is a Streamlit-based gym management application designed to simplify daily fitness business operations. It brings member management, membership payments, attendance tracking, trainer records, lead follow-ups, expense management, and business reporting into one centralized dashboard.

Built with Python and SQLite, it provides gym owners with a practical way to organize their operations and monitor business activity.

---

### ✨ CORE CAPABILITIES

| Feature | Impact |
| :--- | :--- |
| **📊 Business Dashboard** | Monitor members, collections, expenses, renewals, and leads. |
| **👥 Member Management** | Register, search, update, and manage gym members. |
| **💳 Membership & Payments** | Manage membership plans, payment records, and fee history. |
| **🕒 Attendance Tracking** | Record check-ins and check-outs with occupancy insights. |
| **📩 Lead Management** | Track enquiries, follow-ups, and WhatsApp contact links. |
| **🏋️ Trainer Management** | Organize trainer profiles, specialties, shifts, and salaries. |
| **💪 Workout Routines** | Explore predefined routines and add custom workout plans. |
| **💰 Expense Tracking** | Record business expenses and monitor financial activity. |
| **📈 Reports & Backup** | View financial summaries, export CSV reports, and download database backups. |

---

### 🛠️ TECHNICAL ARSENAL

* **Language:** Python
* **Framework:** Streamlit
* **Database:** SQLite
* **Data Processing:** Pandas
* **Authentication:** PBKDF2-HMAC-SHA256 password hashing with individual salts.
* **Interface:** Custom CSS and Streamlit components.
* **Architecture:** Single-file Streamlit application with SQLite-based storage.
* **Status:** 🚧 **MVP — Under Development**

---

### ⚙️ INSTALLATION & EXECUTION

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/apex-fit-gym-os.git

# Navigate to the project
cd apex-fit-gym-os

# Install dependencies
pip install streamlit pandas

# Run the application
streamlit run app.py
```

---

### 📁 PROJECT STRUCTURE

```text
apex-fit-gym-os/
│
├── app.py
├── apex_fit.db
└── README.md
```

*The SQLite database is automatically initialized when the application starts.*

---

### 📈 FUTURE ROADMAP

* **Advanced Analytics:** More detailed gym performance and revenue insights.
* **Automated Notifications:** Membership expiry and payment reminders.
* **Cloud Database:** Persistent, production-ready database infrastructure.
* **Multi-User Access:** Secure role-based access for owners and staff.
* **Enhanced Reporting:** More customizable reports and business insights.

---

> *"Simplifying gym operations through practical software — bringing membership management, attendance, and business insights together in one place."*

---

<p align="center">
  <img src="https://img.shields.io/badge/Language-Python-blue?style=flat-square&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Framework-Streamlit-red?style=flat-square&logo=streamlit" alt="Streamlit">
  <img src="https://img.shields.io/badge/Database-SQLite-003B57?style=flat-square&logo=sqlite" alt="SQLite">
  <img src="https://img.shields.io/badge/Status-MVP-orange?style=flat-square" alt="Status">
</p>

**Developed by MD DILSHAD AMIR**

© 2026 MD DILSHAD AMIR | *Built with Python.*

</div>

---

**Note:** This is an MVP. Production deployment requires persistent database hosting and stronger multi-user data isolation and access controls.
