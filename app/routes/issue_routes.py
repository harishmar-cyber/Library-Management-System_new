from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime, date, timedelta
from app.routes.auth_routes import login_required
from app.db import db
from app.config import Config
from app.services import (
    book_isbn_hash_table, 
    book_id_hash_table, 
    reservation_queues, 
    record_transaction
)

issue_bp = Blueprint('issues', __name__)

@issue_bp.route('/issues')
@login_required
def index():
    status_filter = request.args.get('status', 'all')
    search_q = request.args.get('q', '').strip()

    # Automatically recalculate overdue status and fines for today
    today = date.today()
    active_issues = db.fetch_all("SELECT issue_id, due_date FROM book_issues WHERE status IN ('issued', 'overdue')")
    for row in active_issues:
        try:
            due = datetime.strptime(str(row['due_date']), '%Y-%m-%d').date()
            if today > due:
                overdue_days = (today - due).days
                fine = round(overdue_days * Config.FINE_PER_DAY, 2)
                db.execute_query("""
                    UPDATE book_issues
                    SET status = 'overdue', fine_amount = %s
                    WHERE issue_id = %s
                """, (fine, row['issue_id']))
        except Exception:
            pass

    query = """
        SELECT i.*, 
               b.title as book_title, b.isbn, b.available_copies,
               s.full_name as student_name, s.student_number
        FROM book_issues i
        JOIN books b ON i.book_id = b.book_id
        JOIN students s ON i.student_id = s.student_id
        WHERE 1=1
    """
    params = []

    if status_filter != 'all':
        query += " AND i.status = %s"
        params.append(status_filter)

    if search_q:
        query += " AND (b.title LIKE %s OR s.full_name LIKE %s OR s.student_number LIKE %s OR b.isbn LIKE %s)"
        like_q = f"%{search_q}%"
        params.extend([like_q, like_q, like_q, like_q])

    query += " ORDER BY i.issue_id DESC"
    issues = db.fetch_all(query, tuple(params))

    # Books and students for the issue form
    available_books = db.fetch_all("SELECT book_id, title, isbn, available_copies FROM books WHERE available_copies > 0 ORDER BY title ASC")
    all_students = db.fetch_all("SELECT student_id, full_name, student_number FROM students ORDER BY full_name ASC")

    return render_template(
        'issues.html',
        active_page='issues',
        issues=issues,
        available_books=available_books,
        students=all_students,
        status_filter=status_filter,
        search_q=search_q
    )

@issue_bp.route('/issues/issue', methods=['POST'])
@login_required
def issue_book():
    book_id = request.form.get('book_id', type=int)
    student_id = request.form.get('student_id', type=int)
    loan_days = request.form.get('loan_days', Config.LOAN_PERIOD_DAYS, type=int)

    if not book_id or not student_id:
        flash('Please select both a valid Book and a Student.', 'danger')
        return redirect(url_for('issues.index'))

    # Check available copies
    book = db.fetch_one("SELECT * FROM books WHERE book_id = %s", (book_id,))
    if not book or book['available_copies'] <= 0:
        flash('This book is currently out of stock. You can place a reservation in the Reservation Queue.', 'warning')
        return redirect(url_for('issues.index'))

    # Check student active loan limit
    active_count = db.fetch_one("SELECT COUNT(*) as count FROM book_issues WHERE student_id = %s AND status IN ('issued', 'overdue')", (student_id,))
    if active_count and active_count['count'] >= Config.MAX_BOOKS_PER_STUDENT:
        flash(f"Student has reached the maximum borrowing limit of {Config.MAX_BOOKS_PER_STUDENT} books.", 'warning')
        return redirect(url_for('issues.index'))

    issue_date = date.today()
    due_date = issue_date + timedelta(days=loan_days)

    try:
        # Create issue record
        issue_id = db.execute_query("""
            INSERT INTO book_issues (book_id, student_id, issue_date, due_date, status, fine_amount)
            VALUES (%s, %s, %s, %s, 'issued', 0.00)
        """, (book_id, student_id, issue_date.isoformat(), due_date.isoformat()))

        # Decrement available copies
        db.execute_query("UPDATE books SET available_copies = available_copies - 1 WHERE book_id = %s", (book_id,))

        # Update in-memory hash table
        cached_book = book_isbn_hash_table.get(book['isbn'])
        if cached_book:
            cached_book['available_copies'] -= 1

        # Record on Undo Stack
        tx_data = {
            'issue_id': issue_id,
            'book_id': book_id,
            'student_id': student_id,
            'book_title': book['title']
        }
        record_transaction('issue_book', 'book_issue', issue_id, tx_data, session.get('user_id'))

        flash(f"'{book['title']}' successfully issued! Due date: {due_date.isoformat()}.", 'success')
    except Exception as e:
        flash(f"Error issuing book: {e}", 'danger')

    return redirect(url_for('issues.index'))

@issue_bp.route('/issues/return/<int:issue_id>', methods=['POST'])
@login_required
def return_book(issue_id):
    issue = db.fetch_one("SELECT * FROM book_issues WHERE issue_id = %s", (issue_id,))
    if not issue or issue['status'] == 'returned':
        flash('Issue record is invalid or already returned.', 'warning')
        return redirect(url_for('issues.index'))

    book_id = issue['book_id']
    return_date = date.today()
    due_date = datetime.strptime(str(issue['due_date']), '%Y-%m-%d').date()

    # Calculate fine if overdue
    fine = 0.00
    if return_date > due_date:
        days_overdue = (return_date - due_date).days
        fine = round(days_overdue * Config.FINE_PER_DAY, 2)

    try:
        # Update issue record to returned
        db.execute_query("""
            UPDATE book_issues 
            SET return_date = %s, status = 'returned', fine_amount = %s
            WHERE issue_id = %s
        """, (return_date.isoformat(), fine, issue_id))

        # Increment available copies
        db.execute_query("UPDATE books SET available_copies = available_copies + 1 WHERE book_id = %s", (book_id,))

        book = db.fetch_one("SELECT * FROM books WHERE book_id = %s", (book_id,))
        cached_book = book_isbn_hash_table.get(book['isbn'])
        if cached_book:
            cached_book['available_copies'] += 1

        # Check FIFO Reservation Queue for this book
        queue = reservation_queues.get(book_id)
        queue_msg = ""
        if queue and not queue.is_empty():
            next_reservation = queue.peek()
            queue_msg = f" Notice: Reservation Queue has student '{next_reservation.get('student_name')}' waiting for this book!"

        # Record on Undo Stack
        tx_data = {
            'issue_id': issue_id,
            'book_id': book_id,
            'previous_status': issue['status'],
            'fine_charged': fine
        }
        record_transaction('return_book', 'book_issue', issue_id, tx_data, session.get('user_id'))

        flash(f"Book returned successfully!{' Fine applied: $' + str(fine) if fine > 0 else ''}.{queue_msg}", 'success')
    except Exception as e:
        flash(f"Error returning book: {e}", 'danger')

    return redirect(url_for('issues.index'))
