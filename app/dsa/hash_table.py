class HashNode:
    """Linked list node used for separate chaining collision resolution."""
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.next = None

    def __repr__(self):
        return f"HashNode({self.key}: {self.value})"


class CustomHashTable:
    """
    Custom Hash Table using Separate Chaining for O(1) average lookup/insertion/deletion.
    Supports dynamic resizing when load factor exceeds 0.75.
    Used for instant lookup of books by ISBN or Book ID.
    """
    def __init__(self, initial_capacity: int = 16, max_load_factor: float = 0.75):
        self.capacity = max(4, initial_capacity)
        self.max_load_factor = max_load_factor
        self.buckets = [None] * self.capacity
        self.count = 0
        self.collisions = 0

    def _hash(self, key) -> int:
        """
        Polynomial rolling hash calculation with prime base 31.
        Produces well-distributed bucket indices.
        """
        s = str(key)
        h = 0
        prime = 31
        for char in s:
            h = (h * prime + ord(char)) & 0xFFFFFFFF
        return h % self.capacity

    def put(self, key, value):
        """Insert or update key-value pair. Resizes if load factor exceeds threshold."""
        index = self._hash(key)
        head = self.buckets[index]

        # Check if key exists in the chain
        curr = head
        while curr:
            if curr.key == key:
                curr.value = value
                return
            curr = curr.next

        # Insert new node at head of bucket chain
        new_node = HashNode(key, value)
        new_node.next = head
        if head is not None:
            self.collisions += 1
        self.buckets[index] = new_node
        self.count += 1

        # Check load factor and resize if needed
        if (self.count / self.capacity) > self.max_load_factor:
            self._resize(self.capacity * 2)

    def get(self, key, default=None):
        """Retrieve value by key in O(1) average time."""
        index = self._hash(key)
        curr = self.buckets[index]
        while curr:
            if curr.key == key:
                return curr.value
            curr = curr.next
        return default

    def contains(self, key) -> bool:
        """Check if key exists in hash table."""
        return self.get(key) is not None

    def remove(self, key) -> bool:
        """Remove key-value pair. Returns True if removed, False if not found."""
        index = self._hash(key)
        curr = self.buckets[index]
        prev = None

        while curr:
            if curr.key == key:
                if prev is None:
                    self.buckets[index] = curr.next
                else:
                    prev.next = curr.next
                self.count -= 1
                return True
            prev = curr
            curr = curr.next
        return False

    def size(self) -> int:
        """Number of elements currently stored."""
        return self.count

    def is_empty(self) -> bool:
        return self.count == 0

    def keys(self) -> list:
        """Return list of all stored keys."""
        all_keys = []
        for head in self.buckets:
            curr = head
            while curr:
                all_keys.append(curr.key)
                curr = curr.next
        return all_keys

    def values(self) -> list:
        """Return list of all stored values."""
        all_vals = []
        for head in self.buckets:
            curr = head
            while curr:
                all_vals.append(curr.value)
                curr = curr.next
        return all_vals

    def items(self) -> list:
        """Return list of (key, value) tuples."""
        all_items = []
        for head in self.buckets:
            curr = head
            while curr:
                all_items.append((curr.key, curr.value))
                curr = curr.next
        return all_items

    def get_stats(self) -> dict:
        """Statistical diagnostics of the hash table for DSA Lab."""
        occupied_buckets = sum(1 for b in self.buckets if b is not None)
        max_chain_len = 0
        bucket_distribution = []

        for i, head in enumerate(self.buckets):
            chain_len = 0
            curr = head
            while curr:
                chain_len += 1
                curr = curr.next
            max_chain_len = max(max_chain_len, chain_len)
            bucket_distribution.append({
                'bucket_index': i,
                'chain_length': chain_len,
                'stored_keys': [item.key for item in self._iter_chain(head)]
            })

        load_factor = round(self.count / self.capacity, 3) if self.capacity else 0

        return {
            'total_items': self.count,
            'capacity': self.capacity,
            'load_factor': load_factor,
            'occupied_buckets': occupied_buckets,
            'empty_buckets': self.capacity - occupied_buckets,
            'max_chain_length': max_chain_len,
            'collision_count': self.collisions,
            'distribution': bucket_distribution
        }

    def _iter_chain(self, head):
        curr = head
        while curr:
            yield curr
            curr = curr.next

    def _resize(self, new_capacity: int):
        """Resizes the bucket array and rehashes all elements."""
        old_buckets = self.buckets
        self.capacity = new_capacity
        self.buckets = [None] * new_capacity
        self.count = 0
        self.collisions = 0

        for head in old_buckets:
            curr = head
            while curr:
                self.put(curr.key, curr.value)
                curr = curr.next
