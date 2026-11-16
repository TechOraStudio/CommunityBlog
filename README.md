# CommunityBlog

A moderated community blog website where learners and developers share tutorials, study notes, and technical articles.

---

## 🎯 Key Concept & Workflow
Unlike traditional open blogs where spam and unchecked content proliferate, **CommunityBlog** enforces a quality-moderated publishing workflow:
1. **Drafting**: Authors write tutorials in Markdown and save them as Drafts.
2. **Review Queue**: Submitting a post marks it as **Pending Review**.
3. **Admin Moderation**:
   - **Approve**: Post becomes immediately public.
   - **Reject**: Admin provides mandatory feedback (`BR-5`). The author can edit the rejected post and resubmit it.
4. **Post-Approval Edits**: If an author edits an already approved post, it remains public but is flagged in the **Recently Edited** queue and admin audit log to catch covert spam.

---

## 🛠️ Tech Stack
- **Framework**: Django 6.1
- **Language**: Python 3.15
- **Database**: SQLite (Local Development) / PostgreSQL (Production)
- **Frontend**: Responsive HTML5 + CSS3 (Server-rendered website)
- **Security & Markdown**: `markdown` + `nh3` (XSS sanitization), Django password hashing & CSRF protection

---

## 🚀 Getting Started

### 1. Activate Virtual Environment
```powershell
.\venv\Scripts\Activate.ps1
```

### 2. Apply Database Migrations
```powershell
python manage.py migrate
```

### 3. Create a Moderator / Admin Account
```powershell
python manage.py createsuperuser
```
*(Admins have access to both `/moderation/` and the Django admin panel at `/admin/`)*

### 4. Run Development Server
```powershell
python manage.py runserver
```
Visit **http://127.0.0.1:8000/** in your browser.

### 5. Configure Verification Email
Without SMTP settings, local development automatically verifies accounts so you can sign in. To require email verification and deliver links to inboxes, copy `.env.example` to `.env` and set your email provider's SMTP values. For Gmail, use a Google App Password (not your account password). Never commit `.env`.

```powershell
Copy-Item .env.example .env
```

Restart the server after editing `.env`. Existing unverified accounts can request a new link from **Resend verification email** on the sign-in page.

---

## 🧪 Running Automated Tests
The project includes a 17-test automated verification suite covering:
- Email verification & duplicate checks
- Password hashing & login authentication
- Post lifecycle (Draft $\rightarrow$ Pending $\rightarrow$ Approved / Rejected)
- Cross-user permission boundaries
- XSS prevention on Markdown rendering
- Account deletion cascades

To run the tests:
```powershell
python manage.py test apps
```
