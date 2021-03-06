import nef

from ca.nengo.model import Units
from ca.nengo.model import SimulationMode
from ca.nengo.model.impl import NetworkImpl
from ca.nengo.model.impl import EnsembleOrigin
from ca.nengo.model.impl import EnsembleTermination
from ca.nengo.math.impl import PostfixFunction
from ca.nengo.math.impl import IndicatorPDF
from ca.nengo.math import PDFTools

from util_nodes import *
from util_funcs import *
from random import *
from math import *
from copy import deepcopy
from threshold_detect import Detector

# These classes enable the construction of cleanup memory units in Nengo.
# Two classes are provided, one that constructs a simple node implementation of
# cleanup memory, and one that constructs a neuron-based implementation of 
# cleanup memory. 
#
# The function of a (regular) cleanup memory unit is to compare the input 
# vector to a list of pre-defined vectors within the cleanup vocabulary, and
# determine which of these vectors best matches the input vector. 
# Note that the classes allow for the creation of both associative and 
# auto-associative (i.e. "regular") cleanup memories.
# 
# Auto-associative (regular) cleanup memory:
# - In an auto-associative cleanup memory, both the input vector vocabulary
#   and the output vector vocabulary are identical. 
#                          { Vector 1   } <=>    { Vector 1   }
#                          { Vector 2   } <=>    { Vector 2   }
# Input Vector --> dot_prod{ Vector ... } <=> max{ Vector ... } --> Output Vector
#                          { Vector N-1 } <=>    { Vector N-1 }
#                          { Vector N   } <=>    { Vector N   }
#
# Associative cleanup memory:
# - In an associative cleanup memory, the output vector vocabulary is different
#   than the input vector vocabulary. Note: Vectors can differ in dimensions as
#   well.
#                          { Vector 1   } <=>    { Vector A   }
#                          { Vector 2   } <=>    { Vector B   }
# Input Vector --> dot_prod{ Vector ... } <=> max{ Vector ... } --> Output Vector
#                          { Vector N-1 } <=>    { Vector M-1 }
#                          { Vector N   } <=>    { Vector M   }


