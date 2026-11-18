# Cebu Student Hive

**Repository:** `CebuStudentHive-Cabahug-Imee-G01`
**Author:** Imee Cabahug 

Cebu Student Hive is a community platform where Cebu college and university students discover, share, and verify local student discounts, quiet study spots, campus workshops and events, and scholarships. Students confirm each other's posts with votes and comments, and admins review submissions before they appear in the feed.

**Stack:** Django, Bootstrap 5.3 (CDN) with Bootstrap Icons, vanilla JavaScript, Supabase (PostgreSQL).

## Features
- Email-only authentication (`USERNAME_FIELD = 'email'`) with a custom user manager
- Signup, login, and POST-only logout with Bootstrap alerts
- Two roles, `STUDENT` and `ADMIN`, with role-based redirects and a custom `403.html` for blocked access
- Profile page where users edit only their own details
- Student feed with Card/Compact view toggle, instant up/downvotes, and collapsible threaded comments
- Admin dashboard with KPI cards and an approve/reject moderation queue
- Light and dark themes

## Setup

### 1. Install
```bash
git clone <repo-url>
cd CebuStudentHive-Cabahug-Imee-G1
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Supabase database
1. Create a project at <https://supabase.com> and save the database password.
2. Open **Connect** (or **Project Settings → Database**) and copy the **Session pooler** URI.
3. Replace `[YOUR-PASSWORD]` in the URI with your database password.

### 3. Environment variables
```bash
cp .env.example .env
```
Edit `.env` and set `SECRET_KEY` and `DATABASE_URL`.

### 4. Migrate and create an admin
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_hive      # optional: adds sample posts
```

### 5. Run
```bash
python manage.py runserver
```
Open <http://127.0.0.1:8000/>.

## Routes
| Path | Who | Purpose |
|---|---|---|
| `/accounts/signup/`, `/accounts/login/`, `/accounts/logout/` (POST) | everyone | Authentication |
| `/accounts/profile/` | logged in | Edit your own profile |
| `/dashboard/` | STUDENT | Community feed |
| `/dashboard/admin/` | ADMIN | Moderation and analytics |

Sign-ups always create `STUDENT` accounts. Admins are created with `createsuperuser`.