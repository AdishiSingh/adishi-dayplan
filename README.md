# Adishi's dayplan - Modern Daily Task Planner & Productivity Dashboard

Adishi's dayplan is a sleek, glassmorphic single-page web application designed to help you organize your daily schedule, prioritize your goals, and track your overall productivity. Built with a lightweight **Python Flask** backend, an **SQLite** database, and high-performance **plain vanilla HTML, CSS, and JavaScript**, it represents a modern approach to task management.

---

## 🌟 Features

### 1. Core Task Management (CRUD)
* **Create Tasks**: Quickly add tasks with a title, description, date, and priority level.
* **Auto-Save state**: Checks and status updates are saved instantly to the SQLite database.
* **Dynamic Modals**: Easy-to-use popups for editing existing tasks or verifying actions.
* **Delete Safeguard**: Prompts the user with a confirmation modal before deletion.

### 2. Time-Based Planning
* **Daily Filter**: Separate dashboard focused specifically on today's goals.
* **Timeline Planner**: Plan tasks for future dates and keep tabs on upcoming workloads.
* **Priority Levels**: Flag tasks as **High** 🔴, **Medium** 🟡, or **Low** 🟢 to prioritize your day.

### 3. Productivity Dashboard & Progress Tracking
* **Productivity Pulse**: Hero panel displaying total, completed, pending tasks, and completion percentage.
* **Animated Progress Bars**: Real-time visual updates reflecting your current completion rates.
* **Intelligent Status Messages**: Provides context-aware motivational feedback based on your progress.
* **Priority Distribution**: Quick bars outlining task completions categorized by priority.
* **Upcoming Summary**: Shows dates with pending schedules so you never miss a deadline.

### 4. Interactive UX Boosters
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
├── app.py                  # Main Flask application file (Routing, JSON APIs, and server configuration)
├── requirements.txt        # Backend dependencies list
├── README.md               # Project documentation
│
├── database/
│   ├── db.py               # Database manager (SQLite tables initialization and CRUD helper methods)
│   └── planner.db          # SQLite DB file (Generated dynamically on initial startup)
│
├── templates/
│   └── index.html          # Main HTML5 semantic page template
│
└── static/
    ├── css/
    │   └── style.css       # Complete layout, variable CSS styling, dark/light themes, animations
    └── js/
        └── app.js          # Main client-side script (API requests, state, DOM rendering, events)
```

---

## ⚡ API Endpoint Specification

Adishi's dayplan utilizes an asynchronous RESTful JSON API layer to avoid full-page refreshes:

| Method | Endpoint | Description | Query Parameters |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/tasks` | Retrieve tasks list | `date` (YYYY-MM-DD), `priority`, `completed` (true/false), `search` (keyword) |
| `POST` | `/api/tasks` | Create a new task | *None (Request JSON body)* |
| `PUT` | `/api/tasks/<id>` | Update details / status of a task | *None (Request JSON body)* |
| `DELETE`| `/api/tasks/<id>` | Delete a task | *None* |
| `GET` | `/api/stats` | Retrieve overall task metrics | *None* |
| `GET` | `/api/quote` | Fetch random productivity quote | *None* |

---

## ⚙️ Local Installation & Setup

### Prerequisites
* **Python 3.8+** installed.
* **pip** (Python package installer).

### Step 1: Clone or Open the Project
Open the project root directory in your preferred terminal:
```bash
cd /Users/adishisingh/agy-cli-projects
```

### Step 2: Set Up Virtual Environment (Recommended)
Creating a virtual environment isolates project dependencies:
```bash
# Create a virtual environment named 'venv'
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate
```

### Step 3: Install Required Dependencies
Install the required packages listed in `requirements.txt`:
```bash
pip install -r requirements.txt
```

### Step 4: Run the Application
Start the Flask local development server:
```bash
python3 app.py
```

### Step 5: Access the Application
Open your web browser and navigate to:
**[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🧪 Testing and Verification
The application has been verified for correct operations:
1. **Database initialization**: Tables are generated on initial launch.
2. **Task Creation**: High, medium, and low tasks create correctly.
3. **Filtering & Search**: Dynamic queries filter tasks instantly based on user input.
4. **Completion Rates**: Progress indicators increment and update in real-time.
