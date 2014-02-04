from ca.nengo.ui import NengoGraphics

def full_reset():
   nengo = NengoGraphics.getInstance();
   if( not nengo is None ):
      modelsToRemove = nengo.getWorld().getGround().getChildren();
      copy = [x for x in modelsToRemove]
      for model in copy:
          nengo.removeNodeModel(model.getModel());
      nengo.getScriptConsole().reset(True)

full_reset()

import sys
sys.path.append("F:\\xchoo\\Documents\\Dropbox\\Thesis - PhD\\Code\\Python\\DelayTest\\")
sys.path.append("D:\\fchoo\\Documents\\My Dropbox\\Thesis - PhD\\Code\\Python\\DelayTest\\")
sys.path.append("D:\\Users\\xchoo\\Dropbox\\Thesis - PhD\\Code\\Python\\DelayTest\\")

import datetime
now = "2013-01-03 12:17:51.828000"
now = str(datetime.datetime.now()).replace(":","-").replace(".","-")
#now = "2013-01-03 18:53:41.220000"
#now = "2013-01-03 23:29:03.197000"
print now

import random
random.seed(now)

from random import shuffle
import numeric as np

import nef
from nef.convolution import make_convolution
import hrr
from spa import *
from util_funcs import *
from cleanup_mem import *
from threshold_detect import Detector
from gated_integrator import GatedInt
from selector import Selector
from threshold_detect import Detector, DetectorArray
from mem_block import MemBlock
from ca.nengo.math.impl import PostfixFunction

pstc_base = 0.01
pstc_multiplier = 2
max_rate = (100,200)

nn = 30
nd = 300
ni = 10
ns = 10

nn_cconv = 150

test_option = 8
if( len(sys.argv) > 1 ):
    test_option = int(sys.argv[1])

test_name = "Test"
if( len(sys.argv) > 2 ):
    test_name = sys.argv[2]

screenshot_mode = False

# RULE FORMAT:
#
# POS[i] x (ANT(SENSOR x sense + SENSOR_DATA x data) + CON(ACTION x action + ACTION_DATA x data)) +
#
# Decoding style:
# - Provide SENSOR and SENSORY_DATA to RULE -> get POS[i]
# - Cleanup POS[i]
# - Provide POS[i] to RULE -> get ANT and CON
# - Figure out what do to from ANT and CON
#
# For the sentence structured like this: "if SENSOR SENSORY_DATA ACTION ACTION_DATA"
#                                   e.g. "if see square press button1"
# With these parse rules:
#    S -> SBAR, VP
#    SBAR -> IN, S
#    VP -> V, NP
#    S -> VP
#    NP -> DET, N
#    NP -> N
#
# And these words:
#    N: button1, button2, square, circle, one, two
#    DET: the
#    V: press see hear write
#    IN: if
#
# That generates this parse tree:
# S (1.031   99%)
#   SBAR (1.245   99%)
#     IN (0.572    0%)
#       iff (0.927   98%)
#     S (0.815   81%)
#       VP (0.581    0%)
#         V (0.946   99%)
#           see (0.757   48%)
#         NP (0.852   91%)
#           N (0.775   61%)
#             square (1.157   99%)
#   VP (1.115   99%)
#     V (0.996   99%)
#       press (1.339   99%)
#     NP (0.941   98%)
#       N (1.083   99%)
#         button (1.240   99%)
# 
# In SPA form, that is:
# SENTENCE = L_S(L_SBAR(L_IN(iff)) + R_SBAR(L_S(L_VP(L_V(see)) + R_VP(L_NP(L_N(square)))))) + R_S(L_VP(L_V(press)) + R_VP(L_NP(L_N(button))))
#
# The sentence parsing -> instruction processing mapping vectors are as follows:
# ANT = L_S
# SENSOR = R_SBAR x L_S x L_VP x L_V
# SENSOR_DATA = R_SBAR x R_VP x L_NP x L_N
# ACTION = R_S x L_VP x L_V
# ACTION_DATA = R_S x R_VP x L_NP x L_N

# perm_ant = range(nd)
# perm_con = range(nd)
# shuffle(perm_ant)
# shuffle(perm_con)

# def permute_ant(matrix):
#     return [matrix[i] for i in perm_ant]

# def permute_con(matrix):
#     return [matrix[i] for i in perm_con]

vocab = hrr.Vocabulary(nd, max_similarity = 0.1, include_pairs = False, \
					   unitary = ["I0", "ADD1", "P0", "L_S", "R_S", "L_SBAR", "R_SBAR", "L_VP", "R_VP", \
					              "L_IN", "R_IN", "L_V", "R_V", "L_NP", "R_NP", "L_DET", "R_DET", "L_N", "R_N"])

