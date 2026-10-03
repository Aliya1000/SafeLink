# SafeLink – Secure Emergency QR Information System 🛡️🚨

**SafeLink** is a full-stack web application designed to save lives by providing instant access to critical medical and emergency contact information via secure QR codes. 

## 📖 Problem Statement
In medical emergencies, every second counts. Often, victims are unconscious or unable to communicate their medical history, allergies, or emergency contacts. Physical ID cards can be lost or outdated. SafeLink solves this by providing a digital, updatable, and secure emergency profile.

## ✨ Key Features
- **Secure Authentication:** User accounts with hashed passwords (PBKDF2).
- **Emergency Profile:** Detailed medical data entry (Blood Group, Allergies, Medications).
- **Privacy Controls:** Users choose which data is public (e.g., hide address, show medications).
- **Dynamic QR Generation:** Secure, token-based QR codes that contain NO personal data.
- **One-Touch Emergency Actions:** Mobile-optimized page with direct "Click-to-Call" buttons.
- **Kill-Switch (Revocation):** Instantly disable a lost or compromised QR code.
- **Smart Regeneration:** Generate a new secure link while invalidating the old one.

## 🛠️ Technology Stack
- **Frontend:** HTML5, CSS3 (Custom + Bootstrap 5), JavaScript.
- **Backend:** Python (Flask).
- **Database:** MongoDB (NoSQL) for flexible medical data storage.
- **Security:** Werkzeug (Password Hashing), Secrets (Token Generation).
- **QR Engine:** Python-QRcode (PIL/Pillow).

## 🔒 Security Architecture
- **Tokenized URLs:** Instead of using Database IDs, we use 32-character cryptographically secure tokens to prevent IDOR attacks.
- **Access Control:** Custom `@login_required` decorators to protect user data.
- **XSS & CSRF Protection:** Flask-driven template escaping and secure cookie configurations.
- **Data Privacy:** Personal Identifiable Information (PII) is never stored directly inside the QR code.

## 🚀 Installation & Local Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/SafeLink.git
   cd SafeLink