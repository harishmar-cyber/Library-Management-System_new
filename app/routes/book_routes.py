from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from app.routes.auth_routes import login_required
from app.db import db
from app.services import book_isbn_hash_table, book_id_hash_table, book_graph, record_transaction
from app.dsa.search import linear_search, binary_search
from app.dsa.sort import merge_sort, quick_sort

book_bp = Blueprint('books', __name__)

@book_bp.route('/books')
@login_required
def index():
    search_q = request.args.get('q', '').strip()
    search_by = request.args.get('by', 'title') # 'isbn', 'title', 'author', 'category'
    sort_by = request.args.get('sort', 'title') # 'title', 'author', 'publication_year'
    sort_algo = request.args.get('algo', 'merge') # 'merge' or 'quick'
    sort_dir = request.args.get('dir', 'asc')

    books = db.fetch_all("SELECT * FROM books")

    search_meta = {'applied': False, 'time_taken': None, 'dsa_used': None}

    # 1. Searching
    if search_q:
        search_meta['applied'] = True
        if search_by == 'isbn':
            # Use O(1) Custom Hash Table lookup
            exact_book = book_isbn_hash_table.get(search_q)
            books = [exact_book] if exact_book else []
            search_meta['dsa_used'] = 'Custom Separate-Chaining Hash Table O(1)'
        else:
            # Linear Search on titles/authors/categories
            books = linear_search(books, key_func=lambda b: b.get(search_by, ''), target=search_q)
            search_meta['dsa_used'] = f"Linear Search O(n) on field '{search_by}'"

    # 2. Sorting via Custom DSA algorithms
    reverse = (sort_dir == 'desc')
    if sort_algo == 'quick':
        books = quick_sort(books, key_func=lambda b: b.get(sort_by, ''), reverse=reverse)
        sort_meta = f"Quick Sort O(n log n) by '{sort_by}' ({sort_dir.upper()})"
    else:
        books = merge_sort(books, key_func=lambda b: b.get(sort_by, ''), reverse=reverse)
        sort_meta = f"Merge Sort O(n log n) by '{sort_by}' ({sort_dir.upper()})"

    return render_template(
        'books.html',
        active_page='books',
        books=books,
        search_q=search_q,
        search_by=search_by,
        sort_by=sort_by,
        sort_algo=sort_algo,
        sort_dir=sort_dir,
        search_meta=search_meta,
        sort_meta=sort_meta
    )

