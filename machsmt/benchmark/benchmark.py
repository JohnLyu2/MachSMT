import os,pdb,sys,time
from machsmt.parser import args as settings
from machsmt.util import die
from machsmt.tokenize_sexpr import SExprTokenizer
from ..smtlib import grammatical_construct_list,logic_list,get_smtlib_file
from ..features import bonus_features
# import ..extra_features

keyword_to_index = dict( (grammatical_construct_list[i],i) for i in range(len(grammatical_construct_list)))

class Benchmark:
    def __init__(self,name:str):
        self.name = name
        self.path = name if os.path.exists(name) else get_smtlib_file(name)
        self.features = None
        self.theory = None
        self.timeout = False
        self.logic = 'ALL'
        self.track = 'UNKNOWN' ## 'SQ' or 'INC'
        self.family = None
        self.check_sats = 0
        self.score = None
        self.graph = None
        self.parsed = False

    def make_graph(self):
        pass

    ## Compute Features up to a timeout
    def compute_features(self):
        self.compute_core_features()
        self.compute_bonus_features()

    def compute_core_features(self):
        start = time.time()
        self.features = [0] * (len(grammatical_construct_list) + 2)
        #recursion handle
        def get_constructs(sexpr):
            ret = {}
            for v in sexpr:
                if time.time() - start > settings.feature_timeout:
                    self.timeout = True
                    return
                if isinstance(v,str): 
                    if v in keyword_to_index: self.features[keyword_to_index[v]] += 1
                elif isinstance(v,list): get_constructs(v)
                else: die("parsing error on: " + self.path + " " + str(type(v)))
        tokenizer = SExprTokenizer(self.path)

        self.features[-2] = 1 if self.timeout else -1           #feature calc timeout?
        self.features[-1] = float(os.path.getsize(self.path))   #benchmark file size


        for sexpr in tokenizer:
            if self.timeout: break
            try:                    get_constructs(sexpr)
            except RecursionError:  pass

    def compute_bonus_features(self):
        for feat in bonus_features:
            ret = feat(self.path)
            try:
                val = float(ret)
                self.features.append(val)
            except:
                for v in ret:
                    val = float(ret)
                    self.features.append(val)

    ## Get and if necessary, compute features.
    def get_features(self):
        if self.features != None: return self.features
        self.compute_features()
        return self.features

    # full parsing of input file.
    # compute logic, track, # check-sat
    def parse(self):
        if self.parsed: return
        tokenizer = SExprTokenizer(self.path)
        for sexpr in tokenizer:
            # print(sexpr)
            if len(sexpr) > 0 and sexpr[0]  == 'check-sat': self.check_sats += 1
            if len(sexpr) >= 2 and sexpr[0] == 'set-logic': self.logic = sexpr[1]
        assert self.logic in logic_list or self.logic == 'ALL'
        assert self.check_sats >= 1
        self.track = 'SQ' if self.check_sats == 1 else 'INC'
        self.parsed=True

    def __str__(self): return self.name

    __repr__ = __str__

    def __hash__(self):
        return hash(str(self))