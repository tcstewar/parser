import numpy as np
np.random.seed(4)

import lcparser_v2 as lcparser

rules = [
    ('S', ['SBAR', 'VP']),
    ('SBAR', ['IN', 'S']),    
    ('VP', ['V', 'NP']),
    ('S', ['VP']),
    ('NP', ['DET', 'N']),
    ('NP', ['N']),
    ]
    
words = {
    'N': 'button square'.split(),
    'DET': 'the'.split(),
    'V': 'press see'.split(),
    'IN': 'iff'.split(),
    }

parser = lcparser.LeftCornerParser(1024, rules, words)

#tree = parser.parse('press the button'.split(), verbose=True)
#tree = parser.parse('iff see square'.split(), goal='S', verbose=True)
tree = parser.parse('iff see square press button'.split())
parser.print_tree(tree, threshold=0.52, show_match=True)


    
