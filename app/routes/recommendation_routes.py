from flask import Blueprint, render_template, request, jsonify
from app.routes.auth_routes import login_required
from app.db import db
from app.services import book_graph

recommendation_bp = Blueprint('recommendations', __name__)

@recommendation_bp.route('/recommendations')
@login_required
def index():
    books = db.fetch_all("SELECT book_id, title, author, category, isbn FROM books ORDER BY title ASC")
    default_book_id = books[0]['book_id'] if books else None
    selected_id = request.args.get('book_id', default_book_id, type=int)

    recommendations = []
    selected_book = None
    if selected_id:
        selected_book = db.fetch_one("SELECT * FROM books WHERE book_id = %s", (selected_id,))
        recommendations = book_graph.get_recommendations(selected_id, limit=6)

    # Graph stats
    vis_data = book_graph.to_vis_data()

    return render_template(
        'recommendations.html',
        active_page='recommendations',
        books=books,
        selected_book=selected_book,
        selected_id=selected_id,
        recommendations=recommendations,
        total_nodes=len(vis_data['nodes']),
        total_edges=len(vis_data['edges'])
    )

@recommendation_bp.route('/api/recommendations/graph-data')
@login_required
def api_graph_data():
    """Returns nodes and edges formatted for HTML5 canvas rendering."""
    return jsonify(book_graph.to_vis_data())

@recommendation_bp.route('/api/recommendations/bfs')
@login_required
def api_bfs():
    """Executes BFS from a starting book and returns step-by-step trace."""
    start_id = request.args.get('book_id', type=int)
    max_depth = request.args.get('depth', 3, type=int)
    if not start_id:
        return jsonify({'error': 'book_id is required'}), 400

    result = book_graph.bfs(start_id, max_depth=max_depth)
    return jsonify(result)

@recommendation_bp.route('/api/recommendations/dfs')
@login_required
def api_dfs():
    """Executes DFS from a starting book and returns step-by-step trace."""
    start_id = request.args.get('book_id', type=int)
    max_depth = request.args.get('depth', 3, type=int)
    if not start_id:
        return jsonify({'error': 'book_id is required'}), 400

    result = book_graph.dfs(start_id, max_depth=max_depth)
    return jsonify(result)

@recommendation_bp.route('/api/recommendations/suggest')
@login_required
def api_suggest():
    """Returns top ranked recommendations for selected book."""
    book_id = request.args.get('book_id', type=int)
    if not book_id:
        return jsonify({'error': 'book_id required'}), 400
    recs = book_graph.get_recommendations(book_id, limit=6)
    return jsonify({'recommendations': recs})
