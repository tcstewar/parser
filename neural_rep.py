D=8
Dsub=2
N=50
tau=0.1

import nengo
import pointer

value = pointer.SemanticPointer(D)

model = nengo.Model()
with model:
    def input_func(t):
        if t<0.1:
            return value.v
        else:
            return value.v*0

    input = nengo.Node(value.v)
    buffer = nengo.networks.EnsembleArray(N/Dsub, D/Dsub, dimensions=Dsub)
    nengo.Connection(input, buffer.input, filter=None)
    nengo.Connection(buffer.output, buffer.input, filter=tau)
    
    probe = nengo.Probe(buffer.output, 'output', filter=tau)
    
sim = nengo.Simulator(model)
sim.run(1)

value2 = pointer.SemanticPointer(data=sim.data(probe)[-1])
value2.normalize()
# amount of "noise" in a similar sense as the noise added in the lcparser
print (value2-value).norm()

#import pylab
#pylab.plot(sim.data(probe))
#pylab.show()    