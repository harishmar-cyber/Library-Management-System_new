class QueueNode:
    """Linked list node representing a queue position."""
    def __init__(self, data):
        self.data = data
        self.next = None


class ReservationQueue:
    """
    First-In-First-Out (FIFO) Queue for book reservations.
    Enforces strict chronological fairness when multiple students wait for an unavailable book.
    """
    def __init__(self, book_id: int = None):
        self.book_id = book_id
        self.head = None
        self.tail = None
        self._count = 0

    def enqueue(self, reservation_data: dict):
        """Adds a student reservation to the end of the line (tail) in O(1)."""
        new_node = QueueNode(reservation_data)
        if self.tail is None:
            self.head = self.tail = new_node
        else:
            self.tail.next = new_node
            self.tail = new_node
        self._count += 1

    def dequeue(self) -> dict:
        """Serves and removes the earliest reservation at the front (head) in O(1)."""
        if self.is_empty():
            return None
        served_node = self.head
        self.head = self.head.next
        if self.head is None:
            self.tail = None
        self._count -= 1
        return served_node.data

    def peek(self) -> dict:
        """Inspects the front of the queue without removing it in O(1)."""
        if self.is_empty():
            return None
        return self.head.data

    def is_empty(self) -> bool:
        return self.head is None

    def size(self) -> int:
        return self._count

    def remove_by_reservation_id(self, reservation_id: int) -> bool:
        """Removes a cancelled reservation from anywhere in the queue."""
        curr = self.head
        prev = None
        while curr:
            if curr.data.get('reservation_id') == reservation_id:
                if prev is None:
                    self.head = curr.next
                    if self.head is None:
                        self.tail = None
                else:
                    prev.next = curr.next
                    if curr == self.tail:
                        self.tail = prev
                self._count -= 1
                return True
            prev = curr
            curr = curr.next
        return False

    def to_list(self) -> list:
        """Returns all reservations in current queue order with position numbers."""
        result = []
        curr = self.head
        pos = 1
        while curr:
            item = dict(curr.data)
            item['queue_position'] = pos
            result.append(item)
            curr = curr.next
            pos += 1
        return result
