# Adishi's dayplan - Modern Daily Task Planner & Productivity Dashboard

Adishi's dayplan is a sleek, glassmorphic single-page web application designed to help you organize your daily schedule, prioritize your goals, and track your overall productivity. Built with a lightweight **Python Flask** backend, a dual-engine **PostgreSQL / SQLite** database system, and high-performance **plain vanilla HTML, CSS, and JavaScript**, it represents a modern approach to task management.

---

## 🌟 Features

### 1. Core Task Management (CRUD)
* **Create Tasks**: Quickly add tasks with a title, description, date, and priority level.
* **Auto-Save state**: Checks and status updates are saved instantly to the database.
* **Dynamic Modals**: Easy-to-use popups for editing existing tasks or verifying actions.
* **Delete Safeguard**: Prompts the user with a confirmation modal before deletion.

### 2. Security & User Accounts
* **Registration & Login**: Secure user registration and login workflows.
* **Password Hashing**: Cryptographically secure hashing using Werkzeug security handlers.
* **Access Control**: Scopes all database queries (tasks and statistics) by the authenticated session's `user_id`.

### 3. Time-Based Planning
* **Daily Filter**: Separate dashboard focused specifically on today's goals.
* **Timeline Planner**: Plan tasks for future dates and keep tabs on upcoming workloads.
* **Priority Levels**: Flag tasks as **High** 🔴, **Medium** 🟡, or **Low** 🟢 to prioritize your day.

### 4. Productivity Dashboard & Progress Tracking
* **Productivity Pulse**: Hero panel displaying total, completed, pending tasks, and completion percentage.
* **Animated Progress Bars**: Real-time visual updates reflecting your current completion rates.
* **Intelligent Status Messages**: Provides context-aware motivational feedback based on your progress.
* **Priority Distribution**: Quick bars outlining task completions categorized by priority.
* **Upcoming Summary**: Shows dates with pending schedules so you never miss a deadline.

### 5. Interactive UX Boosters
* **Power Search**: Instant search matching keywords inside task titles and descriptions.
* **Advanced Filters**: Filter and drill down by Priority, Status (Pending vs. Completed), and Specific Dates.
* **Dark Mode**: Sleek dark theme toggle using CSS variables and persistence in `localStorage`.
* **Daily Motivation**: A randomized list of productivity quotes curated to keep you inspired.
* **Fully Responsive**: Highly optimized experience across mobile devices, tablets, and desktops.

---

## 🏗️ Project Structure

```text
agy-cli-projects/
│
├── app.py                  # Main Flask application file (Routing, Auth, JSON APIs, and server configuration)
├── requirements.txt        # Backend dependencies list (Includes gunicorn and psycopg2-binary)
├── render.yaml             # Render Blueprint configuration file (Database and Web App declaration)
├── README.md               # Project documentation
│
├── database/
│   ├── db.py               # Database router (PostgreSQL/SQLite dual-engine, query mapping)
│   └── planner.db          # SQLite DB file (Generated dynamically as local development fallback)
│
├── templates/
│   ├── index.html          # Main HTML5 task planner workspace template
│   ├── login.html          # Auth login view template
│   └── register.html       # Auth registration view template
│
└── static/
    ├── css/
    │   └── style.css       # Complete layout, HSL variables, dark/light themes, animations
    └── js/
        └── app.js          # Main client-side script (API requests, state, DOM rendering, events)
```

---

## ⚡ API Endpoint Specification

All core transactions run asynchronously using RESTful JSON API layers:

| Method | Endpoint | Description | Access Control |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/tasks` | Retrieve tasks list | Session Required (scoped by user ID) |
| `POST` | `/api/tasks` | Create a new task | Session Required (scoped by user ID) |
| `PUT` | `/api/tasks/<id>` | Update details / status of a task | Session Required (scoped by user ID) |
| `DELETE`| `/api/tasks/<id>` | Delete a task | Session Required (scoped by user ID) |
| `GET` | `/api/stats` | Retrieve overall task metrics | Session Required (scoped by user ID) |
| `GET` | `/api/quote` | Fetch random productivity quote | Public |

---

## 💾 Dual-Engine Database Support (Production-Ready)
To support both seamless local development and production cloud deployment, the app contains an intelligent database engine switcher:
* **Production Mode (Render)**: Connects to a robust **PostgreSQL** database if the `DATABASE_URL` environment variable is detected.
* **Development Mode (Local)**: Falls back to a local **SQLite** database file (`database/planner.db`) if `DATABASE_URL` is empty, allowing you to run, edit, and test code locally without any Postgres setup!

---

## 🚀 Deployment to Render (Step-by-Step)

The project includes a Render Blueprint config ([render.yaml](file:///Users/adishisingh/agy-cli-projects/render.yaml)) which automatically provisions a PostgreSQL database and sets up the Flask server with Gunicorn.

### Deployment Steps:
1. Push all your code to your GitHub repository (e.g. `https://github.com/AdishiSingh/adishi-dayplan`).
2. Sign in to your **[Render Dashboard](https://dashboard.render.com/)**.
3. Click **New** (top-right button) and select **Blueprint**.
4. Connect your GitHub account and select your repository **adishi-dayplan**.
5. Render will automatically read the [render.yaml](file:///Users/adishisingh/agy-cli-projects/render.yaml) file and setup:
   * A managed **PostgreSQL Database** (`dayplan-db`).
   * A **Python Web Service** running Gunicorn.
   * Auto-generated, secure session `SECRET_KEY` environment values.
   * Direct connection link mapping `DATABASE_URL` between the database and the Web Service.
6. Click **Approve** on the Render dashboard, and the project will compile and deploy automatically!

---

## ⚙️ Local Installation & Setup

### Prerequisites
* **Python 3.8+** installed.
* **pip** (Python package installer).

### Step 1: Clone or Open the Project
```bash
cd /Users/adishisingh/agy-cli-projects
```

### Step 2: Set Up Virtual Environment (Recommended)
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run the Application
```bash
python3 app.py
```
*Locally, it will default to SQLite mode. Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** to plan.*

---

## 🧪 Testing and Verification
Run the automated testing suite locally:
```bash
python3 test_suite.py
```
*Runs all 6 testing assertions locally, verifying logins, database queries, and productivity analytics.*
