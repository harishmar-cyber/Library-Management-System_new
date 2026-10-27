from flask import Blueprint, render_template, request, jsonify
from app.routes.auth_routes import login_required
from app.db import db
from app.services import (
    book_isbn_hash_table, 
    book_id_hash_table, 
    reservation_queues, 
    undo_stack, 
    book_graph
)
from app.dsa.search import search_with_trace
from app.dsa.sort import sort_with_trace

dsa_lab_bp = Blueprint('dsa_lab', __name__)

@dsa_lab_bp.route('/dsa-lab')
@login_required
def index():
    books = db.fetch_all("SELECT * FROM books ORDER BY book_id ASC")
    hash_stats = book_isbn_hash_table.get_stats()
    stack_items = undo_stack.to_list()
    
    return render_template(
        'dsa_lab.html',
        active_page='dsa_lab',
        books=books,
        hash_stats=hash_stats,
        stack_items=stack_items,
        stack_size=undo_stack.size()
    )

@dsa_lab_bp.route('/api/dsa-lab/hash/stats')
@login_required
def api_hash_stats():
    """Returns hash table bucket distribution and metrics."""
    return jsonify(book_isbn_hash_table.get_stats())

@dsa_lab_bp.route('/api/dsa-lab/search/run', methods=['POST'])
@login_required
def api_run_search():
    """Runs Linear or Binary search with step-by-step tracing."""
    data = request.get_json() or {}
    algorithm = data.get('algorithm', 'linear') # 'linear' or 'binary'
    key_field = data.get('key_field', 'title')
    target = data.get('target', '')

    books = db.fetch_all("SELECT book_id, isbn, title, author, category, publication_year FROM books")
    trace_result = search_with_trace(books, algorithm=algorithm, key_field=key_field, target=target)
    return jsonify(trace_result)

@dsa_lab_bp.route('/api/dsa-lab/sort/run', methods=['POST'])
@login_required
def api_run_sort():
    """Runs Merge Sort or Quick Sort with operation traces and metrics."""
    data = request.get_json() or {}
    algorithm = data.get('algorithm', 'merge') # 'merge' or 'quick'
    key_field = data.get('key_field', 'title')
    reverse = data.get('reverse', False)

    books = db.fetch_all("SELECT book_id, isbn, title, author, category, publication_year, available_copies FROM books")
    trace_result = sort_with_trace(books, algorithm=algorithm, key_field=key_field, reverse=reverse)
    return jsonify(trace_result)

@dsa_lab_bp.route('/api/dsa-lab/stack/inspect')
@login_required
def api_stack_inspect():
    """Returns current LIFO undo stack entries."""
    return jsonify({
        'size': undo_stack.size(),
        'is_empty': undo_stack.is_empty(),
        'items': undo_stack.to_list()
    })
