# 🗳️ College Online Voting System

A secure web-based election management platform built using Flask, Supabase, OTP Authentication, and Face Recognition.

The system provides a complete digital voting workflow, including voter registration, identity verification, candidate management, vote casting, election monitoring, and result publication.

---

## 🚀 Overview

College Online Voting System is designed to modernize election processes through a secure and transparent digital platform.

The system combines multi-factor authentication, face recognition technology, and real-time monitoring to ensure election integrity while providing a seamless user experience.

---

## ✨ Features

### User Management

* User Registration
* Profile Photo Upload
* Account Approval Workflow
* User Eligibility Validation
* Session-Based Authentication

### Authentication & Verification

* Email OTP Authentication
* OTP Expiry Validation
* Face Recognition Verification
* Multi-Step Login Process
* Secure Session Management

### Election Management

* Election Scheduling
* Election Activation & Deactivation
* Result Publication Scheduling
* Election Configuration
* Election Monitoring

### Candidate Management

* Candidate Registration
* Position Management
* Candidate Profile Management
* Candidate Updates
* Candidate Reset & Removal

### Voting System

* Secure Online Ballot
* One Vote Per Position
* Vote Confirmation Workflow
* Duplicate Vote Prevention
* Real-Time Vote Tracking

### Administration

* Administrative Dashboard
* User Approval Management
* Candidate Management
* Election Settings Control
* Live Monitoring Tools

### Results & Analytics

* Automated Result Publishing
* Vote Statistics Dashboard
* Turnout Monitoring
* Election Analytics
* Visual Reports

---

## 🔐 Security Features

* bcrypt Password Hashing
* OTP-Based Authentication
* Face Recognition Verification
* Session Protection
* Route-Based Access Control
* Server-Side Validation
* Client-Side Validation
* Duplicate Vote Prevention
* Election Date Validation
* User Eligibility Verification

---

## 🏗️ System Workflow

```text
User Registration
        │
        ▼
Account Approval
        │
        ▼
OTP Authentication
        │
        ▼
Face Verification
        │
        ▼
Voting Dashboard
        │
        ▼
Ballot Submission
        │
        ▼
Vote Storage
        │
        ▼
Results Publication
```

---

## 🛠️ Technology Stack

### Backend

* Python
* Flask
* Supabase SDK
* Gunicorn
* bcrypt

### Frontend

* HTML5
* CSS3
* JavaScript
* Chart.js

### Database

* PostgreSQL (Supabase)

### Authentication

* Email OTP Verification
* Face Recognition

### Computer Vision

* face_recognition
* dlib
* Pillow
* NumPy

### Deployment

* Render
* GitHub

---

## 📂 Project Structure

```text
College_voting_system/
│
├── app.py
├── db.py
├── validators.py
├── face_service.py
├── mail_service.py
├── create_admin.py
├── schema.sql
├── requirements.txt
├── Procfile
├── README.md
│
├── static/
│   ├── css/
│   │   └── style.css
│   │
│   └── js/
│       ├── validation.js
│       ├── webcam.js
│       └── vote.js
│
└── templates/
    ├── signup.html
    ├── login.html
    ├── otp.html
    ├── dashboard.html
    ├── face_verify.html
    ├── ballot.html
    ├── thankyou.html
    ├── results.html
    │
    └── admin/
        ├── login.html
        ├── dashboard.html
        ├── students.html
        ├── candidates.html
        ├── settings.html
        └── monitor.html
```

---

## ⚙️ Installation

### Clone Repository

```bash
git clone https://github.com/nithinr8265/College_voting_system.git

cd College_voting_system
```

### Create Virtual Environment

**Windows**

```bash
python -m venv venv
venv\Scripts\activate
```

**Linux / macOS**

```bash
python3 -m venv venv
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 📦 Environment Configuration

Create a `.env` file:

```env
SUPABASE_URL=
SUPABASE_KEY=
GMAIL_ADDRESS=
GMAIL_APP_PASSWORD=
SECRET_KEY=
```

---

## 🗄️ Database Setup

1. Create a Supabase Project
2. Open SQL Editor
3. Execute `schema.sql`
4. Verify all required tables are created
5. Configure environment variables

Core database entities:

* Users
* Candidates
* Votes
* Election Settings
* Administrators

---

## 👤 Administrator Setup

Create an administrator account:

```bash
python create_admin.py
```

Follow the prompts to configure credentials.

---

## ▶️ Running the Application

Start the application:

```bash
flask run
```

Application URL:

```text
http://localhost:5000
```

Admin Portal:

```text
http://localhost:5000/admin/login
```

---

## 📊 Validation & Integrity Controls

### Client-Side Validation

* Form Validation
* Email Validation
* OTP Validation
* File Validation
* Input Sanitization

### Server-Side Validation

* User Verification
* Vote Verification
* Candidate Validation
* Election Validation
* Duplicate Vote Detection

---

## 🚀 Deployment

### Render Deployment

Build Command:

```bash
pip install -r requirements.txt
```

Start Command:

```bash
gunicorn app:app
```

Deployment Steps:

1. Push source code to GitHub
2. Create a Render Web Service
3. Connect the repository
4. Configure environment variables
5. Deploy

---

## 📈 Future Enhancements

* Multi-Administrator Support
* Audit Logging
* Email Notifications
* SMS Authentication
* Real-Time Notifications
* Mobile Application
* Advanced Analytics Dashboard
* Multi-Election Support
* API Integrations

---

## 📄 License

This project is provided for learning, research, and demonstration purposes.

---

## ⭐ Repository

Repository URL:

https://github.com/nithinr8265/College_voting_system

If you find this project useful, consider giving it a star.
