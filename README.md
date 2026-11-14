# Cebu Student Hive

**Repository:** `CebuStudentHive-Cabahug-Imee-G1`
**Author:** Imee Cabahug (Group 1)

A Reddit-style platform where Cebu college and university students discover, submit, and peer-verify student discounts, quiet study spots, campus workshops/events, and scholarships. Admins moderate submissions.

**Stack:** Django, Bootstrap 5.3 (CDN) with Bootstrap Icons, vanilla JavaScript, Supabase (PostgreSQL). No React, Vue, Tailwind, HTMX, or Alpine.

## Features
- Email-only login (`USERNAME_FIELD = 'email'`, no username), custom `CustomUserManager`
- Signup, login, and POST-only logout with Bootstrap alerts
- Roles `STUDENT` and `ADMIN`, role-based redirect after login, strict role guards with a custom `403.html`
- Profile page (`UpdateView`, `get_object()` returns `request.user`)
- Student feed with Card/Compact toggle, optimistic up/downvotes (saved to the server), collapsible threaded comments
- Admin dashboard with KPI cards and an approve/reject queue
- Light/dark theme (`data-bs-theme`), remembered in the browser

## Setup

### 1. Clone and install
```bash
git clone <your-repo-url> CebuStudentHive-Cabahug-Imee-G1
cd CebuStudentHive-Cabahug-Imee-G1
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Create the Supabase database
1. Create a project at <https://supabase.com> and save the database password.
2. Open **Project Settings → Database → Connection string** and copy the **URI** (the session pooler URI works on IPv4 networks).
3. Replace `[YOUR-PASSWORD]` in it with your database password. URL-encode special characters.

### 3. Configure `.env`
```bash
cp .env.example .env
```
Set `SECRET_KEY` and `DATABASE_URL`. Generate a key with:
```bash
python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

### 4. Migrate
```bash
python manage.py makemigrations accounts dashboard   # skip if a migrations/ folder already exists
python manage.py migrate
python manage.py createsuperuser                      # email + password; role is set to ADMIN
python manage.py seed_hive                            # optional: demo student and sample posts
```

### 5. Run
```bash
python manage.py runserver
```
Open <http://127.0.0.1:8000/>. Run tests with `python manage.py test` (it needs a database your `DATABASE_URL` user can create test databases in).

## Routes
| Path | Who | Purpose |
|---|---|---|
| `/accounts/signup/`, `/accounts/login/`, `/accounts/logout/` (POST) | everyone | Authentication |
| `/accounts/profile/` | logged in | Edit your own profile |
| `/dashboard/` | STUDENT | Community feed |
| `/dashboard/admin/` | ADMIN | Moderation and analytics |
| `/django-admin/` | staff | Django admin |

## Notes
- Public sign-up always creates `STUDENT` accounts. Create admins with `createsuperuser` or by changing a user's role in `/django-admin/`.
- Profile photos are saved to the local `media/` folder. Use Supabase Storage or another object store when deploying.
- The custom 404 page renders when `DEBUG=False`.
- The seeded demo account is for development only. Delete it before deploying.