pos_list = []
vocab.parse("P0")
pos_list.append(vocab.hrr["P0"].v)
for i in range(ns-1):
    vocab.add("P%i" % (i+1), hrr.HRR(data = cconv(vocab.hrr["P0"].v, vocab.hrr["P%i"%i].v)))
    pos_list.append(vocab.hrr["P%i"%(i+1)].v)

for i in ["L_S", "R_S", "L_SBAR", "R_SBAR", "L_VP", "R_VP", "L_IN", "R_IN", "L_V", "R_V", "L_NP", "R_NP", "L_DET", "R_DET", "L_N", "R_N"]:
	vocab.parse(i)

action_list = []
for i in ["press", "write"]:
	vocab.parse(i)
	action_list.append(vocab.hrr[i].v)

action_data_list = []
for i in ["button1", "button2", "num1", "num2"]:
	vocab.parse(i)
	action_data_list.append(vocab.hrr[i].v)

sensor_list = []
for i in ["see", "hear"]:
	vocab.parse(i)
	sensor_list.append(vocab.hrr[i].v)

sensor_data_list = []
for i in ["square", "circle", "one", "two"]:
	vocab.parse(i)
	sensor_data_list.append(vocab.hrr[i].v)

vocab.parse("iff")
vocab.parse("WAIT")


####
VEC_ANT = vocab.hrr["L_S"].v
VEC_SENSOR = cconv(cconv(cconv(vocab.hrr["R_SBAR"].v, vocab.hrr["L_S"].v), vocab.hrr["L_VP"].v), vocab.hrr["L_V"].v)
VEC_SENSOR_DATA = cconv(cconv(cconv(cconv(vocab.hrr["R_SBAR"].v, vocab.hrr["L_S"].v), vocab.hrr["R_VP"].v), vocab.hrr["L_NP"].v), vocab.hrr["L_N"].v)
VEC_CONS = vocab.hrr["R_S"].v
VEC_ACTION = cconv(vocab.hrr["L_VP"].v, vocab.hrr["L_V"].v)
VEC_ACTION_DATA = cconv(cconv(vocab.hrr["R_VP"].v, vocab.hrr["L_NP"].v), vocab.hrr["L_N"].v)
VEC_IFF_VEC = cconv(cconv(vocab.hrr["L_SBAR"].v, vocab.hrr["L_IN"].v), vocab.hrr["iff"].v)
vocab.add("ANT", hrr.HRR(data = VEC_ANT))
vocab.add("SENSOR", hrr.HRR(data = VEC_SENSOR))
vocab.add("S_DATA", hrr.HRR(data = VEC_SENSOR_DATA))
vocab.add("CONS", hrr.HRR(data = VEC_CONS))
vocab.add("ACTION", hrr.HRR(data = VEC_ACTION))
vocab.add("A_DATA", hrr.HRR(data = VEC_ACTION_DATA))
vocab.add("IFFV", hrr.HRR(data = VEC_IFF_VEC))
vocab.add("ANTxSENSOR", hrr.HRR(data = cconv(VEC_ANT, VEC_SENSOR)))
vocab.add("ANTxS_DATA", hrr.HRR(data = cconv(VEC_ANT, VEC_SENSOR_DATA)))
vocab.add("CONSxACTION", hrr.HRR(data = cconv(VEC_CONS, VEC_ACTION)))
vocab.add("CONSxA_DATA", hrr.HRR(data = cconv(VEC_CONS, VEC_ACTION_DATA)))
vocab.add("~(CONSxACTION)", hrr.HRR(data = invol(vocab.hrr["CONSxACTION"].v)))
vocab.add("~(CONSxA_DATA)", hrr.HRR(data = invol(vocab.hrr["CONSxA_DATA"].v)))

vocab.add("write*num1", hrr.HRR(data = cconv(vocab.hrr["write"].v, vocab.hrr["num1"].v)))
vocab.add("write*num2", hrr.HRR(data = cconv(vocab.hrr["write"].v, vocab.hrr["num2"].v)))
vocab.add("press*button1", hrr.HRR(data = cconv(vocab.hrr["press"].v, vocab.hrr["button1"].v)))
vocab.add("press*button2", hrr.HRR(data = cconv(vocab.hrr["press"].v, vocab.hrr["button2"].v)))

def gen_instr_SP(vocab, sensor, s_data, action, a_data):
    return np.array(cconv(vocab.hrr["ANT"].v, np.array(VEC_IFF_VEC) + \
                                              np.array(cconv(vocab.hrr["SENSOR"].v, vocab.hrr[sensor].v)) + \
                                              np.array(cconv(vocab.hrr["S_DATA"].v, vocab.hrr[s_data].v)))) + \
           np.array(cconv(vocab.hrr["CONS"].v, np.array(cconv(vocab.hrr["ACTION"].v, vocab.hrr[action].v)) + \
                                               np.array(cconv(vocab.hrr["A_DATA"].v, vocab.hrr[a_data].v))))

