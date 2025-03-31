import time
def myers_diff(a, b):
    """
    Implements Myers' diff algorithm to find the shortest edit script between two lists.
    Returns a list of operations (insert, delete, Same) to transform list a into list b.
    """
    # Split sentences into words
    a = a.split()
    b = b.split()

    # Initialize the edit graph
    max_edit = len(a) + len(b)
    v = {1: 0}
    trace = []

    # Find the shortest path through the edit graph
    for d in range(max_edit + 1):
        trace.append(v.copy())
        for k in range(-d, d + 1, 2):
            if k == -d or (k != d and v.get(k - 1, -1) < v.get(k + 1, -1)):
                x = v.get(k + 1, -1)
            else:
                x = v.get(k - 1, -1) + 1

            y = x - k

            # Follow diagonal matches as far as possible
            while x < len(a) and y < len(b) and a[x] == b[y]:
                x += 1
                y += 1

            v[k] = x

            # Check if we've reached the end
            if x >= len(a) and y >= len(b):
                # Build the edit script
                return backtrack(a, b, trace, d)

    return []  # Should never reach here

def backtrack(a, b, trace, d):
    """
    Backtrack through the edit graph to find the edit script.
    """
    x, y = len(a), len(b)
    edit_script = []

    for _d in range(d, 0, -1):
        v = trace[_d]
        k = x - y

        if k == -_d or (k != _d and v.get(k - 1, -1) < v.get(k + 1, -1)):
            k_prev = k + 1
        else:
            k_prev = k - 1

        x_prev = v.get(k_prev, -1)
        y_prev = x_prev - k_prev

        while x > x_prev and y > y_prev:
            # Diagonal move - kept word
            edit_script.append(("Same", a[x-1]))
            x -= 1
            y -= 1

        if x > x_prev:
            # Horizontal move - deleted word
            edit_script.append(("delete", a[x-1]))
            x -= 1
        elif y > y_prev:
            # Vertical move - inserted word
            edit_script.append(("insert", b[y-1]))
            y -= 1

    # Handle any remaining diagonal moves at the start
    while x > 0 and y > 0:
        if a[x-1] == b[y-1]:
            edit_script.append(("Same", a[x-1]))
        else:
            edit_script.append(("replace", a[x-1], b[y-1]))
        x -= 1
        y -= 1

    # Handle any remaining words
    while x > 0:
        edit_script.append(("delete", a[x-1]))
        x -= 1

    while y > 0:
        edit_script.append(("insert", b[y-1]))
        y -= 1

    return list(reversed(edit_script))

def display_diff(sentence1, sentence2):
    """
    Display readable diff between two sentences and measure performance
    """
    # Measure execution time
    start_time = time.perf_counter()
    diff = myers_diff(sentence1, sentence2)
    end_time = time.perf_counter()
    
    # Calculate elapsed time in microseconds
    elapsed_microseconds = (end_time - start_time) * 1_000_000
    
    print("Differences:")
    for op in diff:
        if op[0] == "Same":
            print(f"  Same: '{op[1]}'")
        elif op[0] == "delete":
            print(f"- Delete: '{op[1]}'")
        elif op[0] == "insert":
            print(f"+ Insert: '{op[1]}'")
        elif op[0] == "replace":
            print(f"~ Replace: '{op[1]}' → '{op[2]}'")
    
    print(f"\nExecution time: {elapsed_microseconds:.2f} microseconds")

# Example usage
sentence1 = "heil"
sentence2 = "heil ,"

print("Sentence 1:", sentence1)
print("Sentence 2:", sentence2)
display_diff(sentence1, sentence2)
