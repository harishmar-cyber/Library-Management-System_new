# Lavender Library Management System (DSA-Powered)

A modern, full-stack Library Management System built with **Python Flask**, **MySQL**, and a responsive **Lavender & White Design System**, deeply integrating core **Data Structures and Algorithms (DSA)** to solve real-world library operations.

---

## 1. Technologies

- **Backend**: Python 3.13+, Flask 3.1+ (Application Factory, Blueprints)
- **Database**: MySQL 8.0 (with automated seamless SQLite dev fallback via PyMySQL)
- **Frontend**: HTML5, Modern CSS3 with Lavender Design System, Vanilla ES6+ JavaScript, HTML5 Canvas Graph Visualizer
- **Testing**: Pytest (26 unit and integration tests)
- **Version Control**: Git & GitHub

---

## 2. Lavender & White Design System

The user interface features a clean, professional aesthetic tailored for administrative workflows:
- **Color Palette**: Primary Lavender (`#7c5cbf`), Deep Violet (`#271e3d`), Soft Lavender Surfaces (`#f1ecfa`, `#f8f6fd`), Clean White (`#ffffff`), and status accents (Emerald, Amber, Rose).
- **Navigation**: Persistent modern sidebar with route indicators and DSA capability pills.
- **Components**: Metric cards with subtle glows, interactive data tables, accessible modals, and toast alerts.
- **Interactive Visualizers**: HTML5 Canvas rendering for book recommendation graphs and dynamic step traces.

---

## 3. Data Structures & Algorithms (DSA) Implementations

Only concepts strictly relevant to Library Management are utilized:

| DSA Concept | Implementation File | Application Purpose | Time Complexity |
|---|---|---|---|
| **Hashing** | `app/dsa/hash_table.py` | Instant lookup of books by Book ID or ISBN via a custom Hash Table with polynomial rolling hash and separate chaining collision resolution. | `O(1)` average lookup, insertion, deletion |
| **Searching** | `app/dsa/search.py` | Linear Search for multi-field and partial text matching (author, category, title); Binary Search on pre-sorted book collections. | `O(n)` Linear, `O(log n)` Binary |
| **Sorting** | `app/dsa/sort.py` | Arrange book catalog by title, author, or publication year using Merge Sort (stable) and Quick Sort (partitioning). | `O(n log n)` |
| **Queue** | `app/dsa/queue.py` | First-In, First-Out (FIFO) linked queue for book reservations, ensuring strict chronological fairness when copies are checked out. | `O(1)` Enqueue & Dequeue |
| **Stack** | `app/dsa/stack.py` | Last-In, First-Out (LIFO) undo stack for reversing librarian actions (undo delete, undo return, undo issues). | `O(1)` Push & Pop |
| **Graph** | `app/dsa/graph.py` | Adjacency List representing books as vertices and relationships (co-borrowed, prerequisite, same genre) as weighted edges. | `O(V + E)` space |
| **BFS & DFS** | `app/dsa/graph.py` | Breadth-First Search (level-by-level queue exploration) and Depth-First Search (deep branch exploration) with real-time traversal animation. | `O(V + E)` time |

---

## 4. System Pages (9 Complete Working GUI Modules)

1. **Login & Authentication** (`/login`): Secure session login with scrypt-hashed passwords.
2. **Dashboard** (`/dashboard`): Real-time metrics on titles, active loans, overdue fines, and DSA engine status.
3. **Books Management** (`/books`): Add, view, edit, delete, search, and sort books with instant O(1) hash table lookup.
4. **Student Directory** (`/students`): Register students, track active loan limits, and manage borrower information.
5. **Issue & Return Circulation** (`/issues`): Issue books with due dates, process returns, calculate late fines ($1.00/day), and trigger reservation notifications.
6. **Book Reservation Queue** (`/reservations`): FIFO waiting list per book with visual linked queue pipeline (Head to Tail) and one-click dequeue.
7. **Recommendation Graph** (`/recommendations`): Interactive HTML5 canvas showing related books with animated BFS and DFS traversals and ranked recommendations.
8. **DSA Demonstration Lab** (`/dsa-lab`): Dedicated computational playground comparing Linear vs Binary Search, Merge vs Quick Sort, Hash Table bucket distributions, and LIFO Stack frames.
9. **Reports & Audit Ledger** (`/reports`): Chronological transaction history with a global "Undo Last Action" button powered by the LIFO Stack.

---

## 5. Project Directory Structure

