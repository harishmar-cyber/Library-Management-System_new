import time
from typing import List, Any, Callable, Dict, Tuple

def linear_search(items: List[Any], key_func: Callable[[Any], str], target: str, partial_match: bool = True) -> List[Any]:
    """
    Performs Linear Search O(n) on items using key_func to extract search field.
    Returns list of matching items.
    """
    target_clean = str(target).strip().lower()
    matches = []
    
    for item in items:
        field_val = str(key_func(item)).strip().lower()
        if partial_match:
            if target_clean in field_val:
                matches.append(item)
        else:
            if target_clean == field_val:
                matches.append(item)
                
    return matches


def binary_search(sorted_items: List[Any], key_func: Callable[[Any], Any], target: Any) -> int:
    """
    Performs Binary Search O(log n) on already sorted items.
    Returns index of matching item, or -1 if not found.
    """
    low = 0
    high = len(sorted_items) - 1
    target_val = str(target).strip().lower()

    while low <= high:
        mid = (low + high) // 2
        mid_val = str(key_func(sorted_items[mid])).strip().lower()

        if mid_val == target_val:
            return mid
        elif mid_val < target_val:
            low = mid + 1
        else:
            high = mid - 1

    return -1


def search_with_trace(items: List[Any], algorithm: str, key_field: str, target: str) -> Dict[str, Any]:
    """
    Executes search with step-by-step tracing for DSA Interactive Lab.
    Supports 'linear' and 'binary' algorithms.
    """
    start_time = time.perf_counter()
    steps = []
    comparisons = 0
    target_clean = str(target).strip().lower()

    if algorithm.lower() == 'binary':
        # Ensure items are sorted by key_field first
        sorted_list = sorted(items, key=lambda x: str(x.get(key_field, '')).lower())
        low = 0
        high = len(sorted_list) - 1
        found_idx = -1

        while low <= high:
            comparisons += 1
            mid = (low + high) // 2
            mid_val = str(sorted_list[mid].get(key_field, '')).strip().lower()
            
            step_record = {
                'step': len(steps) + 1,
                'low': low,
                'mid': mid,
                'high': high,
                'current_value': sorted_list[mid].get(key_field),
                'target': target,
                'action': ''
            }

            if mid_val == target_clean:
                step_record['action'] = f"Match found at index {mid}! ({mid_val} == {target_clean})"
                steps.append(step_record)
                found_idx = mid
                break
            elif mid_val < target_clean:
                step_record['action'] = f"'{mid_val}' < '{target_clean}' → Narrow range to right half (low = {mid + 1})"
                low = mid + 1
            else:
                step_record['action'] = f"'{mid_val}' > '{target_clean}' → Narrow range to left half (high = {mid - 1})"
                high = mid - 1
                
            steps.append(step_record)

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        found_item = sorted_list[found_idx] if found_idx != -1 else None

        return {
            'algorithm': 'Binary Search',
            'time_complexity': 'O(log n)',
            'comparisons': comparisons,
            'elapsed_ms': round(elapsed_ms, 3),
            'found': found_idx != -1,
            'match_count': 1 if found_idx != -1 else 0,
            'result': [found_item] if found_item else [],
            'steps': steps
        }

    else: # Linear Search
        matches = []
        for i, item in enumerate(items):
            comparisons += 1
            val = str(item.get(key_field, '')).strip().lower()
            is_match = target_clean in val
            
            step_record = {
                'step': len(steps) + 1,
                'index': i,
                'current_value': item.get(key_field),
                'target': target,
                'action': f"Examining index {i}: '{item.get(key_field)}' {'✓ MATCH' if is_match else '✗ No match'}"
            }
            steps.append(step_record)
            if is_match:
                matches.append(item)

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return {
            'algorithm': 'Linear Search',
            'time_complexity': 'O(n)',
            'comparisons': comparisons,
            'elapsed_ms': round(elapsed_ms, 3),
            'found': len(matches) > 0,
            'match_count': len(matches),
            'result': matches,
            'steps': steps
        }
