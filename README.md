# 🏛️ SWC Election Platform — College Online Voting System

A complete, production-ready College Online Voting System built with Flask + Supabase + Face Recognition.

---

## 📋 Features

| Feature | Details |
|---|---|
| Student Signup | Self-registration with face photo upload |
| Admin Approval | Admin reviews and approves signup requests |
| OTP Login | 6-digit OTP sent via Gmail SMTP |
| Face Verification | Live webcam vs stored photo comparison (dlib) |
| Eligibility Engine | Automatic 3-year vote eligibility based on entry year |
| Ballot | One vote per position, confirmation modal |
| Results | Published on admin-set result date |
| Admin Dashboard | Live stats, Chart.js bar chart, turnout % |
| Fully Responsive | Mobile, tablet, desktop |

---

## 🗂️ Folder Structure

```
college-voting-system/
├── app.py                  ← All Flask routes
├── db.py                   ← Supabase queries
├── face_service.py         ← Face recognition logic
├── mail_service.py         ← OTP email (Gmail SMTP)
├── create_admin.py         ← One-time admin setup script
├── schema.sql              ← Supabase DB schema (run first)
├── requirements.txt
├── .env.example
├── Procfile
├── static/
│   ├── css/style.css
│   └── js/
│       ├── webcam.js
│       ├── vote.js
│       └── validation.js
└── templates/
    ├── base.html
    ├── signup.html
    ├── login.html
    ├── otp.html
    ├── dashboard.html
    ├── face_verify.html
    ├── ballot.html
    ├── thankyou.html
    ├── results.html
    └── admin/
        ├── login.html
        ├── dashboard.html
        ├── students.html
        ├── candidates.html
        ├── settings.html
        └── monitor.html
```

---

## ⚙️ Setup (Local Development)

### Step 1 — Clone & Install

```bash
git clone https://github.com/yourname/college-voting-system.git
cd college-voting-system

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

> **Note:** `face_recognition` requires `dlib` which requires CMake.
> On Ubuntu: `sudo apt-get install cmake build-essential`
> On Mac: `brew install cmake`
> On Windows: Install Visual Studio C++ build tools first.

### Step 2 — Supabase Setup

1. Go to [supabase.com](https://supabase.com) → New Project
2. Open **SQL Editor** → paste and run `schema.sql`
3. Copy your **Project URL** and **anon key** from Settings → API

### Step 3 — Gmail App Password

1. Go to Google Account → Security → 2-Step Verification (must be ON)
2. Search "App passwords" → create one → copy the 16-character password

### Step 4 — Environment Variables

```bash
cp .env.example .env
# Edit .env with your real values:
```

```env
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=your_anon_key
GMAIL_ADDRESS=youremail@gmail.com
GMAIL_APP_PASSWORD=abcd efgh ijkl mnop
SECRET_KEY=any-random-string-at-least-32-chars
```

### Step 5 — Create Admin Account

```bash
python create_admin.py
# Enter username and password when prompted
```

### Step 6 — Run

```bash
flask run
# Visit: http://localhost:5000
# Admin:  http://localhost:5000/admin/login
```

---

## 🚀 Deploy on Render.com

1. Push code to GitHub
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. Set:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
5. Add all `.env` variables under **Environment**
6. Deploy!

---

## 🎓 Eligibility Logic

| Entry Year | Admission Year | Can Vote In | Last Year |
|---|---|---|---|
| 1st Year (normal) | 2022 | 2022, 2023, 2024 | 2024 |
| 2nd Year (lateral) | 2022 | 2022, 2023 | 2023 |
| 3rd Year (lateral) | 2022 | 2022 only | 2022 |

Formula: `last_eligible = admission_year + (3 - entry_year)`

---

## 🔐 Security

- Passwords hashed with **bcrypt**
- OTP expires after **5 minutes**
- Face verification required before ballot
- Server-side double-check for `has_voted`
- Session cleared after vote submission
