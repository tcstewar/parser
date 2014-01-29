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
            if self.parser.sp_tree is not None:
                # TODO: can we get rid of this special case and just convolve regardless?
                self.parser.sp_tree = self.parser.sp_tree*self.parser.NEXT + self.parser.sp_lex
            else:
                self.parser.sp_tree = self.parser.sp_lex
            self.parser.sp_goal = self.parser.sp_goal*self.parser.NEXT+self.RHS[1]
            self.parser.finished_word = True
            
class MergeRule(Rule):
    def utility(self):
        return self.parser.sp_lex.dot(self.parser.sp_goal)*2
    def label(self):
        return 'Merge lex into tree'    
    def apply(self):
        if self.parser.sp_tree is None:
            print 'could not merge'
            self.parser.finished_word=True  
        else:
            type = self.parser.rule_label(self.parser.sp_tree)
            R = self.parser.vocab.parse('R_'+type)
            self.parser.sp_lex = self.parser.sp_tree + R*self.parser.sp_lex
            
            self.parser.sp_goal = self.parser.sp_goal*(~self.parser.NEXT)
            self.parser.sp_tree = self.parser.sp_tree*(~self.parser.NEXT)
                
            type = self.parser.rule_label(self.parser.sp_tree)
            if type is None:
                self.parser.sp_tree = None
    


class LeftCornerParser:
    def __init__(self, dimensions, rules, words, goal='S', verbose=False):
        self.vocab = vocab.Vocabulary(dimensions, max_similarity=0.1)
        self.verbose = verbose
        
        self.NEXT = pointer.SemanticPointer(dimensions)
        self.NEXT.make_unitary()
        self.vocab.add('NEXT', self.NEXT)

        self.words = words
        self.rules = rules
        
        self.label_list = [rule[0] for rule in self.rules]
        self.label_list.extend(self.words.keys())
        for w in self.words.values():
            self.label_list.extend(w)
        self.label_list = list(set(self.label_list))    
            
        print self.label_list    
        for w in self.label_list:
            self.vocab.parse(w)
            if w.lower()!=w:
                print w
                L = pointer.SemanticPointer(dimensions)
                L.make_unitary()
                self.vocab.add('L_'+w, L)
                R = pointer.SemanticPointer(dimensions)
                R.make_unitary()
                self.vocab.add('R_'+w, R)


                #self.vocab.parse('L_'+w)
                #self.vocab.parse('R_'+w)

        # expand out the words list into the individual rules for each word
        for category, items in words.items():
            for item in items:
                self.rules.append((category, [item]))
                
        self.match_rules = [MergeRule(self)]
        for (LHS, RHS) in self.rules:
            self.match_rules.append(LCRule(self, LHS, RHS))
        
        self.sp_goal = self.vocab.parse(goal)
        self.sp_tree = None
        self.sp_lex = None    
        self.finished_word = True
                   
                
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
                text+=' (%0.3f)'%max(c)
            return text
        else:
            return None
            
    def print_tree(self, s, depth=0, threshold=0.1, premult=None):
        if premult is None: premult=self.vocab.parse('I')
        if depth>10: return  # stop if things get out of hand
        x = self.text_label(s, threshold=threshold, premult=premult)
        if x is not None:
            print '  '*depth+self.text_label(s, threshold=threshold, premult=premult, show_match=True)
            if x.lower()!=x:
                self.print_tree(s, depth+1, threshold=threshold, premult=premult*self.vocab.parse('L_'+x))
                self.print_tree(s, depth+1, threshold=threshold, premult=premult*self.vocab.parse('R_'+x))
            
                
                
    def parse_step(self):
        u = [r.utility() for r in self.match_rules]
        print ' '.join(['%+4.1f'%uu for uu in u])
        max_u = max(u)
        if max_u>0.7:
            index = u.index(max_u)
            if self.verbose:
                print 'RULE:',self.match_rules[index].label()
            self.match_rules[index].apply()
                
    
    def parse_word(self, word):
        self.sp_lex = self.vocab.parse(word)
        self.finished_word = False
        while not self.finished_word:
            self.parse_step()

    
    def parse(self, sentence):
        for word in sentence:
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

    parser = LeftCornerParser(512, rules, words, verbose=True)
    
    tree = parser.parse('the dog ran'.split())
    parser.print_tree(tree, threshold=0.07)
            
