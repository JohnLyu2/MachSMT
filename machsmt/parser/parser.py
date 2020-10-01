import argparse,os

parser = argparse.ArgumentParser()

parser.add_argument("-f", "--data-files",
                metavar="files[,files...]",
                action="store",
                dest="files",
                default=None,
                nargs='+',
                help="Input Data files containing solver, benchmark, runtime pairs"
)

parser.add_argument("-l", "--lib-directory",
            metavar="lib",
            action="store",
            dest="lib",
            default=None,
            type=str,
            help="Library directory, save state for machsmt"
)

parser.add_argument("-r", "--results-directory",
            metavar="results",
            action="store",
            dest="results",
            default="results",
            type=str,
            help="Results directory, save results of machsmt"
)

parser.add_argument("-k", "--k-fold-value",
            metavar="k",
            action="store",
            dest="k",
            default=5,
            type=int,
            help="K Fold Cross Validation parameter",
)

parser.add_argument("-profile",
            metavar="profile",
            action="store",
            dest="profile",
            default=False,
            type=bool,
            help="Profile MachSMT"
)

parser.add_argument("--min-datapoints",
            metavar="min_datapoints",
            action="store",
            dest="min_datapoints",
            default=10,
            type=int,
            help="Minimum number of datapoints needed to build MachSMT.",
)



parser.add_argument("-c", "--num_cpus",
            metavar="cores",
            action="store",
            dest="cores",
            default=os.cpu_count(),
            type=int,
            help="Number of CPUs to run in parallel."
)

parser.add_argument("-pca", "--pca-diminsions",
            metavar="pca",
            action="store",
            dest="pca",
            default=35,
            type=int,
            help="Number of diminsions in PCA",
)

parser.add_argument("-rng",
            metavar="rng",
            action="store",
            dest="rng",
            default=42,
            type=int,
            help="Library directory, save state of the database of machsmt"
)

parser.add_argument('--no-semantic-features', 
                    action='store_false',
                    dest="semantic_features",
                    help="Generate benchmarks with width 128"
)

parser.add_argument('--run-all-eval', 
                    action='store_true',
                    dest="rerun_eval",
                    help="Rerun and overwrite evaluation"
)

parser.add_argument("-debug",
            metavar="debug",
            action="store",
            dest="debug",
            default=True,
            type=bool,
            help="Run in debug mode"
)

parser.add_argument("-wall",
            metavar="wall",
            action="store",
            dest="wall",
            default=False,
            type=bool,
            help="Exit on warning"
)

parser.add_argument("-t", "--timeout",
            metavar="timeout",
            action="store",
            dest="timeout",
            default=2400,
            type=int,
            help="Number of CPUs to run in parallel."
)

parser.add_argument('--smt-comp-year',
            metavar="smtcomp_year",
            action="store",
            dest="smtcomp_year",
            default=2020,
            type=int,
            help="SMT-COMP Evaluation year"
)

parser.add_argument('--smt-comp-files',
            metavar="smtcomp_files",
            action="store",
            dest="smtcomp_files",
            default=2020,
            type=int,
            help="SMT-COMP Evaluation year"
)

parser.add_argument('--smt-comp-loc',
            metavar="smtcomp_loc",
            action="store",
            dest="smtcomp_loc",
            default='smt-comp',
            type=str,
            help="SMT-COMP github location"
)

parser.add_argument('--eval-logic',
            metavar="eval_logic",
            action="store",
            dest="eval_logic",
            default=None,
            type=str,
            help="Evaluation Logic"
)

parser.add_argument("--feature-timeout",
            metavar="feature_timeout",
            action="store",
            dest="feature_timeout",
            default=10,
            type=int,
            help="Number of CPUs to run in parallel."
)

args = parser.parse_args()