vis_stim = {}
vis_stim[0.0] = zeros(1,nd)
vis_stim[0.1] = vocab.hrr["square"].v
vis_stim[0.35] = zeros(1,nd)
vis_stim[0.9] = vocab.hrr["circle"].v
vis_stim[1.15] = zeros(1,nd)
vis_stim[1.25] = vocab.hrr["square"].v
vis_stim[1.50] = zeros(1,nd)

aud_stim = {}
aud_stim[0.0] = zeros(1,nd)
aud_stim[0.5] = vocab.hrr["one"].v
aud_stim[0.75] = zeros(1,nd)

run_time = 1.75
rule_info = np.array(cconv(vocab.hrr["P0"].v, gen_instr_SP(vocab, "see", "square", "press", "button1"))) + \
            np.array(cconv(vocab.hrr["P1"].v, gen_instr_SP(vocab, "see", "circle", "press", "button2"))) + \
            np.array(cconv(vocab.hrr["P2"].v, gen_instr_SP(vocab, "hear", "one", "write", "num1"))) + \
            np.array(cconv(vocab.hrr["P3"].v, gen_instr_SP(vocab, "hear", "two", "write", "num2")))

print("Done!")

######################################################################################################
class RuleProc(module.Module):
    def create(self):
        stored_rule = self.net.make_input("StoredRule", rule_info)

        sensor_in = self.net.make("SENSOR IN", 1, nd, mode = 'direct')
        sensor_data_in = self.net.make("S_DATA IN", 1, nd, mode = 'direct')
        self.add_sink(sensor_in, "sensor_in") ##>]##
        self.add_sink(sensor_data_in, "sensor_data_in") ##>]##

        ant_add = self.net.make("ANT ADD", 1, nd, mode = 'direct')
        ant_add.addDecodedTermination("SENSOR", np.array(vocab.hrr["ANTxSENSOR"].get_transform_matrix()) * 0.4, 0.001, False)
        ant_add.addDecodedTermination("S_DATA", np.array(vocab.hrr["ANTxS_DATA"].get_transform_matrix()) * 0.6, 0.001, False)
        self.net.connect("SENSOR IN", ant_add.getTermination("SENSOR"))
        self.net.connect("S_DATA IN", ant_add.getTermination("S_DATA"))

        cconv_pos_out = self.net.make("CConv Pos Out", 1, nd, mode = 'direct')
        cconv_pos_ens = make_convolution(self.net, "CCONV -> POS", None, None, cconv_pos_out, nn_cconv, radius = 6, \
                                         invert_second = True, quick = True)
        self.net.connect("StoredRule", cconv_pos_ens.getTermination("A"))
        self.net.connect("ANT ADD", cconv_pos_ens.getTermination("B"))

        cleanup_pos = CleanupMem("CleanupPos", pos_list, en_mut_inhib = True, tau_in = pstc_base, in_scale = 1.0, threshold = 0.4)
        self.net.add(cleanup_pos)
        self.net.connect(cconv_pos_out.getOrigin("X"), cleanup_pos.getTermination("Input"))

        cconv_rule_out = self.net.make("CConv Rule Out", 1, nd, mode = 'direct')
        cconv_rule_ens = make_convolution(self.net, "CCONV -> RULE", None, None, cconv_rule_out, nn_cconv, radius = 6, \
                                          invert_second = True, quick = True)
        self.net.connect("StoredRule", cconv_rule_ens.getTermination("A"))
        self.net.connect(cleanup_pos.getOrigin("X"), cconv_rule_ens.getTermination("B"))

        action = self.net.make("ACTION", 1, nd, mode = 'direct')
        action.addDecodedTermination("Input", vocab.hrr["~(CONSxACTION)"].get_transform_matrix(), 0.001, False)
        action_cu = CleanupMem("CleanupAction", action_list, en_mut_inhib = True, tau_in = pstc_base, \
                                     threshold = 0.15, in_scale = 1.2, tau_smooth = pstc_base)
        self.net.add(action_cu)
        self.net.connect(cconv_rule_out, action.getTermination("Input"))
        self.net.connect(action, action_cu.getTermination("Input"))
        self.add_source(action_cu.getOrigin("X"), "act_out") ##]>##

        action_data = self.net.make("ACTION DATA", 1, nd, mode = 'direct')
        action_data.addDecodedTermination("Input", vocab.hrr["~(CONSxA_DATA)"].get_transform_matrix(), 0.001, False)
        action_data_cu = CleanupMem("CleanupActionData", action_data_list, en_mut_inhib = True, tau_in = pstc_base, \
                                     threshold = 0.15, in_scale = 1.2, tau_smooth = pstc_base)
        self.net.add(action_data_cu)
        self.net.connect(cconv_rule_out, action_data.getTermination("Input"))
        self.net.connect(action_data, action_data_cu.getTermination("Input"))
        self.add_source(action_data_cu.getOrigin("X"), "act_data_out") ##]>##        


    def connect(self):
        pass


