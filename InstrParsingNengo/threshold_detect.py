import nef

from ca.nengo.model import Units
from ca.nengo.model import SimulationMode
from ca.nengo.model.impl import NetworkImpl
from ca.nengo.model.impl import EnsembleTermination
from ca.nengo.model.impl import EnsembleOrigin
from ca.nengo.math.impl import IndicatorPDF
from ca.nengo.math.impl import PostfixFunction
from ca.nengo.math import PDFTools

from util_nodes import *
from util_funcs import *
from math import *
from copy import deepcopy
from random import *
from java.lang.System.err import println


class Detector(NetworkImpl):
    def __init__(self, name = "Detector", detect_vec = None, inhib_vec = None, out_vec = [1], tau_in = 0.005, \
                 en_inhib = False, en_inhibN = None, en_inhibM = None, tau_inhib = 0.005, in_scale = 1.0, inhib_scale = 2.0,\
                 en_out = True, en_N_out = False, en_M_out = False, en_X_out = False, num_neurons = 20, detect_threshold = 0.4, \
                 sim_mode = SimulationMode.DEFAULT, quick = True, rand_seed = None, net = None, input_name = "Input"):
   
        self.dimension = len(out_vec)

        NetworkImpl.__init__(self)
        ens_name = name
        if( not isinstance(net, nef.Network) ):
            if( not net is None ):
                net = nef.Network(net, quick)
            else:
                ens_name = "detect"
                net = nef.Network(self, quick)
        self.setName(name)

        self.net = net
        self.en_out = en_out
        self.en_N_out = en_N_out
        self.en_M_out = en_M_out
        self.en_X_out = en_X_out
        self.ens_name = ens_name

        if( detect_vec is None ):
            detect_vec = [1]

        vec_dim = len(detect_vec)
        detect_vec_scale = [detect_vec[n] * in_scale for n in range(vec_dim)]
        if( en_inhib ):
            if( inhib_vec is None ):
                inhib_vec = [1]
            inhib_dim = len(inhib_vec)
        if( en_inhibN is None ):
            en_inhibN = en_inhib
        if( en_inhibM is None ):
            en_inhibM = en_inhib
        if( en_inhib or en_inhibN or en_inhibM ):
            inhib_vec_scale = [inhib_vec[n] * -inhib_scale for n in range(inhib_dim)]

        num_inhib_terms = max(en_inhib, en_inhibN, en_inhibM)
        inhib_terms = [[]] * num_inhib_terms

        max_rate  = (100,200)
        max_rateN = (300,400)

        intercepts  = [detect_threshold + n * (1-detect_threshold)/(num_neurons) for n in range(num_neurons)]
        interceptsN = [-(n * (detect_threshold)/(num_neurons)) for n in range(num_neurons)]
        params  = dict(intercept = intercepts , max_rate = max_rate , quick = quick, seed = rand_seed)
        paramsN = dict(intercept = interceptsN, max_rate = max_rateN, quick = quick, seed = rand_seed)
        paramsM = dict(intercept = intercepts , max_rate = max_rate , quick = quick, seed = rand_seed)

        out_func  = [FilteredStepFunction(shift = detect_threshold, mirror = False, step_val = out_vec[d]) for d in range(self.dimension)]
        out_funcN = [FilteredStepFunction(shift = detect_threshold, mirror = True, step_val = out_vec[d]) for d in range(self.dimension)]
        out_funcM = [MirroredFilteredStepFunction(shift = detect_threshold, step_val = out_vec[d]) for d in range(self.dimension)]
        
        params["encoders"]  = [[1]] * num_neurons
        paramsN["encoders"] = [[-1]] * num_neurons

        pdf  = IndicatorPDF(detect_threshold + 0.1, 1.1)
        pdfN = IndicatorPDF(-0.1, detect_threshold - 0.1)
        pdfM = IndicatorPDF(-1.1, -(detect_threshold + 0.1))
        params["eval_points"]  = [[pdf.sample()[0]] for _ in range(1000)]
        paramsN["eval_points"] = [[pdfN.sample()[0]] for _ in range(1000)]
        params["eval_points"]  = [[pdf.sample()[0]] for _ in range(500)] + [[pdfM.sample()[0]] for _ in range(500)]
        

        if( en_out ):
            if( sim_mode == SimulationMode.DIRECT or str(sim_mode).lower() == 'ideal' ):
                detect = SimpleNEFEns(ens_name, 1, input_name = "")
                net.add(detect)
            else:
                detect = net.make(ens_name, num_neurons, 1, **params)
            if( not input_name is None ):
                detect.addDecodedTermination(input_name, [detect_vec_scale], tau_in, False)
            if( en_inhib ):
                for n in range(num_inhib_terms):
                    if( n == 0 ):
                        inhib_name = "Inhib"
                    else:
                        inhib_name = "Inhib%d" % (n+1)
                    detect.addTermination(inhib_name, [inhib_vec_scale] * num_neurons, tau_inhib, False)
                    inhib_terms[n].append(detect.getTermination(inhib_name))                
            
            detect.removeDecodedOrigin("X")
            detect.addDecodedOrigin("X", out_func, "AXON")

            if( en_X_out ):
                detect.addDecodedOrigin("x0", [PostfixFunction("x0", 1)], "AXON")
                self.exposeOrigin(detect.getOrigin("x0"), "x0")

        if( en_N_out ):
            if( sim_mode == SimulationMode.DIRECT or str(sim_mode).lower() == 'ideal' ):
                detectN = SimpleNEFEns(ens_name + "N", 1, input_name = "")
                net.add(detectN)
            else:
                detectN = net.make(ens_name + "N", num_neurons, 1, **paramsN)
            if( not input_name is None ):
                detectN.addDecodedTermination(input_name, [detect_vec_scale], tau_in, False)
            if( en_inhibN ):
                for n in range(num_inhib_terms):
                    if( n == 0 ):
                        inhib_name = "Inhib"
                    else:
                        inhib_name = "Inhib%d" % (n+1)
                    detectN.addTermination(inhib_name, [inhib_vec_scale] * num_neurons, tau_inhib, False)
                    inhib_terms[n].append(detectN.getTermination(inhib_name))                
        
            detectN.removeDecodedOrigin("X")
            detectN.addDecodedOrigin("X", out_funcN, "AXON")

            if( en_X_out ):
                detectN.addDecodedOrigin("x0", [PostfixFunction("x0", 1)], "AXON")
                self.exposeOrigin(detectN.getOrigin("x0"), "x0N")

        if( en_M_out ):
            nn_scale = 2
            if( sim_mode == SimulationMode.DIRECT or str(sim_mode).lower() == 'ideal' ):
                detectM = SimpleNEFEns(ens_name + "M", 1, input_name = "")
                net.add(detectM)
            else:
                detectM = net.make(ens_name + "M", num_neurons * nn_scale, 1, **paramsM)
            if( not input_name is None ):
                detectM.addDecodedTermination(input_name, [detect_vec_scale], tau_in, False)
            if( en_inhibM ):
                for n in range(num_inhib_terms):
                    if( n == 0 ):
                        inhib_name = "Inhib"
                    else:
                        inhib_name = "Inhib%d" % (n+1)
                    detectM.addTermination(inhib_name, [inhib_vec_scale] * num_neurons, tau_inhib, False)
                    inhib_terms[n].append(detectM.getTermination(inhib_name))                
        
            detectM.removeDecodedOrigin("X")
            detectM.addDecodedOrigin("X", out_funcM, "AXON")

            if( en_X_out ):
                detectM.addDecodedOrigin("x0", [PostfixFunction("x0", 1)], "AXON")
                self.exposeOrigin(detectM.getOrigin("x0"), "x0M")
              

        input_terms = []       
        if( en_out ):
            if( not input_name is None ):
                input_terms.append(detect.getTermination(input_name))
            self.exposeOrigin(detect.getOrigin("X"), name)
        if( en_N_out ):
            if( not input_name is None ):
                input_terms.append(detectN.getTermination(input_name))
            self.exposeOrigin(detectN.getOrigin("X"), str(name + "N"))
        if( en_M_out ):
            if( not input_name is None ):
                input_terms.append(detectM.getTermination(input_name))
            self.exposeOrigin(detectM.getOrigin("X"), str(name + "M"))
        
        if( len(input_terms) > 0 ):
            input_term = EnsembleTermination(net.network, input_name, input_terms)
            self.exposeTermination(input_term, input_name)
        for n in range(len(inhib_terms)):
            if( len(inhib_terms[n]) > 0 ):
                inhib_term = EnsembleTermination(net.network, "Inhib%d" % n, inhib_terms[n])
                if( n == 0 ):
                    self.exposeTermination(inhib_term, "Inhib")
                else:
                    self.exposeTermination(inhib_term, "Inhib%d" % (n+1))

        if( str(sim_mode).lower() == 'ideal' ):
            sim_mode = SimulationMode.DIRECT
        NetworkImpl.setMode(self, sim_mode)
        if( sim_mode == SimulationMode.DIRECT ):
            self.fixMode()

        # Reset random seed
        if( not seed is None ):
            seed()
        self.releaseMemory()

            
    def setMode(self, sim_mode):
        if( sim_mode == SimulationMode.DIRECT ):
            sim_mode = SimulationMode.RATE
        NetworkImpl.setMode(self, sim_mode)


    def releaseMemory(self):
        for node in self.getNodes():
            node.releaseMemory()


    def addDecodedTermination(self, name, matrix, tauPsc, isModulatory = False):
        in_terms = []
        if( self.en_out ):
            node = self.getNode(self.ens_name)
            node.addDecodedTermination(name, matrix, tauPsc, isModulatory)
            in_terms.append(node.getTermination(name))
        if( self.en_N_out ):
            node = self.getNode(self.ens_name + "N")
            node.addDecodedTermination(name, matrix, tauPsc, isModulatory)
            in_terms.append(node.getTermination(name))
        if( self.en_M_out ):
            node = self.getNode(self.ens_name + "M")
            node.addDecodedTermination(name, matrix, tauPsc, isModulatory)
            in_terms.append(node.getTermination(name))
        in_term = EnsembleTermination(self.net.network, name, in_terms)
        self.exposeTermination(in_term, name)




