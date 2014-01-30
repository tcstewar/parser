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

correct = [
    'the*L_DET*L_NP*L_S',
    'dog*L_N*R_NP*L_S',
    'chases*L_V*L_VP*R_S',
    'the*L_DET*L_NP*R_VP*R_S',
    'cat*L_N*R_NP*R_VP*R_S',
    ]
    
    
    
    
def test(sentence, noise):
    parser = lcparser.LeftCornerParser(1024, rules, words, noise=noise)
    tree = parser.parse(sentence.split())
    
    score = [tree.compare(parser.vocab.parse(c)) for c in correct]
    prob = [parser.vocab.prob_cleanup(s, 10000) for s in score]
    
    total = 1.0
    for p in prob: total*=p
    
    print prob
    print total
    #parser.print_tree(tree, threshold=0.52, show_match=True)

    
test('the dog chases the cat', noise=0.1)      

  
   
