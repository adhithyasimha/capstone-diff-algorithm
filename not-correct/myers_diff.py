def compute_code_changes(previous_code_log, current_code_log):
    previous_code = previous_code_log["code"]
    current_code = current_code_log["code"]
    
    if previous_code == current_code:
        return "No change"
    
    # Split into lines
    a = previous_code.splitlines()
    b = current_code.splitlines()
    n, m = len(a), len(b)
    
    # Maximum edit distance (n + m covers all possible changes)
    max_d = n + m
    v = [0] * (2 * max_d + 1)  # Store x-coordinates for each diagonal
    v[max_d + 1] = 0  # Offset for k=1 (diagonal starting point)
    trace = []  # Store v arrays for backtracking
    
    # Myers algorithm: Forward pass
    for d in range(max_d + 1):
        v_copy = v.copy()  # Save state for backtracking
        trace.append(v_copy)
        
        for k in range(-d, d + 1, 2):
            k_idx = k + max_d
            
            # Decide whether to move down (delete) or right (insert)
            if k == -d or (k != d and v[k_idx - 1] < v[k_idx + 1]):
                x = v[k_idx + 1]  # Move down
            else:
                x = v[k_idx - 1] + 1  # Move right
            
            y = x - k
            
            # Follow matching lines (snake)
            while x < n and y < m and a[x] == b[y]:
                x += 1
                y += 1
            
            v[k_idx] = x
            
            # Reached the end
            if x >= n and y >= m:
                # Backtrack to compute changes
                changes = []
                i, j = n, m
                for depth in range(d, -1, -1):
                    k = i - j
                    k_idx = k + max_d
                    
                    # Reconstruct the path
                    if depth > 0:
                        if k == -depth or (k != depth and trace[depth-1][k_idx - 1] < trace[depth-1][k_idx + 1]):
                            prev_x = trace[depth-1][k_idx + 1]
                            prev_y = prev_x - (k + 1)
                        else:
                            prev_x = trace[depth-1][k_idx - 1] + 1
                            prev_y = prev_x - (k - 1)
                    else:
                        prev_x, prev_y = 0, 0
                    
                    # Add changes based on current position
                    while i > prev_x and j > prev_y:
                        if a[i-1] == b[j-1]:
                            i -= 1
                            j -= 1
                        else:
                            break
                    
                    if i > prev_x:
                        changes.append(f"- '{a[i-1]}'")
                        i -= 1
                    elif j > prev_y:
                        changes.append(f"+ '{b[j-1]}'")
                        j -= 1
                
                changes.reverse()
                return "\n".join(changes) if changes else "No change"
    
    return "No change"  