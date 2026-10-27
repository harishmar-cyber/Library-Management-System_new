from collections import deque
from typing import Dict, List, Any, Optional

class BookGraph:
    """
    Graph implementation using an Adjacency List for book recommendations.
    Vertices represent books; edges represent topic affinities, prerequisites,
    shared authors, or co-borrowed patterns.
    Supports Breadth-First Search (BFS) and Depth-First Search (DFS) traversals.
    """
    def __init__(self):
        # adjacency_list: {book_id: [{'target': id, 'relation': type, 'weight': float}]}
        self.adjacency_list: Dict[int, List[Dict[str, Any]]] = {}
        # node_metadata: {book_id: {title, author, category, isbn, ...}}
        self.node_metadata: Dict[int, Dict[str, Any]] = {}

    def add_vertex(self, book_id: int, metadata: Dict[str, Any]):
        """Adds a book vertex with its metadata."""
        if book_id not in self.adjacency_list:
            self.adjacency_list[book_id] = []
        self.node_metadata[book_id] = metadata

    def add_edge(self, source_id: int, target_id: int, relation_type: str = 'co_borrowed', weight: float = 1.0, bidirectional: bool = True):
        """Adds a weighted relationship edge between two books."""
        if source_id not in self.adjacency_list:
            self.adjacency_list[source_id] = []
        if target_id not in self.adjacency_list:
            self.adjacency_list[target_id] = []

        # Check existing edge
        exists = any(edge['target'] == target_id for edge in self.adjacency_list[source_id])
        if not exists:
            self.adjacency_list[source_id].append({
                'target': target_id,
                'relation': relation_type,
                'weight': float(weight)
            })

        if bidirectional:
            back_exists = any(edge['target'] == source_id for edge in self.adjacency_list[target_id])
            if not back_exists:
                self.adjacency_list[target_id].append({
                    'target': source_id,
                    'relation': relation_type,
                    'weight': float(weight)
                })

    def bfs(self, start_id: int, max_depth: int = 3) -> Dict[str, Any]:
        """
        Breadth-First Search traversal starting from a given book.
        Explores level-by-level using a FIFO Queue.
        Records step-by-step queue snapshots and traversal order for visualization.
        """
        if start_id not in self.adjacency_list:
            return {'visited_order': [], 'steps': [], 'traversed_edges': []}

        visited = set([start_id])
        queue = deque([(start_id, 0)]) # (node_id, depth)
        visited_order = []
        steps = []
        traversed_edges = []

        while queue:
            current_id, depth = queue.popleft()
            curr_meta = self.node_metadata.get(current_id, {})
            visited_order.append(current_id)

            step_record = {
                'step': len(steps) + 1,
                'node_id': current_id,
                'title': curr_meta.get('title', f"Book {current_id}"),
                'depth': depth,
                'queue_state': [q[0] for q in queue],
                'action': f"Dequeued & visited '{curr_meta.get('title', current_id)}' at depth {depth}"
            }
            steps.append(step_record)

            if depth < max_depth:
                # Explore neighbors
                for edge in self.adjacency_list.get(current_id, []):
                    neighbor_id = edge['target']
                    if neighbor_id not in visited:
                        visited.add(neighbor_id)
                        queue.append((neighbor_id, depth + 1))
                        traversed_edges.append({
                            'source': current_id,
                            'target': neighbor_id,
                            'relation': edge['relation']
                        })

        return {
            'algorithm': 'Breadth-First Search (BFS)',
            'start_node': start_id,
            'visited_order': visited_order,
            'visited_count': len(visited_order),
            'traversed_edges': traversed_edges,
            'steps': steps
        }

    def dfs(self, start_id: int, max_depth: int = 3) -> Dict[str, Any]:
        """
        Depth-First Search traversal starting from a given book.
        Explores deeply along each branch using recursion / LIFO Stack.
        Records step-by-step stack snapshots and traversal order for visualization.
        """
        if start_id not in self.adjacency_list:
            return {'visited_order': [], 'steps': [], 'traversed_edges': []}

        visited = set()
        visited_order = []
        steps = []
        traversed_edges = []

        def _dfs_helper(node_id: int, depth: int, parent_id: Optional[int]):
            visited.add(node_id)
            visited_order.append(node_id)
            curr_meta = self.node_metadata.get(node_id, {})

            steps.append({
                'step': len(steps) + 1,
                'node_id': node_id,
                'title': curr_meta.get('title', f"Book {node_id}"),
                'depth': depth,
                'action': f"Visiting branch node '{curr_meta.get('title', node_id)}' (depth {depth})"
            })

            if parent_id is not None:
                traversed_edges.append({
                    'source': parent_id,
                    'target': node_id
                })

            if depth < max_depth:
                for edge in self.adjacency_list.get(node_id, []):
                    neighbor_id = edge['target']
                    if neighbor_id not in visited:
                        _dfs_helper(neighbor_id, depth + 1, node_id)

        _dfs_helper(start_id, 0, None)

        return {
            'algorithm': 'Depth-First Search (DFS)',
            'start_node': start_id,
            'visited_order': visited_order,
            'visited_count': len(visited_order),
            'traversed_edges': traversed_edges,
            'steps': steps
        }

    def get_recommendations(self, start_id: int, limit: int = 6) -> List[Dict[str, Any]]:
        """
        Generates book recommendations using 1-hop and 2-hop weighted graph traversal.
        Sorts candidates by cumulative edge weight and relationship relevance.
        """
        if start_id not in self.adjacency_list:
            return []

        scores: Dict[int, float] = {}
        relations_map: Dict[int, str] = {}

        # 1-hop direct neighbors
        for edge in self.adjacency_list.get(start_id, []):
            target = edge['target']
            scores[target] = scores.get(target, 0.0) + edge['weight'] * 1.5
            relations_map[target] = edge['relation']

            # 2-hop neighbors (co-recommended)
            for hop2 in self.adjacency_list.get(target, []):
                h2_target = hop2['target']
                if h2_target != start_id:
                    scores[h2_target] = scores.get(h2_target, 0.0) + hop2['weight'] * 0.7
                    if h2_target not in relations_map:
                        relations_map[h2_target] = f"Linked via {self.node_metadata.get(target, {}).get('title', 'connected title')}"

        # Sort candidate book IDs by highest score
        ranked_ids = sorted(scores.keys(), key=lambda b_id: scores[b_id], reverse=True)[:limit]

        recommendations = []
        for b_id in ranked_ids:
            meta = self.node_metadata.get(b_id, {})
            recommendations.append({
                'book_id': b_id,
                'title': meta.get('title', 'Unknown'),
                'author': meta.get('author', 'Unknown'),
                'category': meta.get('category', 'General'),
                'isbn': meta.get('isbn', ''),
                'score': round(scores[b_id], 2),
                'relation_reason': relations_map.get(b_id, 'Related by graph community')
            })

        return recommendations

    def to_vis_data(self) -> Dict[str, Any]:
        """
        Exports the graph structure formatted for interactive HTML5 canvas rendering.
        """
        nodes = []
        for b_id, meta in self.node_metadata.items():
            degree = len(self.adjacency_list.get(b_id, []))
            nodes.append({
                'id': b_id,
                'label': meta.get('title', f"Book {b_id}"),
                'category': meta.get('category', 'General'),
                'author': meta.get('author', ''),
                'isbn': meta.get('isbn', ''),
                'degree': degree
            })

        edges = []
        seen = set()
        for source_id, edge_list in self.adjacency_list.items():
            for edge in edge_list:
                target_id = edge['target']
                edge_pair = tuple(sorted([source_id, target_id]))
                if edge_pair not in seen:
                    seen.add(edge_pair)
                    edges.append({
                        'from': source_id,
                        'to': target_id,
                        'relation': edge['relation'],
                        'weight': edge['weight']
                    })

        return {'nodes': nodes, 'edges': edges}
