import pytest
from app.dsa.hash_table import CustomHashTable
from app.dsa.search import linear_search, binary_search, search_with_trace
from app.dsa.sort import merge_sort, quick_sort, sort_with_trace
from app.dsa.queue import ReservationQueue
from app.dsa.stack import ActionUndoStack
from app.dsa.graph import BookGraph

# =====================================================================
# 1. Custom Hash Table Tests
# =====================================================================
def test_hash_table_basic_operations():
    ht = CustomHashTable(initial_capacity=4)
    
    # Test insertion and retrieval
    ht.put("978-01", {"title": "Book One"})
    ht.put("978-02", {"title": "Book Two"})
    
    assert ht.size() == 2
    assert ht.get("978-01") == {"title": "Book One"}
    assert ht.get("978-02") == {"title": "Book Two"}
    assert ht.contains("978-01") is True
    assert ht.contains("non-existent") is False

def test_hash_table_update_and_delete():
    ht = CustomHashTable(initial_capacity=8)
    ht.put("ISBN-100", {"copies": 5})
    # Update value
    ht.put("ISBN-100", {"copies": 6})
    assert ht.get("ISBN-100") == {"copies": 6}
    assert ht.size() == 1

    # Delete
    assert ht.remove("ISBN-100") is True
    assert ht.contains("ISBN-100") is False
    assert ht.size() == 0
    assert ht.remove("ISBN-100") is False

def test_hash_table_collision_resolution_and_resizing():
    # Force collisions with very small initial capacity
    ht = CustomHashTable(initial_capacity=2, max_load_factor=0.75)
    
    # Insert multiple items to trigger resizing
    for i in range(10):
        ht.put(f"ISBN-{i}", f"Book {i}")
        
    assert ht.size() == 10
    assert ht.capacity > 2  # capacity increased
    for i in range(10):
        assert ht.get(f"ISBN-{i}") == f"Book {i}"

    stats = ht.get_stats()
    assert stats['total_items'] == 10
    assert stats['load_factor'] <= 0.75

# =====================================================================
# 2. Searching Algorithm Tests
# =====================================================================
def test_linear_search():
    books = [
        {"title": "Clean Code", "author": "Robert Martin"},
        {"title": "Introduction to Algorithms", "author": "Thomas Cormen"},
        {"title": "Clean Architecture", "author": "Robert Martin"},
    ]
    
    matches = linear_search(books, key_func=lambda b: b['title'], target="clean")
    assert len(matches) == 2
    assert matches[0]['title'] == "Clean Code"
    assert matches[1]['title'] == "Clean Architecture"

    author_matches = linear_search(books, key_func=lambda b: b['author'], target="cormen")
    assert len(author_matches) == 1
    assert author_matches[0]['title'] == "Introduction to Algorithms"

def test_binary_search():
    sorted_titles = [
        {"title": "Algorithms"},
        {"title": "Clean Code"},
        {"title": "Design Patterns"},
        {"title": "Operating Systems"},
        {"title": "Python Basics"}
    ]

    idx = binary_search(sorted_titles, key_func=lambda b: b['title'], target="Design Patterns")
    assert idx == 2

    missing_idx = binary_search(sorted_titles, key_func=lambda b: b['title'], target="Quantum Computing")
    assert missing_idx == -1

def test_search_with_trace():
    books = [
        {"title": "Alpha", "id": 1},
        {"title": "Beta", "id": 2},
        {"title": "Gamma", "id": 3},
        {"title": "Delta", "id": 4}
    ]

    # Test Binary Search trace
    trace = search_with_trace(books, algorithm='binary', key_field='title', target='Gamma')
    assert trace['found'] is True
    assert trace['comparisons'] > 0
    assert len(trace['steps']) > 0

# =====================================================================
# 3. Sorting Algorithm Tests
# =====================================================================
def test_merge_sort():
    books = [
        {"year": 2018, "title": "C"},
        {"year": 1994, "title": "A"},
        {"year": 2008, "title": "B"},
        {"year": 2024, "title": "D"}
    ]
    
    sorted_asc = merge_sort(books, key_func=lambda b: b['year'])
    assert [b['year'] for b in sorted_asc] == [1994, 2008, 2018, 2024]

    sorted_desc = merge_sort(books, key_func=lambda b: b['year'], reverse=True)
    assert [b['year'] for b in sorted_desc] == [2024, 2018, 2008, 1994]

