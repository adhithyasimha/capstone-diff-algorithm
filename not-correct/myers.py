import re

def tokenize(text):
    """Splits text into words while preserving spaces and punctuation."""
    return re.findall(r'\S+|\s+', text)

def myers_diff(old_text, new_text):
    old_words = tokenize(old_text)
    new_words = tokenize(new_text)
    
    n, m = len(old_words), len(new_words)
    v = {0: 0}
    trace = []
    
    for d in range(n + m + 1):
        trace.append(v.copy())
        for k in range(-d, d + 1, 2):
            if k == -d or (k != d and v.get(k - 1, -1) < v.get(k + 1, -1)):
                x = v.get(k + 1, 0)  # Default to 0 if k+1 is missing

            else:
                x = v[k - 1] + 1
            y = x - k
            
            while x < n and y < m and old_words[x] == new_words[y]:
                x += 1
                y += 1
            
            v[k] = x
            
            if x >= n and y >= m:
                return backtrack(trace, old_words, new_words)
    
    return ""  # Shouldn't reach here

def backtrack(trace, old_words, new_words):
    old_index, new_index = len(old_words), len(new_words)
    result = []
    
    for d in range(len(trace) - 1, -1, -1):
        v = trace[d]
        k = old_index - new_index
        
        if k == -d or (k != d and v.get(k - 1, -1) < v.get(k + 1, -1)):
            prev_k = k + 1
        else:
            prev_k = k - 1
        
        x_start, y_start = v[prev_k], v[prev_k] - prev_k
        x_mid = v.get(k, 0)  # Default to 0 if k is missing
        y_mid = x_mid - k

        
        while x_mid > x_start and y_mid > y_start:
            result.append(old_words[x_mid - 1])
            x_mid -= 1
            y_mid -= 1
        
        if x_mid > x_start:
            result.append(f'[- {old_words[x_mid - 1]} -]')
        elif y_mid > y_start:
            result.append(f'{{+ {new_words[y_mid - 1]} +}}')
        
        old_index, new_index = x_start, y_start
    
    return " ".join(reversed(result))

if __name__ == "__main__":
    old_text = "The quick brown fox jumps over the lazy dog."
    new_text = "The quick white fox jumps over a lazy dog."
    
    diff = myers_diff(old_text, new_text)
    print(diff)