@book_bp.route('/books/add', methods=['POST'])
@login_required
def add_book():
    isbn = request.form.get('isbn', '').strip()
    title = request.form.get('title', '').strip()
    author = request.form.get('author', '').strip()
    category = request.form.get('category', '').strip()
    pub_year = request.form.get('publication_year', 2026, type=int)
    total_copies = request.form.get('total_copies', 1, type=int)
    shelf = request.form.get('shelf_location', 'Section A').strip()

    if not isbn or not title or not author:
        flash('ISBN, Title, and Author are required fields.', 'danger')
        return redirect(url_for('books.index'))

    # Check duplicate ISBN
    if book_isbn_hash_table.contains(isbn):
        flash(f"A book with ISBN '{isbn}' already exists in the catalog.", 'warning')
        return redirect(url_for('books.index'))

    try:
        book_id = db.execute_query("""
            INSERT INTO books (isbn, title, author, category, publication_year, total_copies, available_copies, shelf_location)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (isbn, title, author, category, pub_year, total_copies, total_copies, shelf))

        new_book = {
            'book_id': book_id,
            'isbn': isbn,
            'title': title,
            'author': author,
            'category': category,
            'publication_year': pub_year,
            'total_copies': total_copies,
            'available_copies': total_copies,
            'shelf_location': shelf
        }

        # Update in-memory DSA structures
        book_isbn_hash_table.put(isbn, new_book)
        book_id_hash_table.put(str(book_id), new_book)
        book_graph.add_vertex(book_id, new_book)

        # Log for Undo Stack
        record_transaction('add_book', 'book', book_id, new_book, session.get('user_id'))

        flash(f"Book '{title}' added successfully! (Indexed in Custom Hash Table)", 'success')
    except Exception as e:
        flash(f"Error adding book: {e}", 'danger')

    return redirect(url_for('books.index'))

@book_bp.route('/books/edit/<int:book_id>', methods=['POST'])
@login_required
def edit_book(book_id):
    title = request.form.get('title', '').strip()
    author = request.form.get('author', '').strip()
    category = request.form.get('category', '').strip()
    pub_year = request.form.get('publication_year', 2026, type=int)
    total_copies = request.form.get('total_copies', 1, type=int)
    available_copies = request.form.get('available_copies', 1, type=int)
    shelf = request.form.get('shelf_location', '').strip()

    old_book = db.fetch_one("SELECT * FROM books WHERE book_id = %s", (book_id,))
    if not old_book:
        flash('Book not found.', 'danger')
        return redirect(url_for('books.index'))

    try:
        db.execute_query("""
            UPDATE books 
            SET title = %s, author = %s, category = %s, publication_year = %s, total_copies = %s, available_copies = %s, shelf_location = %s
            WHERE book_id = %s
        """, (title, author, category, pub_year, total_copies, available_copies, shelf, book_id))

        updated_book = dict(old_book)
        updated_book.update({
            'title': title,
            'author': author,
            'category': category,
            'publication_year': pub_year,
            'total_copies': total_copies,
            'available_copies': available_copies,
            'shelf_location': shelf
        })

        # Update DSA Hash Tables & Graph
        book_isbn_hash_table.put(old_book['isbn'], updated_book)
        book_id_hash_table.put(str(book_id), updated_book)
        book_graph.add_vertex(book_id, updated_book)

        # Record undo stack entry
        record_transaction('edit_book', 'book', book_id, {'previous': old_book, 'updated': updated_book}, session.get('user_id'))

        flash(f"Book '{title}' updated successfully.", 'success')
    except Exception as e:
        flash(f"Error updating book: {e}", 'danger')

    return redirect(url_for('books.index'))

@book_bp.route('/books/delete/<int:book_id>', methods=['POST'])
@login_required
def delete_book(book_id):
    book = db.fetch_one("SELECT * FROM books WHERE book_id = %s", (book_id,))
    if not book:
        flash('Book not found.', 'danger')
        return redirect(url_for('books.index'))

    # Check if currently issued
    active_issues = db.fetch_one("SELECT COUNT(*) as count FROM book_issues WHERE book_id = %s AND status = 'issued'", (book_id,))
    if active_issues and active_issues['count'] > 0:
        flash('Cannot delete book while active copies are currently issued to students.', 'warning')
        return redirect(url_for('books.index'))

    try:
        db.execute_query("DELETE FROM books WHERE book_id = %s", (book_id,))

        # Remove from Custom Hash Table
        book_isbn_hash_table.remove(book['isbn'])
        book_id_hash_table.remove(str(book_id))

        # Record on Undo Stack
        record_transaction('delete_book', 'book', book_id, {'deleted_book': book}, session.get('user_id'))

        flash(f"Book '{book['title']}' deleted. (Action can be undone via Undo Stack)", 'info')
    except Exception as e:
        flash(f"Error deleting book: {e}", 'danger')

    return redirect(url_for('books.index'))

@book_bp.route('/api/books/hash-lookup')
@login_required
def api_hash_lookup():
    """O(1) Hash Table lookup demonstration endpoint."""
    isbn = request.args.get('isbn', '').strip()
    book = book_isbn_hash_table.get(isbn)
    if book:
        return jsonify({'found': True, 'book': book, 'complexity': 'O(1) Separate Chaining Hash Map'})
    return jsonify({'found': False, 'message': 'Book ISBN not found in hash table'})