def test_quick_sort():
    books = [
        {"title": "Zoo Guide"},
        {"title": "Algorithms"},
        {"title": "Database Systems"},
        {"title": "Computer Networks"}
    ]

    sorted_books = quick_sort(books, key_func=lambda b: b['title'])
    assert sorted_books[0]['title'] == "Algorithms"
    assert sorted_books[1]['title'] == "Computer Networks"
    assert sorted_books[2]['title'] == "Database Systems"
    assert sorted_books[3]['title'] == "Zoo Guide"

def test_sort_with_trace():
    items = [{"val": 4}, {"val": 1}, {"val": 3}, {"val": 2}]
    res = sort_with_trace(items, algorithm='merge', key_field='val')
    assert res['comparisons'] > 0
    assert [x['val'] for x in res['sorted_items']] == [1, 2, 3, 4]

# =====================================================================
# 4. Queue (FIFO) Tests
# =====================================================================
def test_reservation_queue_fifo_order():
    q = ReservationQueue(book_id=1)
    assert q.is_empty() is True
    assert q.size() == 0

    q.enqueue({"reservation_id": 101, "student": "Alice"})
    q.enqueue({"reservation_id": 102, "student": "Bob"})
    q.enqueue({"reservation_id": 103, "student": "Charlie"})

    assert q.size() == 3
    assert q.peek()['student'] == "Alice"

    # Dequeue in exact arrival order
    first = q.dequeue()
    assert first['student'] == "Alice"
    assert q.size() == 2

    second = q.dequeue()
    assert second['student'] == "Bob"

    third = q.dequeue()
    assert third['student'] == "Charlie"
    assert q.is_empty() is True
    assert q.dequeue() is None

def test_reservation_queue_cancel_removal():
    q = ReservationQueue(book_id=5)
    q.enqueue({"reservation_id": 1, "student": "S1"})
    q.enqueue({"reservation_id": 2, "student": "S2"})
    q.enqueue({"reservation_id": 3, "student": "S3"})

    # Cancel middle item
    assert q.remove_by_reservation_id(2) is True
    assert q.size() == 2

    lst = q.to_list()
    assert len(lst) == 2
    assert lst[0]['student'] == "S1"
    assert lst[1]['student'] == "S3"
    assert lst[1]['queue_position'] == 2

# =====================================================================
# 5. Stack (LIFO) Undo Tests
# =====================================================================
def test_action_undo_stack_lifo_order():
    stack = ActionUndoStack(max_capacity=5)
    assert stack.is_empty() is True

    stack.push({"action": "add_book", "id": 1})
    stack.push({"action": "issue_book", "id": 2})
    stack.push({"action": "delete_book", "id": 3})

    assert stack.size() == 3
    assert stack.peek()['action'] == "delete_book"

    # Pop most recent (LIFO)
    top = stack.pop()
    assert top['action'] == "delete_book"

    second = stack.pop()
    assert second['action'] == "issue_book"

    third = stack.pop()
    assert third['action'] == "add_book"
    assert stack.is_empty() is True

# =====================================================================
# 6. Graph (BFS & DFS) Tests
# =====================================================================
def test_book_graph_construction_and_traversals():
    g = BookGraph()
    # Vertices
    g.add_vertex(1, {"title": "Algorithms"})
    g.add_vertex(2, {"title": "Data Structures"})
    g.add_vertex(3, {"title": "Operating Systems"})
    g.add_vertex(4, {"title": "Computer Networks"})
    g.add_vertex(5, {"title": "Machine Learning"})

    # Edges: 1 - 2, 1 - 3, 3 - 4, 2 - 5
    g.add_edge(1, 2, "Core CS", 0.9)
    g.add_edge(1, 3, "Prerequisite", 0.8)
    g.add_edge(3, 4, "Systems Domain", 0.85)
    g.add_edge(2, 5, "AI Application", 0.75)

    # BFS from 1
    bfs_result = g.bfs(start_id=1, max_depth=2)
    assert bfs_result['algorithm'] == 'Breadth-First Search (BFS)'
    assert bfs_result['visited_order'][0] == 1
    # Level 1 should be 2 and 3
    assert set(bfs_result['visited_order'][1:3]) == {2, 3}
    assert len(bfs_result['steps']) > 0

    # DFS from 1
    dfs_result = g.dfs(start_id=1, max_depth=3)
    assert dfs_result['algorithm'] == 'Depth-First Search (DFS)'
    assert dfs_result['visited_order'][0] == 1
    assert len(dfs_result['visited_order']) == 5

    # Recommendations
    recs = g.get_recommendations(start_id=1, limit=3)
    assert len(recs) > 0
    assert recs[0]['book_id'] in [2, 3] # highest weighted direct neighbors
