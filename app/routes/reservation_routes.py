from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app.routes.auth_routes import login_required
from app.db import db
from app.config import Config
from app.dsa.queue import ReservationQueue
from app.services import reservation_queues, record_transaction

reservation_bp = Blueprint('reservations', __name__)

@reservation_bp.route('/reservations')
@login_required
def index():
    # Fetch all books that have reservations
    reserved_books = db.fetch_all("""
        SELECT DISTINCT b.book_id, b.title, b.isbn, b.available_copies, b.total_copies,
               COUNT(r.reservation_id) as queue_length
        FROM books b
        JOIN reservations r ON b.book_id = r.book_id
        WHERE r.status = 'pending'
        GROUP BY b.book_id
        ORDER BY queue_length DESC
    """)

    # Get reservation queues with student details
    all_reservations = db.fetch_all("""
        SELECT r.*, 
               b.title as book_title, b.isbn, b.available_copies,
               s.full_name as student_name, s.student_number, s.email, s.phone
        FROM reservations r
        JOIN books b ON r.book_id = b.book_id
        JOIN students s ON r.student_id = s.student_id
        WHERE r.status = 'pending'
        ORDER BY r.book_id, r.queue_position ASC, r.reservation_date ASC
    """)

    # Sync and build in-memory queues for all books
    grouped_queues = {}
    for r in all_reservations:
        b_id = r['book_id']
        if b_id not in grouped_queues:
            grouped_queues[b_id] = {
                'book_id': b_id,
                'book_title': r['book_title'],
                'isbn': r['isbn'],
                'available_copies': r['available_copies'],
                'reservations': []
            }
        grouped_queues[b_id]['reservations'].append(r)

    # All books and students for modal
    all_books = db.fetch_all("SELECT book_id, title, isbn, available_copies FROM books ORDER BY title ASC")
    all_students = db.fetch_all("SELECT student_id, full_name, student_number FROM students ORDER BY full_name ASC")

    return render_template(
        'reservations.html',
        active_page='reservations',
        reserved_books=reserved_books,
        grouped_queues=grouped_queues,
        all_reservations=all_reservations,
        books=all_books,
        students=all_students
    )

@reservation_bp.route('/reservations/enqueue', methods=['POST'])
@login_required
def enqueue_reservation():
    book_id = request.form.get('book_id', type=int)
    student_id = request.form.get('student_id', type=int)

    if not book_id or not student_id:
        flash('Please select both book and student.', 'danger')
        return redirect(url_for('reservations.index'))

    # Check if student already has a pending reservation for this book
    existing = db.fetch_one("""
        SELECT * FROM reservations 
        WHERE book_id = %s AND student_id = %s AND status = 'pending'
    """, (book_id, student_id))

    if existing:
        flash('This student already holds a waiting position in the queue for this book.', 'warning')
        return redirect(url_for('reservations.index'))

    # Determine next queue position
    last_pos_res = db.fetch_one("""
        SELECT COALESCE(MAX(queue_position), 0) + 1 AS next_pos 
        FROM reservations 
        WHERE book_id = %s AND status = 'pending'
    """, (book_id,))
    next_pos = last_pos_res['next_pos'] if last_pos_res else 1

    try:
        res_id = db.execute_query("""
            INSERT INTO reservations (book_id, student_id, queue_position, status)
            VALUES (%s, %s, %s, 'pending')
        """, (book_id, student_id, next_pos))

        student = db.fetch_one("SELECT full_name, student_number FROM students WHERE student_id = %s", (student_id,))
        book = db.fetch_one("SELECT title FROM books WHERE book_id = %s", (book_id,))

        # Update in-memory queue
        if book_id not in reservation_queues:
            reservation_queues[book_id] = ReservationQueue(book_id=book_id)

        queue_item = {
            'reservation_id': res_id,
            'book_id': book_id,
            'student_id': student_id,
            'student_name': student['full_name'],
            'queue_position': next_pos
        }
        reservation_queues[book_id].enqueue(queue_item)

        # Record on Undo Stack
        record_transaction('enqueue_reservation', 'reservation', res_id, queue_item, session.get('user_id'))

        flash(f"Student '{student['full_name']}' successfully placed in FIFO Queue at position #{next_pos} for '{book['title']}'.", 'success')
    except Exception as e:
        flash(f"Error adding to reservation queue: {e}", 'danger')

    return redirect(url_for('reservations.index'))

@reservation_bp.route('/reservations/dequeue/<int:book_id>', methods=['POST'])
@login_required
def dequeue_reservation(book_id):
    """
    Serves the earliest student at head of the queue (FIFO) and fulfills their reservation.
    """
    earliest = db.fetch_one("""
        SELECT r.*, s.full_name as student_name, b.title as book_title
        FROM reservations r
        JOIN students s ON r.student_id = s.student_id
        JOIN books b ON r.book_id = b.book_id
        WHERE r.book_id = %s AND r.status = 'pending'
        ORDER BY r.queue_position ASC, r.reservation_date ASC
        LIMIT 1
    """, (book_id,))

    if not earliest:
        flash('No pending reservations in queue for this book.', 'warning')
        return redirect(url_for('reservations.index'))

    try:
        # Mark reservation fulfilled
        db.execute_query("""
            UPDATE reservations 
            SET status = 'fulfilled' 
            WHERE reservation_id = %s
        """, (earliest['reservation_id'],))

        # Reindex remaining positions for this book: decrement queue_position by 1
        db.execute_query("""
            UPDATE reservations 
            SET queue_position = queue_position - 1 
            WHERE book_id = %s AND status = 'pending' AND queue_position > %s
        """, (book_id, earliest['queue_position']))

        # Update in-memory FIFO queue
        if book_id in reservation_queues:
            reservation_queues[book_id].dequeue()

        # Record on Undo Stack
        record_transaction('dequeue_reservation', 'reservation', earliest['reservation_id'], earliest, session.get('user_id'))

        flash(f"Served FIFO Head: Reservation fulfilled for '{earliest['student_name']}' on '{earliest['book_title']}'!", 'success')
    except Exception as e:
        flash(f"Error fulfilling reservation: {e}", 'danger')

    return redirect(url_for('reservations.index'))

@reservation_bp.route('/reservations/cancel/<int:reservation_id>', methods=['POST'])
@login_required
def cancel_reservation(reservation_id):
    res = db.fetch_one("SELECT * FROM reservations WHERE reservation_id = %s", (reservation_id,))
    if not res:
        flash('Reservation not found.', 'danger')
        return redirect(url_for('reservations.index'))

    try:
        db.execute_query("UPDATE reservations SET status = 'cancelled' WHERE reservation_id = %s", (reservation_id,))

        # Decrement position of subsequent items in queue
        db.execute_query("""
            UPDATE reservations 
            SET queue_position = queue_position - 1 
            WHERE book_id = %s AND status = 'pending' AND queue_position > %s
        """, (res['book_id'], res['queue_position']))

        if res['book_id'] in reservation_queues:
            reservation_queues[res['book_id']].remove_by_reservation_id(reservation_id)

        record_transaction('cancel_reservation', 'reservation', reservation_id, res, session.get('user_id'))
        flash('Reservation cancelled and subsequent queue positions shifted forward.', 'info')
    except Exception as e:
        flash(f"Error cancelling reservation: {e}", 'danger')

    return redirect(url_for('reservations.index'))
