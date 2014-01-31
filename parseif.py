import numpy as np
import copy
np.random.seed(6)

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
    'N': 'button square circle switch'.split(),
    'DET': 'the'.split(),
    'V': 'press see'.split(),
    'IN': 'iff'.split(),
    }

parser = lcparser.LeftCornerParser(1024, rules, words, verbose=True)
# parser2 = lcparser.LeftCornerParser(1024, rules, words, verbose=True)
# parser2.vocab = copy.deepcopy(parser.vocab)

#tree = parser.parse('press the button'.split())
#tree = parser.parse('iff see square'.split(), goal='S')
tree2 = parser.parse('iff see circle press switch'.split())
parser.print_tree(tree2, threshold=0.52, show_match=True)

tree = parser.parse('iff see square press button'.split())
parser.print_tree(tree, threshold=0.52, show_match=True)

# tree2 = parser2.parse('iff see circle press switch'.split())
# parser2.print_tree(tree2, threshold=0.52, show_match=True)
# parser.print_tree(tree, threshold=0.52, show_match=True)


    
