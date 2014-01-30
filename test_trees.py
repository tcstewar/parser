import lcparser_v2 as lcparser

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
    'N': 'button square dog cat'.split(),
    'DET': 'the'.split(),
    'V': 'press see chases'.split(),
    'IN': 'iff'.split(),
    }

    
    
def test(goal, sentence):
    parser = lcparser.LeftCornerParser(1024, rules, words, goal=goal, verbose=True, noise=0)
    tree = parser.parse(sentence.split())
    parser.print_tree(tree, threshold=0.52, show_match=True)

    
test('S', 'the dog chases the cat')        
   
import numpy as np
np.random.seed(6)
  
#test('S', 'iff see square press button')    