# Cleanup memory simple node class. Use this to create a simple node version of 
# cleanup memory. Note that this class is used by the NEF network class below
# to create a direct mode version of the cleanup memory. (i.e. to make your code
# more flexible, create the cleanup memory using the class below, and set the 
# simulation mode to "DIRECT")
# The simplenode created has two terminations and two origins:
# Terminations:
# - Input: Input (to cleanup memory) vector goes here.
# - Inhib: Single dimensional input, set to 1 to inhibit (i.e. turn off) the cleanup 
#          memory node. Note: en_inhib has to be True.
# Origins:
# - Output: Vector within the cleanup vocabulary that is most like the input vector. 
# - X:      Vector that contains the dot product values of the input vector to each
#           vector in the cleanup vocabulary.
class CleanupMemoryNode(nef.SimpleNode):
    # Class initialization parameters -
    # - name:            Name of the node
    # - in_vec_list:     Input vocabulary list
    # - out_vec_list:    Output vocabulary list
    # - tau_in:          Post-synaptic time constant on the input
    # - en_inhib:        Set to True to enable inhib input
    # - tau_inhib:       Post-synaptic time constant on the inhib input
    # - inhib_threshold: Since this is running "direct" mode, this threshold is needed
    #                    to determine when to inhibit the output. If the input value on
    #                    the inhib termination exceeds this threshold, the output is 
    #                    inhibited.
    # - threshold:       Minimum threshold for the dot product result to generate a 
    #                    "winner" for the cleanup mechanism.
    # - en_wta:          Set to True to enable winner-take-all mode for the cleanup 
    #                    (this is default behaviour). Otherwise, the cleanup will take
    #                    the dot product result multiplied each corresponding dictionary
    #                    output vector.
    # - check_interval:  Interval in ms in which the simple node compares the input
    #                    vector to the dictionary vectors. 
    # - N_out_vec:       If not set to None, this will be used as the output when none
    #                    of the cleanup dictionary vectors meet the cleanup threshold.
    #                    If set to None, the cleanup output will be 0 if none of the 
    #                    cleanup dictionary vectors meet the cleanup threshold.
    def __init__(self, name, in_vec_list = None, out_vec_list = None, tau_in = 0.005, \
                 en_inhib = False, tau_inhib = 0.005, inhib_threshold = 0.2, \
                 threshold = 0.3, en_wta = True, check_interval = 0.01, \
                 N_out_vec = None):

        self.interval = check_interval
        self.next_check = 0

        self.in_vec_list = in_vec_list
        self.out_vec_list = out_vec_list
        self.en_N_out = not (N_out_vec is None)
        if( out_vec_list is None ):
            self.out_vec_list = in_vec_list
        if( N_out_vec is None ):
            self.N_out_vec = zeros(1, out_vec_list[0])
        
        self.dot_vals = zeros(1, len(out_vec_list))

        self.threshold = threshold

        self.num_items = len(in_vec_list)
        self.dimension = len(out_vec_list[0])
        self.max_vec = zeros(1, self.dimension)

        self.inhib = 0
        self.inhib_opt = en_inhib
        self.inhib_threshold = inhib_threshold

        # Option to output the sum of all of the vectors that exceed threshold (instead of the default max only output)
        self.en_wta = en_wta

        nef.SimpleNode.__init__(self, name)
        self.getTermination("Input").setDimensions(len(in_vec_list[0]))
        self.getTermination("Input").setTau(tau_in)
        self.getTermination("Inhib").setDimensions(1)
        self.getTermination("Inhib").setTau(tau_inhib)

        if( not en_inhib ):
            self.removeTermination("Inhib")
    
    # Simple node function to create "Input" termination
    def termination_Input(self, x):
        if( self.t_end >= self.next_check ):
            N_dot = 0
            dot_prods = [util_funcs.dot(x, self.in_vec_list[n], False) for n in range(self.num_items)]
            if( not self.en_wta ):
                dot_prods = [dot_prods[n] * (dot_prods[n] >= self.threshold) for n in range(self.num_items)]
                self.max_vec = util_funcs.zeros(1, self.dimension)
                for item in range(self.num_items):
                    self.max_vec = util_funcs.ew_sum(self.max_vec, [dot_prods[item] * self.out_vec_list[item][d] for d in range(self.dimension)])
            else:
                max_dot = max(dot_prods)
                if( max_dot >= self.threshold ): 
                    max_dots = [(dot_prods[d] == max_dot) * (d + 1) for d in range(self.num_items)]
                    max_item = sum(max_dots)
                else:
                    max_item = 0
            
                if( max_item > self.num_items or max_item <= 0 ):
                    self.max_vec = self.N_out_vec
                    N_dot = 1
                else:
                    self.max_vec = self.out_vec_list[max_item - 1]
            
            self.dot_vals = dot_prods
            if( self.en_N_out ):
                self.dot_vals.append(N_dot)
            self.next_check += self.interval
    
    # Simple node function to create "Inhib" termination
    def termination_Inhib(self, x):
        self.inhib = x[0]
    
    # Simple node function to create "Output" origin
    def origin_Output(self):
        if( self.inhib > self.inhib_threshold ):
            return util_funcs.zeros(1, self.dimension)
        else:
            return self.max_vec

    # Simple node function to create "X" origin
    def origin_X(self):
        return self.dot_vals
    
    # Reset function
    def reset(self, randomize = False):
        self.next_log = 0
        self.max_vec = util_funcs.zeros(1, self.dimension)
        nef.SimpleNode.reset(self, randomize)

    # releaseMemory function (for compatibility with regular NEF ensemble & network classes)
    def releaseMemory(self):
        pass

