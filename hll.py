from hashlib import sha1; 
import math
from typing import Self, Tuple 
import random 

twopow32 = 1 << 32 
    
class HLLCounter: 
    __slots__ = ('b','m','M')
    def __init__(self, b): 
        self.b: int = b
        self.m: int = 2 ** b 
        self.M = [0 for _ in range(0,self.m)]

    def add(self, v: bytes):
        right_offset = 63 - self.b 
        mask = ((1 << (right_offset +1)) - 1) 

        # Split the value to get the indexing part and the value part
        h = int.from_bytes(sha1(v).digest()[:8])
        
        hi = (h & ~mask) >> (right_offset + 1)
        hv = h & mask 
        
        # get the position of the 1st '1' in hv 
        p_hv = 65 - self.b - hv.bit_length()

        # Put the bigger value in 
        self.M[hi] = max(self.M[hi], p_hv) 

    
    def getE(self) -> float: 
        # Calculate raw estimate
        est = sum([1.0 / float(1 << Mj) for Mj in self.M])
        est = get_alpha(self.m) * (self.m * self.m) / est 

        zeroes = self.M.count(0)
        if est < 2.5 * self.m and zeroes > 0: 
            est = self.m * math.log(self.m/zeroes)
        elif est > 1/30 * twopow32:  
            est = self.m * math.log(1.0 - est/twopow32)

        return est 
    
    def copy(self): 
        out = HLLCounter(self.b)
        out.M = self.M.copy()
        return out

    def union_ip(self, y) -> bool: 
        assert self.b == y.b, "UNION: Both counters need the same precision"
        is_changed = False

        for j in range(0,self.m):
            xMj = self.M[j] 
            yMj = y.M[j]

            if xMj != yMj:
                self.M[j] = max(xMj, yMj)
                is_changed = True
            else:
                self.M[j] = xMj

        return is_changed
    
    def __repr__(self) -> str:
        return f"HLLCounter{self.b}"



# Get the correcting factor from the paper 
def get_alpha(m): 
    assert (16 <= m <= 65536), "GET_ALPHA: Invalid precision" 
    if m == 16:
        return 0.673
    if m == 32:
        return 0.697
    if m == 64:
        return 0.709
    return 0.7213 / (1.0 + 1.079 / m)
            


def seed_counter(begin: int, stop: int, c: HLLCounter):
    for i in range(begin, stop): 
        [c.add(i.to_bytes(8)) for _ in range(0,random.randint(5,50))]

def test(): 
    c = HLLCounter(12) 
    random.seed(0xdeadbeef) 

    seed_counter(0, 2000, c)
    print(c.getE())
    
    d = HLLCounter(12) 
    seed_counter(2000, 12000, d)

    print(d.getE()) 

    ch = d.union_ip(c)
    assert ch, "TEST_UNION: The union should yield a changed counter" 

    print(d.getE())

    


if __name__ == "__main__": 
    test() 
        
        
        
        
    
