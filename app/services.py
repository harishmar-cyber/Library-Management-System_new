import json
import logging
from app.db import db
from app.dsa.hash_table import CustomHashTable
from app.dsa.queue import ReservationQueue
from app.dsa.stack import ActionUndoStack
from app.dsa.graph import BookGraph

logger = logging.getLogger(__name__)

# Global DSA In-Memory Structures
book_isbn_hash_table = CustomHashTable(initial_capacity=32)
book_id_hash_table = CustomHashTable(initial_capacity=32)
reservation_queues = {} # {book_id: ReservationQueue}
undo_stack = ActionUndoStack(max_capacity=50)
book_graph = BookGraph()

def init_dsa_structures():
    """Populates in-memory DSA structures directly from database tables."""
    global book_isbn_hash_table, book_id_hash_table, reservation_queues, book_graph

    try:
        # 1. Load Books into Custom Hash Tables
        books = db.fetch_all("SELECT * FROM books")
        book_isbn_hash_table = CustomHashTable(initial_capacity=max(16, len(books) * 2))
        book_id_hash_table = CustomHashTable(initial_capacity=max(16, len(books) * 2))
        book_graph = BookGraph()

        for b in books:
            book_dict = dict(b)
            # Store in ISBN Hash Table
            book_isbn_hash_table.put(b['isbn'], book_dict)
            # Store in Book ID Hash Table
            book_id_hash_table.put(str(b['book_id']), book_dict)
            # Add vertex to graph
            book_graph.add_vertex(b['book_id'], book_dict)

        # 2. Load Graph Edges
        relations = db.fetch_all("SELECT * FROM book_relations")
        for rel in relations:
            book_graph.add_edge(
                rel['source_book_id'],
                rel['target_book_id'],
                rel['relation_type'],
                rel['weight'],
                bidirectional=True
            )

        # 3. Load Active Reservations into FIFO Queues
        res_rows = db.fetch_all("""
            SELECT r.*, s.full_name as student_name, s.student_number, b.title as book_title
            FROM reservations r
            JOIN students s ON r.student_id = s.student_id
            JOIN books b ON r.book_id = b.book_id
            WHERE r.status = 'pending'
            ORDER BY r.book_id, r.queue_position ASC, r.reservation_date ASC
        """)

        reservation_queues = {}
        for r in res_rows:
            b_id = r['book_id']
            if b_id not in reservation_queues:
                reservation_queues[b_id] = ReservationQueue(book_id=b_id)
            reservation_queues[b_id].enqueue(dict(r))

        logger.info(f"Initialized DSA: {len(books)} books hashed, {len(relations)} graph edges, {len(reservation_queues)} reservation queues.")
    except Exception as e:
        logger.error(f"Error during DSA structure initialization: {e}")


def record_transaction(action_type: str, entity_type: str, entity_id: int, details: dict, user_id: int = None):
    """
    Records an action into both MySQL database transactions table and the in-memory LIFO Undo Stack.
    """
    details_str = json.dumps(details)
    tx_id = db.execute_query("""
        INSERT INTO transactions (action_type, entity_type, entity_id, details, user_id, undone)
        VALUES (%s, %s, %s, %s, %s, 0)
    """, (action_type, entity_type, entity_id, details_str, user_id))

    # Push onto LIFO Stack
    action_data = {
        'transaction_id': tx_id,
        'action_type': action_type,
        'entity_type': entity_type,
        'entity_id': entity_id,
        'details': details,
        'user_id': user_id
    }
    undo_stack.push(action_data)
    return tx_id
