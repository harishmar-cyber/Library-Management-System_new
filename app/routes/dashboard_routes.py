from flask import Blueprint, render_template
from app.routes.auth_routes import login_required
from app.db import db

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    # Fetch statistical metrics from database
    total_books_res = db.fetch_one("SELECT COUNT(*) AS count, COALESCE(SUM(total_copies), 0) AS total_copies, COALESCE(SUM(available_copies), 0) AS available_copies FROM books")
    total_students_res = db.fetch_one("SELECT COUNT(*) AS count FROM students")
    active_issues_res = db.fetch_one("SELECT COUNT(*) AS count FROM book_issues WHERE status = 'issued'")
    overdue_issues_res = db.fetch_one("SELECT COUNT(*) AS count, COALESCE(SUM(fine_amount), 0) AS total_fines FROM book_issues WHERE status = 'overdue'")
    pending_reservations_res = db.fetch_one("SELECT COUNT(*) AS count FROM reservations WHERE status = 'pending'")
    
    # Recent Transactions / Activity
    recent_transactions = db.fetch_all("""
        SELECT t.*, u.full_name as user_name 
        FROM transactions t 
        LEFT JOIN users u ON t.user_id = u.user_id 
        ORDER BY t.timestamp DESC 
        LIMIT 6
    """)

    # Recent Issues
    recent_issues = db.fetch_all("""
        SELECT i.*, b.title as book_title, s.full_name as student_name, s.student_number 
        FROM book_issues i
        JOIN books b ON i.book_id = b.book_id
        JOIN students s ON i.student_id = s.student_id
        ORDER BY i.issue_id DESC
        LIMIT 5
    """)

    # Top Recommended Connected Books (Graph degree count)
    graph_stats = db.fetch_one("SELECT COUNT(*) as edge_count FROM book_relations")

    metrics = {
        'total_books': total_books_res['count'] if total_books_res else 0,
        'total_copies': total_books_res['total_copies'] if total_books_res else 0,
        'available_copies': total_books_res['available_copies'] if total_books_res else 0,
        'total_students': total_students_res['count'] if total_students_res else 0,
        'active_issues': active_issues_res['count'] if active_issues_res else 0,
        'overdue_issues': overdue_issues_res['count'] if overdue_issues_res else 0,
        'total_fines': overdue_issues_res['total_fines'] if overdue_issues_res else 0.0,
        'pending_reservations': pending_reservations_res['count'] if pending_reservations_res else 0,
        'graph_edges': graph_stats['edge_count'] if graph_stats else 0
    }

    return render_template('dashboard.html', active_page='dashboard', metrics=metrics, recent_issues=recent_issues, recent_transactions=recent_transactions)