# Cleanup memory NEF network class. Use this to create a NEF network version of 
# cleanup memory. The NEF network created has two terminations and two origins:
# Terminations:
# - Input: Input (to cleanup memory) vector goes here.
# - Inhib: Single dimensional input, set to 1 to inhibit (i.e. turn off) the cleanup 
#          memory node. Note: en_inhib has to be True.
# Origins:
# - Output: Vector within the cleanup vocabulary that is most like the input vector. 
# - X:      Vector that contains the dot product values of the input vector to each
#           vector in the cleanup vocabulary.
class CleanupMem(NetworkImpl):
    # Class initialization parameters -
    # - name:                Name of the node
    # - in_vec_list:         Input vocabulary list
    # - out_vec_list:        Output vocabulary list
    # - tau_in:              Post-synaptic time constant on the input
    # - in_scale:            Scaling on the input termination.
    # - en_inhib:            Set to True to enable inhib input
    # - tau_inhib:           Post-synaptic time constant on the inhib input
    # - inhib_scale:         Scaling on the inhib termination. Setting a larger value will 
    #                        ensure that the cleanup memory output is inhibited at a faster
    #                        rate, however, recovery of the network when inhibition is 
    #                        released will be slower.
    # - inhib_threshold:     Since this is running "direct" mode, this threshold is needed
    #                        to determine when to inhibit the output. If the input value on
    #                        the inhib termination exceeds this threshold, the output is 
    #                        inhibited.
    # - en_mut_inhib:        Set to True to enable mutual inhibition between each ensemble
    #                        representing a vector in the dictionary. With mutual inhibition, the
    #                        cleanup memory tries to pick one winner (most of the time), but this
    #                        also means the result is slower. The default behaviour is to have 
    #                        this off. Otherwise, the cleanup will take the dot product result 
    #                        multiplied each corresponding dictionary output vector.
    # - mut_inhib_scale:     Scaling on the mutual inhibition connections. This is a tricky
    #                        value to set. Too high, and no output will be chosen, too low, and
    #                        multiple values will be chosen.
    # - num_neurons_per_vec: Number of neurons used to represent each vector in the vocabulary's
    #                        dictionary.
    # - threshold:           Minimum threshold for the dot product result to generate an
    #                        output for the cleanup mechanism.
    # - N_out_vec:           If not set to None, this will be used as the output when none
    #                        of the cleanup dictionary vectors meet the cleanup threshold.
    #                        If set to None, the cleanup output will be 0 if none of the 
    #                        cleanup dictionary vectors meet the cleanup threshold.
    # - en_X_out:            Set to True to enable the dot product value for each of the 
    #                        vectors in the vocabulary.
    # - input_name:          Name of the input termination (if you wish to change the name).
    # - sim_mode:            Simulation mode of the cleanup memory network. Note that if this is
    #                        set to "DIRECT" when the network is created, a simplenode implementation
    #                        will be used instead.
    # - quick:               Set to True to enable quick mode when creating the NEF ensembles.
    # - rand_seed:           Random seed used when creating the NEF ensembles.
    def __init__(self, name = "Cleanup Memory", \
                 in_vec_list = None, out_vec_list = None, tau_in = 0.005, in_scale = 1.0, \
                 en_inhib = False, tau_inhib = 0.005, tau_smooth = 0.0001, inhib_scale = 2.0, \
                 en_mut_inhib = False, mut_inhib_scale = 2.0, \
                 num_neurons_per_vec = 10, threshold = 0.3, \
                 N_out_vec = None, en_X_out = False, input_name = "Input", \
                 sim_mode = SimulationMode.DEFAULT, quick = True, rand_seed = None, **params):
        
        NetworkImpl.__init__(self)
        self.setName(name)

        if( mut_inhib_scale <= 0 ):
            en_mut_inhib = False

        if( out_vec_list is None ):
            out_vec_list = in_vec_list
        self.dimension = len(out_vec_list[0])

        if( isinstance(mut_inhib_scale, (int,float)) ):
            mut_inhib_scale = [mut_inhib_scale] * len(in_vec_list)
        if( isinstance(inhib_scale, (int,float)) ):
            inhib_scale = [inhib_scale] * len(in_vec_list)
        if( isinstance(threshold, (int,float)) ):
            threshold = [threshold] * len(in_vec_list)
        in_vec_list = [[in_vec_list[i][d] * in_scale for d in range(len(in_vec_list[i]))] \
                      for i in range(len(in_vec_list))]
        
        self.i_list = []
        self.in_vec_list = []

        if( str(sim_mode).lower() == 'ideal' ):
            node = CleanupMemoryNode(name, in_vec_list, out_vec_list, tau_in, en_inhib, tau_inhib, \
                                     threshold = sum(threshold) / len(threshold), en_wta = en_mut_inhib, \
                                     N_out_vec = N_out_vec)
            self.addNode(node)
            self.exposeTermination(node.getTermination("Input"), "Input")
            if( en_inhib ):
                self.exposeTermination(node.getTermination("Inhib"), "Inhib")
            self.exposeOrigin(node.getOrigin("Output"), "X")
            if( en_X_out ):
                self.exposeOrigin(node.getOrigin("X"), "x0")
        else:
            net = nef.Network(self, quick)

            enss = []
            
            num_items = 0
            for out_vec in out_vec_list:
                if( out_vec is None ):
                    continue
                else:
                    num_items += 1

            in_terms = []
            inhib_terms = []
            origins = []

            en_N_out = not (N_out_vec is None)

            out_relay = SimpleNEFEns("Output", self.dimension, pstc = tau_smooth)
            net.add(out_relay)

            if( en_X_out ):
                x_relay = SimpleNEFEns("X", num_items + en_N_out, pstc = tau_smooth)
                net.add(x_relay)

            for i,in_vec in enumerate(in_vec_list):
                if( out_vec_list[i] is None ):
                    continue

                self.in_vec_list.append(in_vec)
                self.i_list.append(i)
                
                pdf = IndicatorPDF(threshold[i] + 0.1, 1)
                eval_points = [[pdf.sample()[0]] for _ in range(1000)]
                intercepts = [threshold[i] + n * (1-threshold[i])/(num_neurons_per_vec) for n in range(num_neurons_per_vec)]
                if( sim_mode == SimulationMode.DIRECT ):
                    ens = SimpleNEFEns("Item" + str(i), 1, input_name = "")
                    net.add(ens)
                else:
                    ens = net.make("Item" + str(i), num_neurons_per_vec, 1, eval_points = eval_points, \
                                   encoders = [[1]] * num_neurons_per_vec, intercept = intercepts, \
                                   max_rate = (100,200), seed = rand_seed)
                
                if( input_name != "" and not input_name is None ):
                    ens.addDecodedTermination(input_name, [in_vec], tau_in, False)
                    in_terms.append(ens.getTermination(input_name))
                ens.addDecodedOrigin("Output", [FilteredStepFunction(shift = threshold[i], \
                                     step_val = out_vec_list[i][d]) for d in range(self.dimension)], \
                                     "AXON")
                enss.append(ens)
                
                out_relay.addDecodedTermination("Item" + str(i), None, tau_smooth, False)
                out_relay.addNeuronCount(ens.getNeuronCount())
                net.connect(ens.getOrigin("Output"), out_relay.getTermination("Item" + str(i)))
                
                if( en_X_out ):
                    ens.removeDecodedOrigin("X")
                    ens.addDecodedOrigin("X", [FilteredStepFunction(shift = threshold[i])], "AXON")
                    x_relay.addDecodedTermination("Item" + str(i), transpose(delta(num_items + en_N_out, i)), tau_smooth, False)
                    x_relay.addNeuronCount(ens.getNeuronCount())
                    net.connect(ens.getOrigin("X"), x_relay.getTermination("Item" + str(i)))

                if( en_inhib ):
                    ens.addTermination("Inhib", [[-inhib_scale[i]]] * num_neurons_per_vec, tau_inhib, False)
                    inhib_terms.append(ens.getTermination("Inhib"))
            
            if( not N_out_vec is None ):
                N_threshold = min(threshold)
                pdf = IndicatorPDF(-0.1, N_threshold - 0.1)
                eval_points = [[pdf.sample()[0]] for _ in range(1000)]
                intercepts  = [-(n * (N_threshold)/(num_neurons_per_vec)) for n in range(num_neurons_per_vec)]
                if( sim_mode == SimulationMode.DIRECT ):
                    ens = SimpleNEFEns("ItemN", 1, input_name = "")
                    net.add(ens)
                else:
                    ens = net.make("ItemN", num_neurons_per_vec, 1, eval_points = eval_points, \
                                   encoders = [[-1]] * num_neurons_per_vec, intercept = intercepts, \
                                   max_rate = (300,400), seed = rand_seed)

                for i in range(len(in_vec_list)):
                    ens.addDecodedTermination("Item" + str(i), [[1]], 0.005, False)
                    net.connect(enss[i].getOrigin("X"), ens.getTermination("Item" + str(i)))

                ens.addDecodedOrigin("Output", [FilteredStepFunction(shift = N_threshold, \
                                     step_val = N_out_vec[d], mirror = True) for d in range(self.dimension)], \
                                     "AXON")
                
                out_relay.addDecodedTermination("ItemN", None, tau_smooth, False)
                out_relay.addNeuronCount(ens.getNeuronCount())
                net.connect(ens.getOrigin("Output"), out_relay.getTermination("ItemN"))
                
                if( en_X_out ):
                    ens.removeDecodedOrigin("X")
                    ens.addDecodedOrigin("X", [FilteredStepFunction(shift = N_threshold, mirror = True)], "AXON")
                    x_relay.addDecodedTermination("ItemN", transpose(delta(num_items + en_N_out, num_items)), tau_smooth, False)
                    x_relay.addNeuronCount(ens.getNeuronCount())
                    net.connect(ens.getOrigin("X"), x_relay.getTermination("ItemN"))

                if( en_inhib ):
                    ens.addTermination("Inhib", [[-inhib_scale[i]]] * num_neurons_per_vec, tau_inhib, False)
                    inhib_terms.append(ens.getTermination("Inhib"))
             

            if( en_mut_inhib ):
                for n in range(num_items):
                    for i in range(num_items):
                        if( n != i):
                            enss[i].addTermination("Inhib" + str(n), [[-mut_inhib_scale[i]]] * num_neurons_per_vec, 0.005, False)
                            net.connect(enss[n].getOrigin("X"), enss[i].getTermination("Inhib" + str(n)))
            
            if( len(in_terms) > 0 ):
                in_term = EnsembleTermination(net.network, "Input", in_terms)
                net.network.exposeTermination(in_term, "Input")
            net.network.exposeOrigin(out_relay.getOrigin("X"), "X")

            if( en_X_out ):
                self.exposeOrigin(x_relay.getOrigin("X"), "x0")

            if( en_inhib ):
                inhib_term = EnsembleTermination(net.network, "Inhib", inhib_terms)
                net.network.exposeTermination(inhib_term, "Inhib")
            
            # Reset random seed
            if( not seed is None ):
                seed()
            self.releaseMemory()

        if( str(sim_mode).lower() == 'ideal' ):
            sim_mode = SimulationMode.DIRECT
        NetworkImpl.setMode(self, sim_mode)
        if( sim_mode == SimulationMode.DIRECT ):
            self.fixMode()

    def addDecodedTermination(self, name, matrix, tauPsc, isModulatory = False):
        try:
            node = self.getNode(self.getName())
            print("CLEANUP-MEM: AddDecodedTermination - NOT SUPPORTED YET")
            return
        except:
            in_terms = []
#            if( not matrix is None ):
#                print("CLEANUP-MEM: AddDecodedTermination - Ignoring input matrix, using cleanup vecs")
            for i in self.i_list:
                node = self.getNode("Item" + str(i))
                node.addDecodedTermination(name, [self.in_vec_list[i]], tauPsc, isModulatory)
                in_terms.append(node.getTermination(name))
            in_term = EnsembleTermination(self, name, in_terms)
            self.exposeTermination(in_term, name)
            
    def releaseMemory(self):
        for node in self.getNodes():
            node.releaseMemory()

    def setMode(self, sim_mode):
        if( sim_mode == SimulationMode.DIRECT ):
            sim_mode = SimulationMode.RATE
        NetworkImpl.setMode(self, sim_mode)