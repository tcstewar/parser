import numpy as np
import math

import pointer

class Vocabulary(object):
    def __init__(self, dimensions, randomize=True, unitary=False, 
                       max_similarity=0.1, include_pairs=False, 
                       include_identity=True):
        self.dimensions = dimensions
        self.randomize = randomize
        self.unitary = unitary
        self.max_similarity = max_similarity
        self.pointers={}
        if include_identity:
            self.pointers['I'] = pointer.SemanticPointer(data=np.eye(dimensions)[0])
        self.keys=[]
        self.key_pairs=[]
        self.vectors=None
        self.vector_pairs=None
        self.include_pairs=include_pairs
        self._zero = None
        
    def create_pointer(self, attempts=100):
        if self.randomize:  
            count = 0
            p = pointer.SemanticPointer(self.dimensions)                
            while count<100 and self.vectors is not None:
                similarity = np.dot(self.vectors,p.v)
                if max(similarity) < self.max_similarity:
                    break
                p = pointer.SemanticPointer(self.dimensions)
                count += 1
            if count >= 100:        
                print 'Warning: Could not create a semantic pointer ' + \
                       'with max_similarity=%1.2f (D=%d, M=%d)' % \
                       (self.max_similarity,self.dimensions,len(self.pointers))
            
            # Check and make vector unitary if needed
            if self.unitary is True or (isinstance(self.unitary,list) and key in self.unitary):
                p.make_unitary()
        else:
            ov = [0]*self.dimensions
            ov[len(self.pointers)]=1.0
            p = pointer.SemanticPointer(data = ov)
        return p        
        
    def __getitem__(self,key):
        if key not in self.pointers:
            p = self.create_pointer()
            self.add(key, p)
        return self.pointers[key]        

    def add(self, key, p):
        if not isinstance(p, pointer.SemanticPointer):
            p = pointer.SemanticPointer(data=p)
        
        assert key not in self.pointers
        self.pointers[key] = p
        self.keys.append(key)
        if self.vectors is None:
            self.vectors = np.array([p.v])
        else:
            self.vectors = np.resize(self.vectors,(len(self.keys),self.dimensions))
            self.vectors[-1,:] = p.v
            
            # Generate vector pairs 
            if(self.include_pairs or self.vector_pairs is not None):
                for k in self.keys[:-1]:
                    self.key_pairs.append('%s*%s'%(k,key))
                    v = (self.pointers[k]*p).v
                    if self.vector_pairs is None:
                        self.vector_pairs = np.array([v])
                    else:    
                        self.vector_pairs=np.resize(self.vector_pairs,(len(self.key_pairs),self.dimensions))
                        self.vector_pairs[-1,:] = v
        
    def generate_pairs(self):
        """ This function is intended to be used in situations where a vocabulary has already been
        created without including pairs, but it becomes necessary to have the pairs (for graphing
        in interactive plots, for example). This is essentially identical to the add function above,
        except that it makes all the pairs in one pass (and without adding new vectors).
        """
        self.key_pairs = []
        self.vector_pairs = None
        for i in range(1, len(self.keys)):
            for k in self.keys[:i]:
                key = self.keys[i]
                self.key_pairs.append('%s*%s'%(k,key))
                v=(self.pointers[k]*self.pointers[key]).v
                if self.vector_pairs is None:
                    self.vector_pairs=np.array([v])
                else:    
                    self.vector_pairs=np.resize(self.vector_pairs,(len(self.key_pairs),self.dimensions))
                    self.vector_pairs[-1,:]=v

    def parse(self, text):
        value = eval(text, {}, self)
        if value == 0:
            value = self.zero
        if not isinstance(value, pointer.SemanticPointer):  
            raise Exception('Vocabulary parsing error: result of "%s" was not a semantic pointer'%text)
        return value
        
    @property
    def zero(self):
        if self._zero is None:
            self._zero = pointer.SemanticPointer(data=np.zeros(self.dimensions))
        return self._zero    
        
    def text(self, v, threshold=0.1, minimum_count=1, include_pairs=True, 
                   join='+', maximum_count=5, terms=None, normalize=False):
        if isinstance(v, pointer.SemanticPointer): 
            v = v.v
            
        if v is None or self.vectors is None: 
            return ''        
            
        if normalize:
            nrm = norm(v)
            if nrm>0: v /= nrm
        
        m = np.dot(self.vectors, v)
        matches = [(m[i], self.keys[i]) for i in range(len(m))]
        if include_pairs:
            if self.vector_pairs is None: self.generate_pairs()
            # vector_pairs may still be None after generate_pairs (if there is only 1 vector)
            if self.vector_pairs is not None:
                m2 = np.dot(self.vector_pairs, v)
                matches.extend([(m2[i],self.key_pairs[i]) for i in range(len(m2))])
        if terms is not None:
            matches = [m for m in matches if m[1] in terms]
        matches.sort()
        matches.reverse()

        r=[]        
        for m in matches:
            if threshold is None or (m[0]>threshold and len(r)<maximum_count): 
                r.append(m)
            elif len(r)<minimum_count: 
                r.append(m)
            else: break
            
        return join.join(['%0.2f%s'%(c,k) for (c,k) in r])

    def dot(self, v):
        if isinstance(v,pointer.SemanticPointer): v=v.v
        return np.dot(self.vectors, v)

    def dot_pairs(self,v):
        if len(self.keys)<2: 
            return None # There are no pairs.
        if isinstance(v, pointer.SemanticPointer): 
            v=v.v
        if self.vector_pairs is None: 
            self.generate_pairs()
        return np.dot(self.vector_pairs, v)

    def transform_to(self, other, keys=None):
        if keys is None:
            keys = set(self.keys)
            keys = keys | set(other.keys)
            
            #keys = [k for f in self.keys if k in other.keys]
        t = np.zeros((other.dimensions,self.dimensions),dtype='f')
        for k in keys:
            a = self[k].v
            b = other[k].v
            t += np.array([a*bb for bb in b])
        return t
        
    def prob_cleanup(self,compare,vocab_size,steps=10000):
        # see http://yamlb.wordpress.com/2008/05/20/why-2-random-vectors-are-orthogonal-in-high-dimention/ 
        #  for argument that the probability of two random vectors being a given angle apart is
        #  proportional to sin(angle)^(D-2)
        def prob_func(angle): 
            return math.sin(angle)**(self.dimensions-2)
        angle = math.acos(compare)
        num = 0
        dnum = angle/steps
        denom = 0
        ddenom = math.pi/steps
        for i in range(steps):
            num += prob_func(math.pi - angle + dnum*i)
            denom += prob_func(ddenom*i)
        num *= dnum
        denom *= ddenom    
        perror1 = num / denom    
        pcorrect = (1 - perror1)**vocab_size
        return pcorrect
        
        
        
