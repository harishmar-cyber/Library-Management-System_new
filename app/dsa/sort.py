import time
from typing import List, Any, Callable, Dict

def merge_sort(items: List[Any], key_func: Callable[[Any], Any] = None, reverse: bool = False) -> List[Any]:
    """
    Standard stable Merge Sort algorithm O(n log n).
    """
    if len(items) <= 1:
        return list(items)

    mid = len(items) // 2
    left = merge_sort(items[:mid], key_func, reverse)
    right = merge_sort(items[mid:], key_func, reverse)

    return _merge(left, right, key_func, reverse)

def _merge(left: List[Any], right: List[Any], key_func: Callable[[Any], Any], reverse: bool) -> List[Any]:
    merged = []
    i = j = 0

    while i < len(left) and j < len(right):
        val_left = key_func(left[i]) if key_func else left[i]
        val_right = key_func(right[j]) if key_func else right[j]

        # Case-insensitive comparison if strings
        if isinstance(val_left, str):
            val_left = val_left.lower()
        if isinstance(val_right, str):
            val_right = val_right.lower()

        condition = (val_left > val_right) if reverse else (val_left <= val_right)

        if condition:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1

    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged


def quick_sort(items: List[Any], key_func: Callable[[Any], Any] = None, reverse: bool = False) -> List[Any]:
    """
    Quick Sort algorithm O(n log n) average.
    """
    arr = list(items)
    if len(arr) <= 1:
        return arr

    def _get_val(x):
        v = key_func(x) if key_func else x
        return v.lower() if isinstance(v, str) else v

    pivot = arr[len(arr) // 2]
    pivot_val = _get_val(pivot)

    if not reverse:
        left = [x for x in arr if _get_val(x) < pivot_val]
        middle = [x for x in arr if _get_val(x) == pivot_val]
        right = [x for x in arr if _get_val(x) > pivot_val]
    else:
        left = [x for x in arr if _get_val(x) > pivot_val]
        middle = [x for x in arr if _get_val(x) == pivot_val]
        right = [x for x in arr if _get_val(x) < pivot_val]

    return quick_sort(left, key_func, reverse) + middle + quick_sort(right, key_func, reverse)


def sort_with_trace(items: List[Any], algorithm: str, key_field: str, reverse: bool = False) -> Dict[str, Any]:
    """
    Sorts list and collects operational trace metrics for DSA Demonstration Lab.
    """
    start_time = time.perf_counter()
    steps = []
    comparisons = [0]
    moves = [0]

    def key_func(item):
        val = item.get(key_field, '')
        return str(val).lower() if isinstance(val, str) else val

    arr = list(items)

    if algorithm.lower() == 'merge':
        def tracked_merge_sort(sub_arr, depth=0):
            if len(sub_arr) <= 1:
                return sub_arr

            mid = len(sub_arr) // 2
            left = tracked_merge_sort(sub_arr[:mid], depth + 1)
            right = tracked_merge_sort(sub_arr[mid:], depth + 1)

            merged = []
            i = j = 0
            while i < len(left) and j < len(right):
                comparisons[0] += 1
                v_l = key_func(left[i])
                v_r = key_func(right[j])
                cond = (v_l > v_r) if reverse else (v_l <= v_r)
                if cond:
                    merged.append(left[i])
                    i += 1
                else:
                    merged.append(right[j])
                    j += 1
                moves[0] += 1

            merged.extend(left[i:])
            merged.extend(right[j:])

            steps.append({
                'depth': depth,
                'action': f"Merged {len(left)} & {len(right)} items → Sublist size: {len(merged)}",
                'sample': [m.get(key_field) for m in merged[:4]]
            })
            return merged

        sorted_result = tracked_merge_sort(arr)
        complexity = "O(n log n) Best / Worst / Avg"

    else: # Quick Sort
        def tracked_quick_sort(sub_arr, depth=0):
            if len(sub_arr) <= 1:
                return sub_arr

            pivot_item = sub_arr[len(sub_arr) // 2]
            p_val = key_func(pivot_item)

            left, middle, right = [], [], []
            for item in sub_arr:
                comparisons[0] += 1
                val = key_func(item)
                if val == p_val:
                    middle.append(item)
                elif (val > p_val if reverse else val < p_val):
                    left.append(item)
                else:
                    right.append(item)
                moves[0] += 1

            steps.append({
                'depth': depth,
                'pivot': pivot_item.get(key_field),
                'action': f"Pivot '{pivot_item.get(key_field)}': Partitioned into {len(left)} (left), {len(middle)} (equal), {len(right)} (right)"
            })

            return tracked_quick_sort(left, depth + 1) + middle + tracked_quick_sort(right, depth + 1)

        sorted_result = tracked_quick_sort(arr)
        complexity = "O(n log n) Avg, O(n²) Worst"

    elapsed_ms = (time.perf_counter() - start_time) * 1000

    return {
        'algorithm': 'Merge Sort' if algorithm.lower() == 'merge' else 'Quick Sort',
        'key_field': key_field,
        'order': 'Descending' if reverse else 'Ascending',
        'time_complexity': complexity,
        'total_items': len(items),
        'comparisons': comparisons[0],
        'moves_or_swaps': moves[0],
        'elapsed_ms': round(elapsed_ms, 3),
        'steps': steps[:15], # cap at top 15 steps for compact UI display
        'sorted_items': sorted_result
    }
