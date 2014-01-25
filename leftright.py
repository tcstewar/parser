D = 512

from vocab import Vocabulary

input_sentence = 'the dog ran'.split()

rules = [
    ('S', ['NP', 'VP']),
    ('VP', ['V']),
    ('NP', ['DET', 'N']),
    ]
    
words = {
    'N': 'man dog'.split(),
    'DET': 'a the'.split(),
    'V': 'ran saw'.split(),
    }
def label_word(s):
    best = None
    for w in words.values():
        for ww in w:
            c = s.dot(vocab.parse(ww))
            if best is None or best<c:
                best = c
                best_word = ww
    'word', best, best_word            
    if best > 0.7:
        return best_word
    return None
                
    
def label(s):
    c = [s.dot(vocab.parse(rule[0])) for rule in rules]
    if max(c)>0.7:
        return rules[c.index(max(c))][0]
    else:
        return None
        
def print_tree(s, depth=0):
    x = label(s)
    if x is None:
        x = label_word(s)
        
        if x is not None: 
            print '  '*depth+x
        return
    print '  '*depth+label(s)
    print_tree(s*vocab.parse('~L_'+x), depth+1)
    print_tree(s*vocab.parse('~R_'+x), depth+1)
        
    
    
vocab = Vocabulary(D)    

NEXT = vocab.parse('NEXT')

for category, items in words.items():
    for item in items:
        rules.append((category, [item]))
print rules    
    
sp_goal = vocab.parse('S')

sp_tree = None
    
for input in input_sentence:
    print 'parsing text:', input
    
    sp_lex = vocab.parse(input)
    
    while True:
        print 'looking for rules with LC=', vocab.text(sp_lex, include_pairs=False, maximum_count=1)
        
        
        if sp_lex.dot(sp_goal)>0.7:
            print 'found goal', label(sp_goal)
            
            if sp_tree is None:
                print 'done'
                break
                pass
            else:
                #print 'merging'
                #print 'lex:'
                #print_tree(sp_lex, depth=2)
                #print 'tree:'
                #print_tree(sp_tree, depth=2)
                
                sp_lex = sp_tree+vocab.parse('R_'+label(sp_tree))*sp_lex
                
                #print 'result:'
                #print_tree(sp_lex, depth=2)
                sp_goal = sp_goal*~NEXT
                sp_tree = None
            print_tree(sp_lex)
        else:    
                
            
            best_rule = None
            best_match = None
            for rule in rules:
                LHR, RHS = rule
                c = sp_lex.dot(vocab.parse(RHS[0]))
                
                if best_rule is None or c>best_match:
                    best_rule = rule
                    best_match = c
            
            if best_match > 0.7:
                LHS, RHS = best_rule
                print 'using rule', LHS, RHS, best_match

                sp_lex = vocab.parse(LHS)+vocab.parse('L_'+LHS)*sp_lex
                
                print_tree(sp_lex)
                
                
                if len(RHS)>1:
                    sp_tree = sp_lex
                    sp_goal = sp_goal*NEXT+vocab.parse(RHS[1])
                    break
            else:
                print 'no rule to match'
                break
            
                
            
    
    
    
    
print_tree(sp_lex)        
    
            
    
    


