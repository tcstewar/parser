import numpy as np
from numpy.fft import fft
from numpy.fft import ifft
from numpy.linalg import norm

class SemanticPointer:
    def __init__(self, N=None, data=None):
        if data is not None:
            self.v = np.array(data)
        elif N is not None:
            self.randomize(N)
        else:
            raise Exception('Must specify size or data for Semantic Pointer')
            
    def length(self):
        return norm(self.v)        
        
    def normalize(self):
        nrm = np.linalg.norm(self.v)        
        if nrm>0: self.v/=nrm
        
    def __str__(self):
        return str(self.v)
        
    def randomize(self, N=None):
        if N is None: N=len(self.v)
        self.v=np.random.randn(N)
        self.normalize()
        
    def make_unitary(self):
        fft_val = fft(self.v)
        fft_imag = fft_val.imag
        fft_real = fft_val.real
        fft_norms = np.sqrt(fft_imag**2 + fft_real**2)
        fft_unit = fft_val / fft_norms
        self.v = (ifft(fft_unit)).real
        
    def __add__(self, other):
        return SemanticPointer(data=self.v + other.v)
        
    def __iadd__(self, other):
        self.v += other.v
        return self
        
    def __neg__(self):
        return SemanticPointer(data=-self.v)    
        
    def __sub__(self, other):
        return SemanticPointer(data=self.v - other.v)
        
    def __isub__(self, other):
        self.v -= other.v
        return self
        
    def __mul__(self, other):
        if isinstance(other, SemanticPointer):
            return self.convolve(other)
        else:
            return SemanticPointer(data=self.v * other)
            
    def convolve(self, other):
        x=ifft(fft(self.v) * fft(other.v)).real
        return SemanticPointer(data=x)
        
    def __rmul__(self, other):
        if isinstance(other, SemanticPointer):
            return self.convolve(other)
        else:
            return SemanticPointer(data=self.v * other)
            
    def __imul__(self, other):
        self.v = ifft(fft(self.v) * fft(other.v)).real
        return self
        
    def compare(self, other):
        scale = norm(self.v) * norm(other.v)
        if scale==0: return 0
        return np.dot(self.v, other.v) / scale
        
    def dot(self, other):
        return np.dot(self.v, other.v)
        
    def distance(self, other):
        return 1 - self.compare(other)
        
    def __invert__(self):
        N = len(self.v)
        return SemanticPointer(data=[self.v[0]] + [self.v[N-i] for i in range(1,N)])
        
    def __len__(self):
        return len(self.v)
        
    def copy(self):
        return SemanticPointer(data=self.v)
        
    def mse(self, other):
        err = 0
        for i in range(len(self.v)):
            err += (self.v[i] - other.v[i])**2
        return err / len(self.v)
        
    def get_convolution_matrix(self):
        D = len(self.v)
        T = []
        for i in range(D):
            T.append([self.v[(i-j)%D] for j in range(D)])
        return np.array(T)
    
