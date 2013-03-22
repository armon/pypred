"""
Various utility methods that are used
"""
from collections import defaultdict

def mode(lst):
    "Returns the most common value"
    # Count each item
    counts = defaultdict(0)
    for x in lst:
        counts[x] += 1

    # Determine the maximum count
    max = 0
    item = None
    for count, val in counts.iteritems():
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