class DetectorArray(NetworkImpl):
    def __init__(self, name = "Detector", num_dim = 1, in_matrix = None, inhib_vec = None, tau_in = 0.005, \
                 en_inhib = False, en_N_out = False, tau_inhib = 0.005, in_scale = 1.0, inhib_scale = 2.0,\
                 out_vec = [1], out_N_vec = None, num_neurons = 50, detect_threshold = 0.1, \
                 sim_mode = SimulationMode.DEFAULT, quick = True, rand_seed = None, net = None, input_name = "Input"):
   
        self.dimension = len(out_vec)
        NetworkImpl.__init__(self)
        ens_name = name
        if( not isinstance(net, nef.Network) ):
            if( not net is None ):
                net = nef.Network(net, quick)
            else:
                ens_name = "detect"
                net = nef.Network(self, quick)
        self.setName(name)
        self.net = net

        self.myNodes = []
        input_terms = []
        inhib_terms = []
        
        num_neurons = int(ceil(num_neurons / 2.0) * 2.0)

        if( en_inhib ):
            if( inhib_vec is None ):
                inhib_vec = [1]
            inhib_dim = len(inhib_vec)
        
        if( in_matrix is None ):
            in_matrix = eye(num_dim)

        max_rate    = (100,200)
        dead_zone   = 0.05
        intercepts  = [dead_zone + n * 2.0 * (1 - dead_zone)/(num_neurons) for n in range(num_neurons/2.0)] * 2
        params      = dict(intercept = intercepts, max_rate = max_rate , quick = quick, seed = rand_seed, \
                           storage_code = "")
        
        Detector("Out", out_vec = out_vec, detect_threshold = 0.1, en_out = True, tau_in = tau_in, \
                 en_inhib = en_inhib, en_X_out = True, sim_mode = sim_mode, quick = quick, rand_seed = rand_seed, \
                 net = net, input_name = None)
        out_relay = self.getNode("Out")

        en_N_vec = (not out_N_vec is None)
        if( en_N_vec ):
            Detector("OutN", out_vec = out_N_vec, detect_threshold = 0.1, en_out = True, tau_in = tau_in, \
                     en_inhib = True + en_inhib, sim_mode = sim_mode, quick = quick, rand_seed = rand_seed, \
                     net = net)
            out_N_relay = self.getNode("OutN")
            net.make_input("Bias", [1])
            net.connect("Bias", out_N_relay.getTermination("Input"))

        for n in range(num_dim):
            params["storage_code"] = "quick_detect_array%d_%d_%d" % (n, num_dim, num_neurons)
            params["storage_code"] += "_%1.3f_%1.3f" % (max_rate)
            #params["storage_code"] += "_%1.3f_%1.3f" % (intercepts)
            if( sim_mode == SimulationMode.DIRECT or str(sim_mode).lower() == 'ideal' ):
                ens = SimpleNEFEns(ens_name + "%d" % n, 1, input_name = "")
                net.add(detect)
            else:
                ens = net.make(ens_name + "%d" % n, num_neurons, 1, **params)

            if( not input_name is None ):
                input_vec = [in_scale * in_matrix[n][d] for d in range(len(in_matrix[n]))]
                ens.addDecodedTermination(input_name, [input_vec], tau_in, False)
            
            ens.addDecodedOrigin("abs", [VFunction(dead_zone = 0.05)], "AXON")
            self.myNodes.append(ens)
            out_relay.addDecodedTermination(ens_name + "%d" % n, [[1.2 * 1.0/num_dim]], tau_in, False)
            self.net.connect(ens.getOrigin("abs"), out_relay.getTermination(ens_name + "%d" % n))
               
            if( not input_name is None ):
                input_terms.append(ens.getTermination(input_name))

        if( len(input_terms) > 0 ):
            input_term = EnsembleTermination(net.network, input_name, input_terms)
            self.exposeTermination(input_term, input_name)
        for n in range(en_inhib):
            if( n == 0 ):
                inhib_str = "Inhib"
                inhib_N_str = "Inhib2"
            else:
                inhib_str = "Inhib%d" % (n+1)
                inhib_N_str = "Inhib%d" % (n+2)
            inhib_terms = [out_relay.getTermination(inhib_str), out_N_relay.getTermination(inhib_N_str)]
            inhib_term = EnsembleTermination(net.network, inhib_str, inhib_terms)
            if( n == 0 ):
                self.exposeTermination(inhib_term, inhib_str)
            else:
                self.exposeTermination(inhib_term, inhib_str)

        if( en_N_vec ):
            out_relay2 = net.make("Sum", 1, len(out_vec), mode = 'direct')
            out_relay2.fixMode()
            
            self.net.connect(out_relay.getOrigin("x0"), out_N_relay.getTermination("Inhib"))
            self.net.connect(out_relay.getOrigin("X"), out_relay2, pstc = 0.0001)
            self.net.connect(out_N_relay.getOrigin("X"), out_relay2, pstc = 0.0001)
            self.exposeOrigin(out_relay2.getOrigin("X"), "X")
            if( en_N_out ):
                self.exposeOrigin(out_N_relay.getOrigin("X"), "XN")
        else:
            self.exposeOrigin(out_relay.getOrigin("X"), "X")       

        if( str(sim_mode).lower() == 'ideal' ):
            sim_mode = SimulationMode.DIRECT
        NetworkImpl.setMode(self, sim_mode)
        if( sim_mode == SimulationMode.DIRECT ):
            self.fixMode()

        # Reset random seed
        if( not seed is None ):
            seed()
        self.releaseMemory()

            
    def setMode(self, sim_mode):
        if( sim_mode == SimulationMode.DIRECT ):
            sim_mode = SimulationMode.RATE
        NetworkImpl.setMode(self, sim_mode)


    def releaseMemory(self):
        for node in self.getNodes():
            if( hasattr(node, "releaseMemory") ):
                node.releaseMemory()


    def addDecodedTermination(self, name, matrix, tauPsc, isModulatory = False):
        in_terms = []
        for n,node in enumerate(self.myNodes):
            node.addDecodedTermination(name, [matrix[n]], tauPsc, isModulatory)
            in_terms.append(node.getTermination(name))
        in_term = EnsembleTermination(self.net.network, name, in_terms)
        self.exposeTermination(in_term, name)
