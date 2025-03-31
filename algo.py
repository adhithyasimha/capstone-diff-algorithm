from typing import List, Tuple, Dict, Optional

XDL_MAX_COST_MIN = 256
XDL_HEUR_MIN_COST = 256
XDL_SNAKE_CNT = 20
XDL_K_HEUR = 4

def xdl_bogosqrt(n: int) -> int:
    """Approximate square root - used for determining mxcost"""
    i = 1
    while i * i < n:
        i *= 2
    while i * i > n:
        i -= 1
    return i

class XDFile:
    """Represents a file being diffed (simplified version of xdfile_t)"""
    def __init__(self, text: str):
        self.lines = text.splitlines(keepends=True)
        self.nrec = len(self.lines)
        self.rchg = [False] * (self.nrec + 2)  # Changed flags (+2 for sentinels)
        
        # In the real implementation, we'd compute hashes here
        self.ha = [hash(line) for line in self.lines]

class XDPSplit:
    """Represents a split point in the diff algorithm"""
    def __init__(self):
        self.i1 = 0
        self.i2 = 0
        self.min_lo = 0
        self.min_hi = 0

class XDLAlgoEnv:
    """Algorithm environment parameters"""
    def __init__(self):
        self.mxcost = 0
        self.snake_cnt = XDL_SNAKE_CNT
        self.heur_min = XDL_HEUR_MIN_COST

