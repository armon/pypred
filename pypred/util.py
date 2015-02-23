"""
Various utility methods that are used
"""
import heapq
from collections import defaultdict

def mode(lst):
    "Returns the most common value"
    # Count each item
    counts = defaultdict(int)
    for x in lst:
        counts[x] += 1

    # Determine the maximum count
    max = 0
    item = None
    for val, count in counts.items():
        if count > max:
            max = count
            item = val

    # Return the most common
    return item

def median(lst):
    "Returns the median value"
    # Sort
    lst.sort()

    # Get the middle index
    middle = len(lst) // 2
    return lst[middle]

def max_count(count):
    "Generator for the keys with the maximum value"
    vals = []
    orig_names = {}
    for n,c in count.items():
        orig_names[str(n)] = n
        vals.append((-c, str(n)))

    heapq.heapify(vals)
    while len(vals):
        c, n = heapq.heappop(vals)
        yield (-c, orig_names[n])

def harmonic_mean(lst):
    "Returns the harmonic mean. Will crash if any value is zero."
    n = len(lst)
    inv_sum = sum((1.0 / x) for x in lst)
    return (1.0 / ((1.0 / n) * inv_sum))

