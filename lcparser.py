import vocab

threshold = 0.7

class LeftCornerParser:
    def __init__(self, dimensions, rules, words):
        self.vocab = vocab.Vocabulary(dimensions, max_similarity=0.1)

        self.words = words
        self.rules = rules
        
        # expand out the words list into the individual rules for each word
        for category, items in words.items():
            for item in items:
                self.rules.append((category, [item]))
        
        
    def word_label(self, s):
        best = None
        for w in self.words.values():
            for ww in w:
                c = s.dot(self.vocab.parse(ww))
                if best is None or best<c:
                    best = c
                    best_word = ww
        if best > threshold:
            return best_word
        return None
    def label(self, s):
        c = [s.dot(self.vocab.parse(rule[0])) for rule in self.rules]
        if max(c)>threshold:
            return self.rules[c.index(max(c))][0]
        else:
            return None
        
    def print_tree(self, s, depth=0):
        if depth>20: return  # stop if things get out of hand
        x = self.label(s)
        if x is None:
            x = self.word_label(s)
            if x is not None: 
                print '  '*depth+x
            return
        print '  '*depth+self.label(s)
        self.print_tree(s*self.vocab.parse('~L_'+x), depth+1)
        self.print_tree(s*self.vocab.parse('~R_'+x), depth+1)
        
    def parse(self, sentence, goal='S', verbose=False):
        sp_goal = self.vocab.parse(goal)   # this is what I'm looking for (top-down)

        sp_tree = None  # this is what I have
    
        for input in sentence:
            if verbose: print 'Reading input text:',input
            sp_lex = self.vocab.parse(input)
            while True:
                if verbose: print 'checking if we are at current goal',self.label(sp_goal)
                if sp_lex.dot(sp_goal)>threshold:
                    if verbose: print 'we have found goal', self.label(sp_goal)
                    if sp_tree is None:
                        # no previous stuff to connect this one to
                        if verbose: print 'done'
                        break
                        pass
                    else:
                        # connect this to the existing tree
                        sp_lex = sp_tree+self.vocab.parse('R_'+self.label(sp_tree))*sp_lex
                        
                        # pop an item off the stack
                        sp_goal = sp_goal*self.vocab.parse('~NEXT')
                        sp_tree = sp_tree*self.vocab.parse('~NEXT')
                        if self.label(sp_tree) is None:
                            # nothing is recognizable here, so ignore it
                            sp_tree = None
                else:    
                    # try to find a bottom-up rule
                    if verbose: print 'looking for rules handling', self.label(sp_lex), self.word_label(sp_lex)
                    best_rule = None
                    best_match = None
                    for rule in self.rules:
                        LHR, RHS = rule
                        c = sp_lex.dot(self.vocab.parse(RHS[0]))
                        
                        if best_rule is None or c>best_match:
                            best_rule = rule
                            best_match = c
                    
                    
                    if best_match > threshold:
                        # apply the rule
                        LHS, RHS = best_rule
                        if verbose: print 'using rule %s->%s'%(LHS, RHS)
                        sp_lex = self.vocab.parse(LHS)+self.vocab.parse('L_'+LHS)*sp_lex
                        if len(RHS)>1:
                            if sp_tree is not None:
                                if verbose:
                                    print 'old tree:'
                                    self.print_tree(sp_tree, depth=2)
                                # do we really have to do a stack of previous trees? 
                                sp_tree = sp_tree*self.vocab.parse('NEXT') + sp_lex
                            else:    
                                sp_tree = sp_lex
                            sp_goal = sp_goal*self.vocab.parse('NEXT')+self.vocab.parse(RHS[1])
                            break
                    else:
                        break
        return sp_lex
    


if __name__ == '__main__':
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

    parser = LeftCornerParser(512, rules, words)
    
    tree = parser.parse('the dog ran'.split())
    parser.print_tree(tree)


    