def xdl_split(ha1: List[int], off1: int, lim1: int,
              ha2: List[int], off2: int, lim2: int,
              kvdf: Dict[int, int], kvdb: Dict[int, int],
              need_min: bool, spl: XDPSplit, xenv: XDLAlgoEnv) -> int:
    """Myers algorithm to find a splitting point"""
    dmin = off1 - lim2
    dmax = lim1 - off2
    fmid = off1 - off2
    bmid = lim1 - lim2
    odd = (fmid - bmid) & 1
    fmin = fmid
    fmax = fmid
    bmin = bmid
    bmax = bmid
    
    # Initialize forward and backward k vectors
    kvdf[fmid] = off1
    kvdb[bmid] = lim1
    
    for ec in range(1, 1000000):  # Prevent infinite loops
        got_snake = False
        
        # Forward path
        if fmin > dmin:
            fmin -= 1
            kvdf[fmin - 1] = -1
        else:
            fmin += 1
        if fmax < dmax:
            fmax += 1
            kvdf[fmax + 1] = -1
        else:
            fmax -= 1
            
        for d in range(fmax, fmin - 1, -2):
            if kvdf.get(d - 1, -1) >= kvdf.get(d + 1, -1):
                i1 = kvdf[d - 1] + 1
            else:
                i1 = kvdf.get(d + 1, -1)
            prev1 = i1
            i2 = i1 - d
            
            # Find snake
            while i1 < lim1 and i2 < lim2 and ha1[i1] == ha2[i2]:
                i1 += 1
                i2 += 1
                
            if i1 - prev1 > xenv.snake_cnt:
                got_snake = True
                
            kvdf[d] = i1
            
            if odd and bmin <= d <= bmax and kvdb.get(d, float('inf')) <= i1:
                spl.i1 = i1
                spl.i2 = i2
                spl.min_lo = spl.min_hi = 1
                return ec
                
        # Backward path
        if bmin > dmin:
            bmin -= 1
            kvdb[bmin - 1] = float('inf')
        else:
            bmin += 1
        if bmax < dmax:
            bmax += 1
            kvdb[bmax + 1] = float('inf')
        else:
            bmax -= 1
            
        for d in range(bmax, bmin - 1, -2):
            if kvdb.get(d - 1, float('inf')) < kvdb.get(d + 1, float('inf')):
                i1 = kvdb[d - 1]
            else:
                i1 = kvdb.get(d + 1, float('inf')) - 1
            prev1 = i1
            i2 = i1 - d
            
            # Find snake
            while i1 > off1 and i2 > off2 and ha1[i1 - 1] == ha2[i2 - 1]:
                i1 -= 1
                i2 -= 1
                
            if prev1 - i1 > xenv.snake_cnt:
                got_snake = True
                
            kvdb[d] = i1
            
            if not odd and fmin <= d <= fmax and i1 <= kvdf.get(d, -1):
                spl.i1 = i1
                spl.i2 = i2
                spl.min_lo = spl.min_hi = 1
                return ec
                
        if need_min:
            continue
            
        # Heuristic for large diffs
        if got_snake and ec > xenv.heur_min:
            best = 0
            # Check forward diagonals
            for d in range(fmax, fmin - 1, -2):
                dd = d - fmid if d > fmid else fmid - d
                i1 = kvdf.get(d, -1)
                i2 = i1 - d
                v = (i1 - off1) + (i2 - off2) - dd
                
                if (v > XDL_K_HEUR * ec and v > best and
                    off1 + xenv.snake_cnt <= i1 < lim1 and
                    off2 + xenv.snake_cnt <= i2 < lim2):
                    for k in range(1, xenv.snake_cnt + 1):
                        if ha1[i1 - k] != ha2[i2 - k]:
                            break
                        if k == xenv.snake_cnt:
                            best = v
                            spl.i1 = i1
                            spl.i2 = i2
                            break
                            
            if best > 0:
                spl.min_lo = 1
                spl.min_hi = 0
                return ec
                
            # Check backward diagonals
            best = 0
            for d in range(bmax, bmin - 1, -2):
                dd = d - bmid if d > bmid else bmid - d
                i1 = kvdb.get(d, float('inf'))
                i2 = i1 - d
                v = (lim1 - i1) + (lim2 - i2) - dd
                
                if (v > XDL_K_HEUR * ec and v > best and
                    off1 < i1 <= lim1 - xenv.snake_cnt and
                    off2 < i2 <= lim2 - xenv.snake_cnt):
                    for k in range(xenv.snake_cnt):
                        if ha1[i1 + k] != ha2[i2 + k]:
                            break
                        if k == xenv.snake_cnt - 1:
                            best = v
                            spl.i1 = i1
                            spl.i2 = i2
                            break
                            
            if best > 0:
                spl.min_lo = 0
                spl.min_hi = 1
                return ec
                
        # If we've searched too much, return the best we found
        if ec >= xenv.mxcost:
            # Find furthest reaching forward path
            fbest = fbest1 = -1
            for d in range(fmax, fmin - 1, -2):
                i1 = min(kvdf.get(d, -1), lim1)
                i2 = i1 - d
                if lim2 < i2:
                    i1 = lim2 + d
                    i2 = lim2
                if fbest < i1 + i2:
                    fbest = i1 + i2
                    fbest1 = i1
                    
            # Find furthest reaching backward path
            bbest = bbest1 = float('inf')
            for d in range(bmax, bmin - 1, -2):
                i1 = max(off1, kvdb.get(d, float('inf')))
                i2 = i1 - d
                if i2 < off2:
                    i1 = off2 + d
                    i2 = off2
                if i1 + i2 < bbest:
                    bbest = i1 + i2
                    bbest1 = i1
                    
            if (lim1 + lim2) - bbest < fbest - (off1 + off2):
                spl.i1 = fbest1
                spl.i2 = fbest - fbest1
                spl.min_lo = 1
                spl.min_hi = 0
            else:
                spl.i1 = bbest1
                spl.i2 = bbest - bbest1
                spl.min_lo = 0
                spl.min_hi = 1
            return ec
            
    return -1  # Shouldn't reach here

