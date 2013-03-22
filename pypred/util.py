"""
Various utility methods that are used
"""
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
    for val, count in counts.iteritems():
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
    middle = len(lst) / 2
    return lst[middle]

def max_count(count):
    "Returns the key with the maximum value"
    max_count = 0
    max_name = None
    for n, c in count.iteritems():
        if c > max_count:
            max_count = c
            max_name = n
    return (max_count, max_name)

