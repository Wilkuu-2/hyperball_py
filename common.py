from typing import List, Self

class FreqDistribution:
    __slots__ = ('arr')
    def __init__(self, initial: int):
        self.arr: List[int] = [0 for _ in range(initial)]
    
    def add(self, n: int, c: int = 1): 
        self._resize(n+1)
        self.arr[n] += c

    def _resize(self, n: int):
        al = len(self.arr)
        if n > al: 
            dl = n - al
            self.arr.extend([0 for _ in range(dl)])

    def merge_ip(self, other: Self): 
        self._resize(len(other))
        for i in range(len(other)):
            self.arr[i] += other.arr[i]

    def avg(self) -> float: 
        s = 0 
        c = 0
        for i in range(len(self.arr)): 
            v = self.arr[i]
            s += v * i 
            c += v 

        return s / c

    def count(self) -> int: 
        return sum(self.arr)

    def half(self): 
        for i in range(len(self.arr)): 
            self.arr[i] = self.arr[i] >> 1 
    def __len__(self): 
        return len(self.arr)

    @staticmethod
    def merge(x,y):
        u = FreqDistribution(max(len(x.arr),len(y.arr))) 
        u.merge_ip(x)
        u.merge_ip(y)
        return u 

            
