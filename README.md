# MeetFlow — Minimal & Professional Meeting Reminder Dashboard

A clean, corporate-grade Meeting Reminder System built with **Python 3** and **Django 6**.

---

## 🏛️ Architecture & Clean Design Overview

### 1. Unified Single-Page SaaS Dashboard (`/`)
- Centralized around a single, responsive URL (`/`) with a shared sidebar and instant, zero-reload tab switching via lightweight JavaScript:
  - **Overview**: Summary statistics + concise upcoming schedule preview.
  - **Meeting Authorization**: Dedicated queue for meetings awaiting timing approval.
  - **Accepted Meetings**: High-density table of all timing-authorized meetings.
  - **All Meetings**: Consolidated, searchable list of all records.
  - **Reminder Settings**: User-relevant timing lead times (presets and custom durations).
- Existing direct URLs (`/authorization/`, `/accepted/`, `/meetings/`, `/settings/`) remain fully supported, automatically opening the corresponding dashboard tab.

### 2. Elimination of Redundant Data & Clear Separation of Concerns
- **Overview**: Shows only 4 key metrics and the next 5 upcoming meetings. No duplicated tables.
- **Meeting Authorization**: Contains **only** Pending meetings awaiting decision. Includes one-click **Accept** and **Reject** buttons that update the backend asynchronously and remove the row immediately.
- **Accepted Meetings**: Contains **only** Accepted meetings with full client details (Name, Email, Phone, Date, Time, Status).
- **All Meetings**: Single master table with quick search and status filtering (All, Accepted, Pending, Rejected).
- **Inspection Modal**: Clicking "Details" on any meeting opens a clean, compact modal with full host, client, location, and agenda notes without cluttering the main lists.

### 3. Timing Authorization Protocol
Enforces the 3 business states:
- ⏳ **Pending**: Meetings awaiting timing confirmation. **Must not trigger reminders**; alerts remain on hold.
- ✅ **Accepted**: Timing authorized. System immediately proceeds to background reminder scheduling.
- ❌ **Rejected**: Timing rejected. **Must not trigger reminders**; all scheduled reminders are cancelled immediately.

### 4. Background Reminder Engine
- **No UI Clutter**: Notification channels (WhatsApp, SMS, Email, Google Calendar) operate strictly in the background.
- Background scheduler details, raw channel toggles, and execution logs are hidden from the user interface.
- Reminder timing configuration supports standard presets (`5m`, `10m`, `15m`, `30m`, `1h`, `1d`) and custom durations (`Minutes`, `Hours`, `Days`).

---

## 🛠️ Quickstart Commands

```powershell
# 1. Navigate to the project directory
cd C:\Users\swati\.gemini\antigravity\scratch\meetflow

# 2. Run Database Migrations
python manage.py migrate

# 3. Seed Realistic Database Records
python manage.py seed_meetflow

# 4. Run the Automated Test Suite (All 7 unit tests pass)
python manage.py test

# 5. Start Development Server
python manage.py runserver 127.0.0.1:8000
```

Open **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** in your browser.
