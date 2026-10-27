import json
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session
from app.routes.auth_routes import login_required
from app.db import db
from app.services import (
    undo_stack, 
    book_isbn_hash_table, 
    book_id_hash_table, 
    book_graph, 
    reservation_queues
)

report_bp = Blueprint('reports', __name__)

@report_bp.route('/reports')
@login_required
def index():
    # Audit log
    transactions = db.fetch_all("""
        SELECT t.*, u.full_name as user_name 
        FROM transactions t
        LEFT JOIN users u ON t.user_id = u.user_id
        ORDER BY t.transaction_id DESC
    """)

    # Circulation summary
    circ_summary = db.fetch_one("""
        SELECT 
            COUNT(CASE WHEN status = 'issued' THEN 1 END) as active_loans,
            COUNT(CASE WHEN status = 'overdue' THEN 1 END) as overdue_loans,
            COUNT(CASE WHEN status = 'returned' THEN 1 END) as returned_loans,
            COALESCE(SUM(fine_amount), 0) as total_fines
        FROM book_issues
    """)

    # Category breakdown
    category_stats = db.fetch_all("""
        SELECT category, COUNT(*) as book_count, SUM(total_copies) as total_copies
        FROM books
        GROUP BY category
        ORDER BY book_count DESC
    """)

    return render_template(
        'reports.html',
        active_page='reports',
        transactions=transactions,
        circ_summary=circ_summary,
        category_stats=category_stats,
        stack_size=undo_stack.size()
    )

@report_bp.route('/api/undo', methods=['POST'])
@login_required
def api_undo_action():
    """
    Pops the latest action from LIFO undo stack and applies reversing logic.
    """
    if undo_stack.is_empty():
        return jsonify({'success': False, 'message': 'Undo Stack is empty. No reversible actions remaining.'})

    action = undo_stack.pop()
    tx_id = action.get('transaction_id')
    action_type = action.get('action_type')
    entity_id = action.get('entity_id')
    details = action.get('details') or {}

    try:
        if action_type == 'add_book':
            # Reverse: Delete the book that was added
            book = db.fetch_one("SELECT * FROM books WHERE book_id = %s", (entity_id,))
            if book:
                db.execute_query("DELETE FROM books WHERE book_id = %s", (entity_id,))
                book_isbn_hash_table.remove(book['isbn'])
                book_id_hash_table.remove(str(entity_id))
            msg = f"Undid: Added book #{entity_id} was removed from catalog."

        elif action_type == 'delete_book':
            # Reverse: Re-insert the book that was deleted
            b = details.get('deleted_book', {})
            if b:
                new_id = db.execute_query("""
                    INSERT INTO books (book_id, isbn, title, author, category, publication_year, total_copies, available_copies, shelf_location)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (b['book_id'], b['isbn'], b['title'], b['author'], b['category'], b['publication_year'], b['total_copies'], b['available_copies'], b['shelf_location']))
                book_isbn_hash_table.put(b['isbn'], b)
                book_id_hash_table.put(str(b['book_id']), b)
                book_graph.add_vertex(b['book_id'], b)
            msg = f"Undid: Deleted book '{b.get('title')}' was restored to catalog."

        elif action_type == 'edit_book':
            # Reverse: Restore previous values
            prev = details.get('previous', {})
            if prev:
                db.execute_query("""
                    UPDATE books 
                    SET title=%s, author=%s, category=%s, publication_year=%s, total_copies=%s, available_copies=%s, shelf_location=%s
                    WHERE book_id=%s
                """, (prev['title'], prev['author'], prev['category'], prev['publication_year'], prev['total_copies'], prev['available_copies'], prev['shelf_location'], entity_id))
                book_isbn_hash_table.put(prev['isbn'], prev)
            msg = f"Undid: Edit changes reverted for book #{entity_id}."

        elif action_type == 'issue_book':
            # Reverse: Cancel the issue record and increment available copies back
            db.execute_query("DELETE FROM book_issues WHERE issue_id = %s", (entity_id,))
            b_id = details.get('book_id')
            if b_id:
                db.execute_query("UPDATE books SET available_copies = available_copies + 1 WHERE book_id = %s", (b_id,))
                book = db.fetch_one("SELECT * FROM books WHERE book_id = %s", (b_id,))
                if book:
                    book_isbn_hash_table.put(book['isbn'], book)
            msg = f"Undid: Loan #{entity_id} reversed and book returned to inventory."

        elif action_type == 'return_book':
            # Reverse: Reopen loan and decrement available copies back
            prev_status = details.get('previous_status', 'issued')
            db.execute_query("UPDATE book_issues SET status = %s, return_date = NULL, fine_amount = 0.00 WHERE issue_id = %s", (prev_status, entity_id))
            b_id = details.get('book_id')
            if b_id:
                db.execute_query("UPDATE books SET available_copies = available_copies - 1 WHERE book_id = %s", (b_id,))
            msg = f"Undid: Return action undone. Loan #{entity_id} restored to active status."

        elif action_type == 'enqueue_reservation':
            # Reverse: Cancel reservation
            db.execute_query("UPDATE reservations SET status = 'cancelled' WHERE reservation_id = %s", (entity_id,))
            b_id = details.get('book_id')
            if b_id in reservation_queues:
                reservation_queues[b_id].remove_by_reservation_id(entity_id)
            msg = f"Undid: Reservation #{entity_id} removed from FIFO Queue."

        else:
            msg = f"Undid transaction #{tx_id} ({action_type})."

        # Mark transaction undone in database
        if tx_id:
            db.execute_query("UPDATE transactions SET undone = 1 WHERE transaction_id = %s", (tx_id,))

        return jsonify({'success': True, 'message': msg})

    except Exception as e:
        return jsonify({'success': False, 'message': f"Error performing undo: {e}"})
