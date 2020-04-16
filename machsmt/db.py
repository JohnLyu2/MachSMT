import pdb,os,glob,sys,copy,pickle
from progress.bar import Bar
from machsmt.search import get_inst_path
from machsmt.compute_features import get_check_sat
import machsmt.settings as settings

from machsmt.util import die

_working_database = None


class DB:

    def __init__(self):
        self.db = {}
        self.paths = {}

    def compute_score(self,logic,track,solver,inst):
        is_incr = track.lower().find('incremental') != -1 and track.lower().find('non-incremental') == -1

        if self.db[logic][track][solver][inst]['result'].find('unknown') != -1:
            return 2.0 * settings.WALL_TIMEOUT
        if not is_incr and self.db[logic][track][solver][inst]['result'] != self.db[logic][track][solver][inst]['expected']:
            if self.db[logic][track][solver][inst]['expected'].lower().find('unknown') != -1:
                return float(self.db[logic][track][solver][inst]['wallclock time'])
            elif  self.db[logic][track][solver][inst]['result'].lower().find('unknown') >= 0:
                return 2.0 * settings.WALL_TIMEOUT
            else:
                print("WRONG ANSWER!", solver, inst, logic, track, self.db[logic][track][solver][inst]['result'] ,self.db[logic][track][solver][inst]['expected'])
                return 10.0 * settings.WALL_TIMEOUT
        elif is_incr:
            if int(self.db[logic][track][solver][inst]['wrong-answers']) != 0:
                print("WRONG ANSWER!", solver, inst, logic, track)
                return 10.0 * settings.WALL_TIMEOUT
            if get_check_sat(get_inst_path(logic,inst)) == int(self.db[logic][track][solver][inst]['correct-answers']):
                if float(self.db[logic][track][solver][inst]['wallclock time']) < settings.TIMEOUT:
                    return float(self.db[logic][track][solver][inst]['wallclock time'])
                else:
                    return 2.0 * settings.WALL_TIMEOUT
            else:
                return 2.0 * settings.WALL_TIMEOUT
        else:
            if float(self.db[logic][track][solver][inst]['wallclock time']) < settings.TIMEOUT:
                return float(self.db[logic][track][solver][inst]['wallclock time'])
            else:
                return 2.0 * settings.WALL_TIMEOUT
            return float(self.db[logic][track][solver][inst]['wallclock time'])

    def add(self,logic,track,solver,instance,data):
        if logic not in self.db:
            self.db[logic] = {}
        if track not in self.db[logic]:
            self.db[logic][track] = {}
        if solver not in self.db[logic][track]:
            self.db[logic][track][solver] = {}
        if instance not in self.db[logic][track][solver]:
            self.db[logic][track][solver][instance] = None
        self.db[logic][track][solver][instance] = data

    def build(self,year=2019):
        dir = 'smt-comp/' + str(year) + '/results/'
        data_files = glob.glob(dir + '*.csv')
        print("Building DB based on the following result files: \n  {}".format('\n  '.join(data_files)))
        header = []
        benchmark_indx = None
        solver_index   = None
        for data_file in data_files:
            with open(data_file,'r') as file:
                it = 0
                for line in file:
                    if it == 0:
                        header = line.split(',')
                        header[-1] = header[-1][:-1]
                        benchmark_indx = header.index('benchmark')
                        solver_indx    = header.index('solver')
                        it+=1
                        continue
                    line = line.split(',')
                    line[-1] = line[-1][:-1]
                    theory_benchmark = line[benchmark_indx].split('/')
                    logic = theory_benchmark[1]
                    solver = line[solver_indx]
                    benchmark = ''
                    for i in range(2,len(theory_benchmark)):
                        benchmark += theory_benchmark[i]
                    val = dict((header[i],line[i]) for i in range(len(header)))
                    self.add(logic,data_file.split('.')[0],solver,benchmark,val)
                    it+=1

    def tidy(self):
        self.clean_solvers()
        self.checker()

    def solver_merger(self,logic,track,solver_0,solver_1,new_name):
        self.db[logic][track][new_name] = {}
        for instance in self.db[logic][track][solver_0]:
            self.add(logic,track,new_name,instance,self.db[logic][track][solver_0][instance])
        for instance in self.db[logic][track][solver_1]:
            self.add(logic,track,new_name,instance,self.db[logic][track][solver_1][instance])
        self.db[logic][track].pop(solver_0)
        self.db[logic][track].pop(solver_1)

    def checker(self):
        pass

    # In the some divisions of the Incremental and Challenge (incremental)
    # track of SMT-COMP 2019, StarExec had an issue where a wrong name was
    # displayed for solver Z3 4.8.4 as Z3 4.7.4
    # (see https://github.com/StarExec/StarExec/issues/269).
    # We fix this by merging the results (if possible) when the overall number
    # of entries for a Z3 configuration in a division does not match the number
    # of the number of entries of the other solvers.
    def clean_solvers(self):
        for logic in self.db:
            for track in self.db[logic]:
                solver_counts = dict( (solver , len(self.db[logic][track][solver]))  for solver in self.db[logic][track])
                if min(list(solver_counts.values())) != max(list(solver_counts.values())):
                    #print('Inconsistent solving counts for: {} {}'.format(logic, track), solver_counts,flush=True)
                    z3_solvers_wrapped = [solver for solver in solver_counts if solver.lower().find('z3') != -1 and solver.lower().find('wrap') != -1]
                    if len(z3_solvers_wrapped) == 2:
                        self.solver_merger(logic,track,z3_solvers_wrapped[0],z3_solvers_wrapped[1],'z3')
                        solver_counts = dict( (solver , len(self.db[logic][track][solver]))  for solver in self.db[logic][track])
                        if min(list(solver_counts.values())) == max(list(solver_counts.values())):
                            continue

                    print("FAILED TO AUTO FIX.")
                    sys.exit(1)

        #print("Finished Cleaning Solvers!")

    def clean_benchmarks(self):
        inputs = set()
        
        print("Enumerating Inputs.", flush=True)
        for logic in self.db:
             for track in self.db[logic]:
                 first_solver = list(self.db[logic][track].keys())[0]
                 for solver in self.db[logic][track]:
                     assert len(self.db[logic][track][solver]) == len(self.db[logic][track][first_solver])
                     for instance in self.db[logic][track][first_solver]:
                         inputs.add((logic,instance))
        bar = Bar('Checking Existence of Inputs', max=len(inputs))
        remove = set()
        for logic,instance in inputs:
            v = get_inst_path(logic,instance)
            if v == None:
                remove.add(instance)
            bar.next()
        bar.finish()
        print("Total to be removed: " + str(len(remove)),flush=True)
        tmp_db = copy.deepcopy(self.db)
        for logic in self.db:
             for track in self.db[logic]:
                 for solver in self.db[logic][track]:
                     for instance in remove:
                         if instance in self.db[logic][track][solver]:
                             tmp_db[logic][track][solver].pop(instance)
        self.db = tmp_db

    def get_inst_path(self,logic,instance):
        path = 'benchmarks/' + logic + '/'
        instance_name = instance
        if os.path.exists(path + '/' + instance):
            return path + '/' + instance
        else:
            canidates = [None]
            while len(canidates) > 0:
                canidates = []
                directories = [v.split('/')[-2] for v in glob.glob(path+'*/')] 
                for dir in directories:
                    if instance_name.startswith(dir):
                        canidates.append(dir)
                best , longest = None,0
                for c in canidates:
                    if len(c) > longest:
                        best = c
                        longest = len(c)
                if best != None:         
                    path = path + best + '/'
                    instance_name = instance_name[len(best):]
        if os.path.exists(path + '/' + instance_name):
            return path + '/' + instance_name
        else:
            print("Failed to find: " + logic + ',' + instance)
            return None

    def summary(self):
        for logic in self.db:
            print(logic)
            for track in self.db[logic]:
                print("\t" + track)
                for solver in self.db[logic][track]:
                    print("\t\t" + solver + "\t" + str(len(self.db[logic][track][solver])))

    def __getitem__(self, index):
        try:
            if isinstance(index,str):
                return self.db[index]
            elif isinstance(index,tuple):
                ret = self.db
                for k in index:
                    ret = ret[k]
                return ret
        except IndexError:
            print("Invalid Index: ")
def working_database():
    global _working_database
    if _working_database == None:
        db_file = os.path.join(settings.LIB_DIR, 'db.p')
        if not os.path.exists(db_file):
            _working_database = DB()
            _working_database.build()
            _working_database.tidy()
            with open(db_file, 'wb') as outfile:
                pickle.dump(_working_database, outfile)
        else:
            with open(db_file, 'rb') as infile:
                db = pickle.load(infile)
    return _working_database