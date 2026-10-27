import pytest
from app import create_app
from app.db import db
from app.services import undo_stack

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def authenticated_client(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['username'] = 'admin'
        sess['user_name'] = 'Chief Librarian'
        sess['role'] = 'admin'
    return client

def test_login_page_renders(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Lavender LMS' in response.data

def test_login_successful(client):
    response = client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
    assert response.status_code == 200
    assert b'Chief Librarian' in response.data

def test_login_invalid_credentials(client):
    response = client.post('/login', data={'username': 'admin', 'password': 'wrongpassword'}, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid username or password' in response.data

def test_dashboard_requires_login(client):
    response = client.get('/dashboard', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers['Location']

def test_dashboard_authenticated(authenticated_client):
    response = authenticated_client.get('/dashboard')
    assert response.status_code == 200
    assert b'System Overview' in response.data
    assert b'Catalog Titles' in response.data

def test_books_page_and_hash_lookup(authenticated_client):
    # Test books catalog page
    response = authenticated_client.get('/books')
    assert response.status_code == 200
    assert b'Catalog Inventory' in response.data

    # Test O(1) hash lookup endpoint
    api_res = authenticated_client.get('/api/books/hash-lookup?isbn=978-0262033848')
    assert api_res.status_code == 200
    data = api_res.get_json()
    assert data['found'] is True
    assert 'Algorithms' in data['book']['title']

def test_add_and_search_book(authenticated_client):
    # Add new book
    res = authenticated_client.post('/books/add', data={
        'isbn': '978-TEST-001',
        'title': 'Test Algorithms Book',
        'author': 'Tester Bob',
        'category': 'Computer Science',
        'publication_year': 2026,
        'total_copies': 4,
        'shelf_location': 'Shelf T-1'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b'Test Algorithms Book' in res.data

    # Search for it using Linear Search
    search_res = authenticated_client.get('/books?q=Test+Algorithms&by=title')
    assert search_res.status_code == 200
    assert b'Test Algorithms Book' in search_res.data

def test_students_page_and_add(authenticated_client):
    response = authenticated_client.get('/students')
    assert response.status_code == 200
    assert b'Student Management' in response.data

    # Add student
    add_res = authenticated_client.post('/students/add', data={
        'student_number': 'STU-TEST-99',
        'full_name': 'Test Student 99',
        'email': 'stu99@test.edu',
        'phone': '1234567890',
        'department': 'CS'
    }, follow_redirects=True)
    assert add_res.status_code == 200
    assert b'Test Student 99' in add_res.data

def test_issues_page_and_circulation(authenticated_client):
    response = authenticated_client.get('/issues')
    assert response.status_code == 200
    assert b'Circulation Ledger' in response.data

def test_reservations_page_and_fifo(authenticated_client):
    response = authenticated_client.get('/reservations')
    assert response.status_code == 200
    assert b'Active Book Waiting Lines' in response.data

def test_recommendations_graph_and_api(authenticated_client):
    response = authenticated_client.get('/recommendations')
    assert response.status_code == 200
    assert b'Relational Adjacency Graph Canvas' in response.data

    # Test BFS API
    bfs_res = authenticated_client.get('/api/recommendations/bfs?book_id=1&depth=2')
    assert bfs_res.status_code == 200
    bfs_data = bfs_res.get_json()
    assert bfs_data['start_node'] == 1
    assert len(bfs_data['steps']) > 0

    # Test DFS API
    dfs_res = authenticated_client.get('/api/recommendations/dfs?book_id=1&depth=2')
    assert dfs_res.status_code == 200
    dfs_data = dfs_res.get_json()
    assert dfs_data['start_node'] == 1

def test_dsa_lab_page_and_search_sort_api(authenticated_client):
    response = authenticated_client.get('/dsa-lab')
    assert response.status_code == 200
    assert b'Interactive DSA Demonstration Lab' in response.data

    # Search run
    search_api = authenticated_client.post('/api/dsa-lab/search/run', json={
        'algorithm': 'linear',
        'key_field': 'title',
        'target': 'Clean'
    })
    assert search_api.status_code == 200
    assert search_api.get_json()['found'] is True

    # Sort run
    sort_api = authenticated_client.post('/api/dsa-lab/sort/run', json={
        'algorithm': 'merge',
        'key_field': 'publication_year',
        'reverse': False
    })
    assert sort_api.status_code == 200
    assert sort_api.get_json()['comparisons'] > 0

def test_reports_page_and_undo_api(authenticated_client):
    response = authenticated_client.get('/reports')
    assert response.status_code == 200
    assert b'Transaction Audit Ledger' in response.data

    # Test undo endpoint
    undo_res = authenticated_client.post('/api/undo')
    assert undo_res.status_code == 200
    undo_data = undo_res.get_json()
    assert 'success' in undo_data