```text
Library Management System _new/
├── .env.example                       # DB configuration template
├── .gitignore                         # Excludes secrets, caches, virtual environments
├── README.md                          # Full documentation & running guide
├── requirements.txt                   # Flask, PyMySQL, Cryptography, Pytest, python-dotenv
├── run.py                             # Local server startup entry point
├── schema.sql                         # MySQL database schema & initial seed data
├── app/
│   ├── __init__.py                    # Flask application factory
│   ├── config.py                      # Application settings & environment variables
│   ├── db.py                          # MySQL connection manager & SQLite fallback
│   ├── services.py                    # In-memory DSA state registry & transaction recorder
│   ├── dsa/                           # Pure custom Python DSA implementations
│   │   ├── __init__.py
│   │   ├── hash_table.py              # Separate-Chaining Custom Hash Table
│   │   ├── search.py                  # Linear Search & Binary Search with traces
│   │   ├── sort.py                    # Merge Sort & Quick Sort with trace metrics
│   │   ├── queue.py                   # FIFO Reservation Queue
│   │   ├── stack.py                   # LIFO Action Undo Stack
│   │   └── graph.py                   # Adjacency List Graph + BFS & DFS traversals
│   ├── routes/                        # Modular Blueprint controllers
│   │   ├── __init__.py
│   │   ├── auth_routes.py             # Authentication & session controls
│   │   ├── dashboard_routes.py        # Analytics and metric counters
│   │   ├── book_routes.py             # Book catalog, O(1) hash lookup, sorting
│   │   ├── student_routes.py          # Student registration and loans
│   │   ├── issue_routes.py            # Issue, return, and overdue fines
│   │   ├── reservation_routes.py      # FIFO reservation queue operations
│   │   ├── recommendation_routes.py   # Book graph recommendations & BFS/DFS APIs
│   │   ├── dsa_lab_routes.py          # Interactive DSA playground endpoints
│   │   └── report_routes.py           # Audit ledger and Stack undo handler
│   ├── static/
│   │   ├── css/
│   │   │   ├── theme.css              # Lavender design system CSS variables
│   │   │   ├── style.css              # Layout, modern sidebar, tables, cards, modals
│   │   │   └── dsa_lab.css            # DSA Lab styles & bucket grid
│   │   └── js/
│   │       ├── main.js                # Modal handlers, toast alerts, API client
│   │       ├── graph_vis.js           # Interactive HTML5 Canvas graph visualizer
│   │       └── dsa_lab.js             # Sorting and searching interactive runner
│   └── templates/                     # 9 Responsive Jinja2 HTML templates
│       ├── base.html                  # Master layout with sidebar & topbar undo button
│       ├── login.html                 # 1. Login & authentication
│       ├── dashboard.html             # 2. Analytics dashboard
│       ├── books.html                 # 3. Books management
│       ├── students.html              # 4. Student directory
│       ├── issues.html                # 5. Circulation & returns
│       ├── reservations.html          # 6. Reservation FIFO queue
│       ├── recommendations.html       # 7. Recommendation graph (BFS/DFS)
│       ├── dsa_lab.html               # 8. Interactive DSA demonstration lab
│       └── reports.html               # 9. Reports & audit ledger
└── tests/
    ├── __init__.py
    ├── test_dsa.py                    # Comprehensive unit tests for all DSA modules
    └── test_app.py                    # Integration tests for all routes & workflows
```

---

## 6. Installation & Setup Guide

### Step 1: Install Requirements
Open PowerShell in the project directory:
```powershell
pip install -r requirements.txt
```

### Step 2: Configure Environment (Optional for MySQL)
Copy `.env.example` to `.env`:
```powershell
cp .env.example .env
```
Edit `.env` with your MySQL credentials:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=library_management_db
DB_AUTO_FALLBACK=True
```
*Note: If MySQL is offline or not configured yet, the system automatically falls back to an initialized SQLite database (`library.sqlite3`), ensuring the system runs smoothly out of the box.*

### Step 3: MySQL Database Import (If using MySQL)
Run the SQL schema in MySQL Workbench or the MySQL command line:
```powershell
mysql -u root -p < schema.sql
```

### Step 4: Run the Application
Start the Flask development server:
```powershell
python run.py
```
Open your web browser and navigate to:
**`http://127.0.0.1:5000`**

### Step 5: Default Credentials
- **Username**: `admin`
- **Password**: `admin123`

---

## 7. Running the Automated Test Suite

Run the full test suite with pytest:
```powershell
pytest tests/ -v
```
All 26 automated unit and integration tests will execute, validating:
- Custom Hash Table collisions, insertions, deletions, and dynamic resizing
- Linear and Binary search correctness and trace generation
- Merge Sort and Quick Sort algorithms
- FIFO Queue ordering and cancellations
- LIFO Undo Stack operations
- Graph construction, BFS and DFS traversals, and recommendation ranking
- Route authorization, book circulation, and API endpoints
