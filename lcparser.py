import vocab
import pointer

threshold = 0.7

class LeftCornerParser:
    def __init__(self, dimensions, rules, words):
        self.vocab = vocab.Vocabulary(dimensions, max_similarity=0.1)
        
        self.NEXT = pointer.SemanticPointer(dimensions)
        self.NEXT.make_unitary()
        self.vocab.add('NEXT', self.NEXT)

        self.words = words
        self.rules = rules
        
        self.label_list = [rule[0] for rule in self.rules]
        self.label_list.extend(self.words.keys())
        for w in self.words.values():
            self.label_list.extend(w)
        print self.label_list    
        
        # expand out the words list into the individual rules for each word
        for category, items in words.items():
            for item in items:
                self.rules.append((category, [item]))
        
        
    def word_label(self, s, threshold=threshold):
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
    def rule_label(self, s, threshold=threshold):
        c = [s.dot(self.vocab.parse(rule[0])) for rule in self.rules]
        if max(c)>threshold:
            return self.rules[c.index(max(c))][0]
        else:
            return None
            
    def text_label(self, s, threshold=threshold, show_match=False):
        c = [s.compare(self.vocab.parse(word)) for word in self.label_list]
        if max(c)>threshold:
            text = self.label_list[c.index(max(c))]
            if show_match:
                text+=' (%0.3f)'%max(c)
            return text
        else:
            return None
        
        
    def print_tree(self, s, depth=0, threshold=0.05):
        if depth>10: return  # stop if things get out of hand
        x = self.text_label(s, threshold=threshold)
        if x is not None:
            print '  '*depth+self.text_label(s, threshold=threshold, show_match=True)
            if x.lower()!=x:
                self.print_tree(s*self.vocab.parse('~L_'+x), depth+1, threshold=threshold*1)
                self.print_tree(s*self.vocab.parse('~R_'+x), depth+1, threshold=threshold*1)
        
    def parse(self, sentence, goal='S', verbose=False):
        sp_goal = self.vocab.parse(goal)   # this is what I'm looking for (top-down)
        if verbose:
            print 'STARTING GOAL'
            self.print_tree(sp_goal, depth=2)

        sp_tree = None  # this is what I have
    
        for input in sentence:
            if verbose: print 'Reading input text:',input
            sp_lex = self.vocab.parse(input)
            while True:
                print 'CURRENT GOAL'
                self.print_tree(sp_goal, depth=2)
                
                if sp_lex.dot(sp_goal)>0.7:
                    if verbose: print 'we have found goal', self.rule_label(sp_goal), sp_lex.dot(sp_goal), sp_lex.dot(self.vocab.parse('VP'))
                    if sp_tree is None:
                        # no previous stuff to connect this one to
                        if verbose: print 'done'
                        break
                        pass
                    else:
                        # connect this to the existing tree
                        sp_lex = sp_tree+self.vocab.parse('R_'+self.rule_label(sp_tree))*sp_lex
                        
                        # pop an item off the stack
                        sp_goal = sp_goal*self.vocab.parse('~NEXT')
                        sp_tree = sp_tree*self.vocab.parse('~NEXT')
                        if verbose:
                            print 'popping up stack'
                            print ' sp_goal'
                            self.print_tree(sp_goal, depth=2)
                            print ' sp_tree'
                            self.print_tree(sp_tree, depth=2)
                            print ' sp_lex'
                            self.print_tree(sp_lex, depth=2)
                            
                        if self.rule_label(sp_tree) is None:
                            if verbose: 'stack is clear'
                            # nothing is recognizable here, so ignore it
                            sp_tree = None
                else:    
                    # try to find a bottom-up rule
                    if verbose: print 'looking for rules handling', self.text_label(sp_lex)
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
                        
                        if verbose:
                            print 'sp_lex'
                            self.print_tree(sp_lex, depth=2)
                        
                        if len(RHS)>1:
                            print 'pushing stack'
                            if sp_tree is not None:
                                if verbose:
                                    print 'old tree:', sp_tree.norm()
                                    self.print_tree(sp_tree, depth=2)
                                    print 'new part:', sp_lex.norm()
                                    self.print_tree(sp_lex, depth=2)
                                    
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


    