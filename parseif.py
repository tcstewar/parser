import lcparser

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

parser = lcparser.LeftCornerParser(512, rules, words)

tree = parser.parse('press the button'.split(), verbose=True)
#tree = parser.parse('iff see square'.split(), goal='SBAR', verbose=True)
#tree = parser.parse('iff see square press button'.split(), verbose=True)
parser.print_tree(tree)


    