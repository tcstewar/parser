D = 128

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
    
vocab = Vocabulary(D)    

for category, items in words.items():
    for item in items:
        vocab.add(item, vocab.parse('CATEGORY*%s+TEXT*text_%s'%(category, item)))
    
sp_goal = vocab.parse('S')

    
for input in input_sentence:
    print 'parsing text:', input
    sp_lex = vocab.parse(input)
    
    category = sp_lex*vocab.parse('~CATEGORY')
    
    while True:
        print 'looking for rules with LC=', vocab.text(category, include_pairs=False, maximum_count=1)
        for LHS, RHS in rules:
            c = category.dot(vocab.parse(RHS[0]))
            if c>0.7:
                print 'matched rule', LHS, RHS, c
                
            sp_part = vocab.parse('CATEGORY*%s')+vocab.parse('HEAD')*sp_lex
            #if len(RHS)>0
              
            
    
    
    
    
    
        
    
            
    
    


