import vocab
import pointer

class Rule:
    def __init__(self, parser):
        self.parser = parser
    def utility(self):
        raise NotImplementedException()
    def apply(self):
        raise NotImplementedException()
    def label(self):
        raise NotImplementedException()
            

class LCRule(Rule):
    def __init__(self, parser, LHS, RHS):
        Rule.__init__(self, parser)
        self.LHS_text = LHS
        self.LHS = parser.vocab.parse(LHS)
        self.RHS_text = RHS
        self.RHS = [parser.vocab.parse(r) for r in RHS]
        self.L = parser.vocab.parse('L_'+LHS)
        self.match = self.RHS[0]
    def utility(self):
        return self.parser.sp_lex.dot(self.match)
    def label(self):
        return 'Apply %s -> [%s]'%(self.LHS_text, ','.join(self.RHS_text))    
    def apply(self):
        self.parser.sp_lex = self.LHS + self.L*self.parser.sp_lex
        if len(self.RHS)>1:
            self.parser.sp_tree = self.parser.sp_tree*self.parser.NEXT + self.parser.sp_lex
            self.parser.sp_lex = self.parser.sp_lex*0 
            self.parser.sp_subgoal = self.parser.sp_subgoal*self.parser.NEXT+self.RHS[1]
            self.parser.finished_word = True
            
class MergeRule(Rule):
    def __init__(self, parser, tree_type):
        Rule.__init__(self, parser)
        self.tree_type = tree_type
        self.match = parser.vocab.parse(tree_type)
        self.R = parser.vocab.parse('R_'+tree_type)
    def utility(self):
        correct_tree = self.match.dot(self.parser.sp_tree)
        correct_lex = self.parser.sp_lex.dot(self.parser.sp_subgoal)
        return correct_tree*correct_lex*1.2   # give priority to merge rules
    def label(self):
        return 'Merge lex into tree: lex=tree+R_%s*lex'%(self.tree_type)    
    def apply(self):
        self.parser.sp_lex = self.parser.sp_tree + self.R*self.parser.sp_lex
        
        self.parser.sp_subgoal = (self.parser.sp_subgoal)*(~self.parser.NEXT)
        
        # Need to subtract this off again when popping the stack;
        #   otherwise it shows up again when something else is pushed!
        self.parser.sp_tree = (self.parser.sp_tree-self.match)*(~self.parser.NEXT)
            
    


class LeftCornerParser:
    def __init__(self, dimensions, rules, words, goal='S', verbose=False, noise=0):
        self.vocab = vocab.Vocabulary(dimensions, max_similarity=0.1)
        self.verbose = verbose
        self.noise = noise
        self.dimensions = dimensions
        
        self.NEXT = pointer.SemanticPointer(dimensions)
        self.NEXT.make_unitary()
        self.vocab.add('NEXT', self.NEXT)

        self.words = words
        self.rules = rules
        
        self.label_list = [rule[0] for rule in self.rules]
        self.label_list.extend(self.words.keys())
        for w in self.words.values():
            self.label_list.extend(w)
        self.label_list = list(set(self.label_list))   # only keep unique entries
            
        for w in self.label_list:
            self.vocab.parse(w)
            if w.lower()!=w:
                # make the Ls and Rs unitary
                L = pointer.SemanticPointer(dimensions)
                L.make_unitary()
                self.vocab.add('L_'+w, L)
                R = pointer.SemanticPointer(dimensions)
                R.make_unitary()
                self.vocab.add('R_'+w, R)


        # expand out the words list into the individual rules for each word
        for category, items in words.items():
            for item in items:
                self.rules.append((category, [item]))
                
        self.match_rules = []
        merged = []
        for (LHS, RHS) in self.rules:
            if len(RHS)>1 and LHS not in merged:
                self.match_rules.append(MergeRule(self, LHS))
                merged.append(LHS)
        for (LHS, RHS) in self.rules:
            self.match_rules.append(LCRule(self, LHS, RHS))
        
        self.sp_goal = self.vocab.parse(goal)
        self.sp_subgoal = self.vocab.parse('I*0')
        self.sp_tree = self.vocab.parse('I*0')
        self.sp_lex = None    
        self.finished_word = True
        self.last_word = False
                   
                
    def rule_label(self, s, threshold=0.7):
        c = [s.dot(self.vocab.parse(rule[0])) for rule in self.rules]
        if max(c)>threshold:
            return self.rules[c.index(max(c))][0]
        else:
            return None
            
    def text_label(self, s, premult, threshold, show_match=False):
        c = [s.dot(premult*self.vocab.parse(word)) for word in self.label_list]
        if max(c)>threshold:
            text = self.label_list[c.index(max(c))]
            if show_match:
                # print dot product and probability of correct cleanup with
                #  a vocabulary size of 10000
                c2 = s.compare(premult*self.vocab.parse(text))  #needed for prob
                text+=' (%0.3f  %3d%%)'%(max(c), self.vocab.prob_cleanup(c2, 10000)*100)
            return text
        else:
            return None
            
    def print_tree(self, s, depth=0, threshold=0.5, premult=None, show_match=False):
        if depth>10: return  # stop if things get out of hand
        
        if premult is None: premult=self.vocab.parse('I')
        x = self.text_label(s, threshold=threshold, premult=premult)
        if x is not None:
            print '  '*depth+self.text_label(s, threshold=threshold, 
                                     premult=premult, show_match=show_match)
            if x.lower()!=x:
                self.print_tree(s, depth+1, threshold=threshold, 
                                     premult=premult*self.vocab.parse('L_'+x), 
                                     show_match=show_match)
                self.print_tree(s, depth+1, threshold=threshold, 
                                     premult=premult*self.vocab.parse('R_'+x), 
                                     show_match=show_match)
            
                
                
    def parse_step(self):
        if self.noise is not None:
            self.sp_tree = self.sp_tree + pointer.SemanticPointer(self.dimensions)*self.noise
            self.sp_lex = self.sp_lex + pointer.SemanticPointer(self.dimensions)*self.noise
            self.sp_subgoal = self.sp_subgoal + pointer.SemanticPointer(self.dimensions)*self.noise
    
        u = [r.utility() for r in self.match_rules]
        if self.verbose: print 'utility:',' '.join(['%3d'%int(max(uu,0)*10) for uu in u])
        max_u = max(u)
        if max_u>0.7:
            index = u.index(max_u)
            if self.verbose: print 'RULE:',self.match_rules[index].label()
            self.match_rules[index].apply()
        else:
            print 'No rule!'
            self.finished_word = True 
        if False and self.verbose:
            print 'sp_lex'
            self.print_tree(self.sp_lex, depth=2)
            print 'sp_tree'
            if self.sp_tree is not None:
                self.print_tree(self.sp_tree, depth=2)
            print 'sp_subgoal'
            print '    ',self.rule_label(self.sp_subgoal)
                
    
    def parse_word(self, word):
        self.sp_lex = self.vocab.parse(word)
        self.finished_word = False
        while not self.finished_word:
            self.parse_step()

    
    def parse(self, sentence):
        self.last_word = False
        for i, word in enumerate(sentence):
            self.parse_word(word)
        return self.sp_lex    
            
            
            
            
if __name__ == '__main__':
    import numpy as np
    np.random.seed(4)


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

    parser = LeftCornerParser(1024, rules, words, verbose=True)
    
    tree = parser.parse('the dog ran'.split())
    parser.print_tree(tree, threshold=0.5)
            
