class StackNode:
    """Linked list node for LIFO undo stack."""
    def __init__(self, data):
        self.data = data
        self.next = None


class ActionUndoStack:
    """
    Last-In-First-Out (LIFO) Stack for undoing librarian operations.
    Supports operations such as undo book deletion, undo loan return, and undo updates.
    """
    def __init__(self, max_capacity: int = 50):
        self.top = None
        self._count = 0
        self.max_capacity = max_capacity

    def push(self, action_data: dict):
        """Pushes a new reversible librarian action onto the top of the stack in O(1)."""
        new_node = StackNode(action_data)
        new_node.next = self.top
        self.top = new_node
        self._count += 1

        # Enforce max capacity by dropping bottom if necessary
        if self._count > self.max_capacity:
            self._drop_bottom()

    def pop(self) -> dict:
        """Pops and returns the most recent action from the top in O(1)."""
        if self.is_empty():
            return None
        popped = self.top
        self.top = self.top.next
        self._count -= 1
        return popped.data

    def peek(self) -> dict:
        """Views the most recent action without removing it in O(1)."""
        if self.is_empty():
            return None
        return self.top.data

    def is_empty(self) -> bool:
        return self.top is None

    def size(self) -> int:
        return self._count

    def clear(self):
        self.top = None
        self._count = 0

    def to_list(self) -> list:
        """Returns stack items from top (most recent) to bottom."""
        items = []
        curr = self.top
        while curr:
            items.append(curr.data)
            curr = curr.next
        return items

    def _drop_bottom(self):
        """Drops the oldest element at the bottom to maintain memory bounds."""
        if not self.top or not self.top.next:
            return
        curr = self.top
        while curr.next and curr.next.next:
            curr = curr.next
        curr.next = None
        self._count -= 1