def xdl_recs_cmp(dd1: XDFile, off1: int, lim1: int,
                 dd2: XDFile, off2: int, lim2: int,
                 kvdf: Dict[int, int], kvdb: Dict[int, int],
                 need_min: bool, xenv: XDLAlgoEnv) -> int:
    """Recursively compare two sequences using Myers algorithm"""
    ha1 = dd1.ha
    ha2 = dd2.ha
    
    # Trim common head and tail
    while off1 < lim1 and off2 < lim2 and ha1[off1] == ha2[off2]:
        off1 += 1
        off2 += 1
    while off1 < lim1 and off2 < lim2 and ha1[lim1 - 1] == ha2[lim2 - 1]:
        lim1 -= 1
        lim2 -= 1
        
    # If one side is empty, mark all on the other side as changed
    if off1 == lim1:
        for i in range(off2, lim2):
            dd2.rchg[i] = True
        return 0
    elif off2 == lim2:
        for i in range(off1, lim1):
            dd1.rchg[i] = True
        return 0
    else:
        spl = XDPSplit()
        if xdl_split(ha1, off1, lim1, ha2, off2, lim2, kvdf, kvdb, need_min, spl, xenv) < 0:
            return -1
            
        # Recurse on both halves
        if (xdl_recs_cmp(dd1, off1, spl.i1, dd2, off2, spl.i2, kvdf, kvdb, spl.min_lo, xenv) < 0 or
            xdl_recs_cmp(dd1, spl.i1, lim1, dd2, spl.i2, lim2, kvdf, kvdb, spl.min_hi, xenv) < 0):
            return -1
            
    return 0

def myers_diff(text1: str, text2: str) -> Tuple[List[bool], List[bool]]:
    """Compute differences between two texts using Myers algorithm"""
    dd1 = XDFile(text1)
    dd2 = XDFile(text2)
    
    # Allocate and setup K vectors
    ndiags = dd1.nrec + dd2.nrec + 3
    kvdf = {}
    kvdb = {}
    
    # Initialize algorithm environment
    xenv = XDLAlgoEnv()
    xenv.mxcost = xdl_bogosqrt(ndiags)
    if xenv.mxcost < XDL_MAX_COST_MIN:
        xenv.mxcost = XDL_MAX_COST_MIN
    xenv.snake_cnt = XDL_SNAKE_CNT
    xenv.heur_min = XDL_HEUR_MIN_COST
    
    # Perform the diff
    if xdl_recs_cmp(dd1, 0, dd1.nrec, dd2, 0, dd2.nrec, kvdf, kvdb, False, xenv) < 0:
        raise RuntimeError("Diff computation failed")
    
    return dd1.rchg, dd2.rchg

def highlight_diff(text1: str, text2: str) -> str:

    lines1 = text1.splitlines(keepends=True)
    lines2 = text2.splitlines(keepends=True)
    
    # Get the diff
    rchg1, rchg2 = myers_diff(text1, text2)
    
    # ANSI color codes
    RED = '\033[91m'
    GREEN = '\033[92m'
    END = '\033[0m'
    
    result = []
    i1 = 0
    i2 = 0
    
    while i1 < len(lines1) or i2 < len(lines2):
        if i1 < len(lines1) and rchg1[i1]:
            # Deleted line
            result.append(f"{RED}- {lines1[i1].rstrip()}{END}")
            i1 += 1
        elif i2 < len(lines2) and rchg2[i2]:
            # Added line
            result.append(f"{GREEN}+ {lines2[i2].rstrip()}{END}")
            i2 += 1
        else:
            # Unchanged line
            if i1 < len(lines1) and i2 < len(lines2):
                result.append(f"  {lines1[i1].rstrip()}")
                i1 += 1
                i2 += 1
            elif i1 < len(lines1):
                result.append(f"{RED}- {lines1[i1].rstrip()}{END}")
                i1 += 1
            elif i2 < len(lines2):
                result.append(f"{GREEN}+ {lines2[i2].rstrip()}{END}")
                i2 += 1
    
    return '\n'.join(result)

def find_difference(text1, text2):
    if text2.startswith(text1):
        return text2[len(text1):]  # Extract the extra part in 'b'
    return text2  # If 'b' does not start with 'a', return 'b' as the difference



# Example usage
if __name__ == "__main__":

    text1 = "hello world"
    
    text2 = "hello"

    difference = find_difference(text1,text2)
    print(highlight_diff(text1, text2))

