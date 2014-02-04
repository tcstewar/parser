D=1000
noise=0
import sys
sys.path.append('/home/tcstewar/github/ccmsuite')
import ccm

import lcparser_v2 as lcparser

log = ccm.log()

rules = [
    ('S', ['SBAR', 'VP']),
    ('SBAR', ['IN', 'S']),    
    ('VP', ['V', 'NP']),
    ('S', ['VP']),
    ('S', ['NP', 'VP']),
    ('NP', ['DET', 'N']),
    ('NP', ['N']),
    ]
    
words = {
    'N': 'five three'.split(),
    'DET': 'the a'.split(),
    'V': 'see write'.split(),
    'IN': 'iff'.split(),
    }

sentence = 'iff see three write five'

correct = [
    'iff*L_IN*L_SBAR*L_S',
    'see*L_V*L_VP*L_S*R_SBAR*L_S',
    'three*L_N*L_NP*R_VP*L_S*R_SBAR*L_S',
    'write*L_V*L_VP*R_S',
    'five*L_N*L_NP*R_VP*R_S',
    ]
    
    
    
    
def test(sentence, noise, retries=0):
    parser = lcparser.LeftCornerParser(D, rules, words, noise=noise)
    tree = parser.parse(sentence.split())
    
    score = [tree.compare(parser.vocab.parse(c)) for c in correct]
    prob = [parser.vocab.prob_cleanup(s, 10000) for s in score]
 

    if max(prob)<=0.000001:
        print 'parsing failure; retrying'
        return test(sentence, noise, retries=retries+1)

    print ' '.join(['%1.5f'%p for p in prob])
    log.prob = sum(prob)/len(prob)
    log.retries = retries

    
test(sentence, noise=noise)      

  
   