class Vision(module.Module):
    def create(self):
        vision_input = self.net.make_input("VIS Input", vis_stim)
        #vision = self.net.make("VISION", 1, nd, mode = 'direct')
        vision = self.net.make("VISION", 20 * nd, nd)
        self.net.connect(vision_input, vision)

        self.add_source(vision.getOrigin("X"), "out") ##]>##

class Auditory(module.Module):
    def create(self):
        aud_input = self.net.make_input("AUD Input", aud_stim)
        #auditory = self.net.make("AUDITORY", 1, nd, mode = 'direct')
        auditory = self.net.make("AUDITORY", 20 * nd, nd)
        self.net.connect(aud_input, auditory)

        self.add_source(auditory.getOrigin("X"), "out") ##]>##

class Motor(module.Module):
    def create(self):
        action_input = self.net.make("ACTION IN", 1, nd, mode = 'direct')
        a_data_input = self.net.make("A_DATA IN", 1, nd, mode = 'direct')
        self.add_sink(action_input, "action_in") ##>]##
        self.add_sink(a_data_input, "action_data_in") ##>]##

        cconv_mtr_out = self.net.make("Motor Out", 20 * nd, nd)
        cconv_mtr_ens = make_convolution(self.net, "CCONV", None, None, cconv_mtr_out, nn_cconv, radius = 6, quick = True)
        self.net.connect("ACTION IN", cconv_mtr_ens.getTermination("A"))
        self.net.connect("A_DATA IN", cconv_mtr_ens.getTermination("B"))


class Rules:
    def VisualInput(vis_out = "square+circle"):
        set(instr_sensor_in = "see")
        set(instr_sensor_data_in = vis_out)
        set(motor_action_in = instr_act_out)
        set(motor_action_data_in = instr_act_data_out)

    def AudInput(aud_out = "one+two"):
        set(instr_sensor_in = "hear")
        set(instr_sensor_data_in = aud_out)
        set(motor_action_in = instr_act_out)
        set(motor_action_data_in = instr_act_data_out)


class FullTest(SPA):
    dimensions = nd
    radius = 1

    vis   = Vision()
    aud   = Auditory()
    #task  = Task()
    instr = RuleProc(N_per_D = 30)
    # wm    = Memory(N_per_D = 30)
    # state = Buffer(feedback = 1, pstc_feedback = 0.01, radius = radius, max_rate = (100,200))
    #motor = Buffer(feedback = 0, radius = radius, max_rate = (100,200))
    motor = Motor(N_per_D = 30)
    BG    = BasalGanglia(Rules(), radius = 1.5, max_rate = (100,200))
    thal  = Thalamus(BG, mutual_inhibit=0.5, max_rate = (100,200), radius = radius, route_scale = 2)


network = FullTest(vocabs = [vocab])
net = network.net
net.releaseMemory()
hrr.Vocabulary.defaults[nd] = vocab

if( screenshot_mode ):
    view_window = network.net.view(play = run_time)
    view_window.save_screenshots(0.01)

else:
    logger = nef.Log(net, test_name + ' ' + now, dir = "E:\\Data\\CogSci2014", tau = 0.02)
    logger.add_vocab("vis.vis_out", vocab)
    logger.add_spikes("vis.VISION")
    logger.add_vocab("aud.aud_out", vocab)
    logger.add_spikes("aud.AUDITORY")
    logger.add_vocab("instr.SENSOR IN.X", vocab)
    logger.add_vocab("instr.S_DATA IN.X", vocab)
    logger.add_vocab("instr.CConv Pos Out.X", vocab)
    logger.add_vocab("instr.CleanupPos.X", vocab)
    logger.add_vocab("instr.CleanupAction.X", vocab)
    logger.add_vocab("instr.CleanupActionData.X", vocab)
    #logger.add_vocab("motor.buffer.X", vocab)
    #logger.add_spikes("motor.buffer")
    logger.add_vocab("motor.Motor Out.X", vocab)
    logger.add_spikes("motor.Motor Out")

    net.network.simulator.run(0,run_time,0.001,False)
    net.network.removeStepListener(logger)

try:
    exit()
except:
    pass
