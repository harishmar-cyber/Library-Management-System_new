from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.routes.auth_routes import login_required
from app.db import db
from app.services import record_transaction

student_bp = Blueprint('students', __name__)

@student_bp.route('/students')
@login_required
def index():
    search_q = request.args.get('q', '').strip()

    if search_q:
        students = db.fetch_all("""
            SELECT s.*, 
                   COUNT(CASE WHEN bi.status = 'issued' THEN 1 END) as active_loans_count
            FROM students s
            LEFT JOIN book_issues bi ON s.student_id = bi.student_id
            WHERE s.full_name LIKE %s OR s.student_number LIKE %s OR s.department LIKE %s
            GROUP BY s.student_id
            ORDER BY s.student_id DESC
        """, (f"%{search_q}%", f"%{search_q}%", f"%{search_q}%"))
    else:
        students = db.fetch_all("""
            SELECT s.*, 
                   COUNT(CASE WHEN bi.status = 'issued' THEN 1 END) as active_loans_count
            FROM students s
            LEFT JOIN book_issues bi ON s.student_id = bi.student_id
            GROUP BY s.student_id
            ORDER BY s.student_id DESC
        """)

    return render_template('students.html', active_page='students', students=students, search_q=search_q)

@student_bp.route('/students/add', methods=['POST'])
@login_required
def add_student():
    student_num = request.form.get('student_number', '').strip().upper()
    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    department = request.form.get('department', '').strip()

    if not student_num or not full_name or not email:
        flash('Student Number, Full Name, and Email are mandatory.', 'danger')
        return redirect(url_for('students.index'))

    # Check duplicates
    existing = db.fetch_one("SELECT * FROM students WHERE student_number = %s OR email = %s", (student_num, email))
    if existing:
        flash('A student with this Student Number or Email already exists.', 'warning')
        return redirect(url_for('students.index'))

    try:
        student_id = db.execute_query("""
            INSERT INTO students (student_number, full_name, email, phone, department)
            VALUES (%s, %s, %s, %s, %s)
        """, (student_num, full_name, email, phone, department))

        student_data = {
            'student_id': student_id,
            'student_number': student_num,
            'full_name': full_name,
            'email': email,
            'phone': phone,
            'department': department
        }

        record_transaction('add_student', 'student', student_id, student_data, session.get('user_id'))
        flash(f"Student '{full_name}' ({student_num}) registered successfully.", 'success')
    except Exception as e:
        flash(f"Error registering student: {e}", 'danger')

    return redirect(url_for('students.index'))

@student_bp.route('/students/edit/<int:student_id>', methods=['POST'])
@login_required
def edit_student(student_id):
    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    department = request.form.get('department', '').strip()

    old_student = db.fetch_one("SELECT * FROM students WHERE student_id = %s", (student_id,))
    if not old_student:
        flash('Student not found.', 'danger')
        return redirect(url_for('students.index'))

    try:
        db.execute_query("""
            UPDATE students 
            SET full_name = %s, email = %s, phone = %s, department = %s
            WHERE student_id = %s
        """, (full_name, email, phone, department, student_id))

        record_transaction('edit_student', 'student', student_id, {'previous': old_student, 'new_name': full_name}, session.get('user_id'))
        flash(f"Student '{full_name}' updated successfully.", 'success')
    except Exception as e:
        flash(f"Error updating student: {e}", 'danger')

    return redirect(url_for('students.index'))

@student_bp.route('/students/delete/<int:student_id>', methods=['POST'])
@login_required
def delete_student(student_id):
    student = db.fetch_one("SELECT * FROM students WHERE student_id = %s", (student_id,))
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('students.index'))

    # Check active loans
    active_loans = db.fetch_one("SELECT COUNT(*) as count FROM book_issues WHERE student_id = %s AND status = 'issued'", (student_id,))
    if active_loans and active_loans['count'] > 0:
        flash(f"Cannot delete student with {active_loans['count']} actively issued books.", 'warning')
        return redirect(url_for('students.index'))

    try:
        db.execute_query("DELETE FROM students WHERE student_id = %s", (student_id,))
        record_transaction('delete_student', 'student', student_id, {'deleted_student': student}, session.get('user_id'))
        flash(f"Student '{student['full_name']}' deleted.", 'info')
    except Exception as e:
        flash(f"Error deleting student: {e}", 'danger')

    return redirect(url_for('students.index'))
