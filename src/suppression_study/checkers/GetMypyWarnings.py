import argparse
from suppression_study.checkers.GetWarningsSuper import GetWarningsSuper
from suppression_study.warnings.Warning import Warning


parser = argparse.ArgumentParser(description="Gather all Mypy warnings in a specific commit")
parser.add_argument("--repo_dir", help="Directory with the repository to check", required=True)
parser.add_argument("--commit_id", help="Specify which commit to run checkers", required=True)
parser.add_argument("--results_dir", help="Directory where to put the results", required=True)


class GetMypyWarnings(GetWarningsSuper): 
    '''
    By receiving a repository and a commit, this script will run Mypy checker 
    on the specified commit, and return a warning list (written to a csv file.).
    '''
    def __init__(self, repo_dir, commit_id, results_dir):
        self.repo_dir = repo_dir
        self.commit_id = commit_id
        self.results_dir = results_dir
    
    def run_checker(self):
        '''
        Run Mypy checker, Return a report file
        '''
        checker = "mypy"
        command_line = "mypy ./"
        report, commit_results_dir = super(GetMypyWarnings, self).run_checker(checker, command_line)

        return report, commit_results_dir

    def read_reports(self, report): 
        '''
        Read reports, Return a warning list.
        Mypy report format: 
            format 1: chia/util/struct_stream.py:80: 
                    error: Signature of "from_bytes" incompatible with supertype "int"  [override]
                    ...
                    end with "Found 8 errors in 1 files (checked 1 source file)"
            format 2: Success: no issues found in 1 source file
        '''
        warnings = [] # If no issues related to target file, the return warnings will be empty
        with open(report, "r") as f: 
            line = f.readline()
            while line:
                if line.startswith("Success:"): # no issues found. the report should only with 1 line.
                    pass
                if " error: " in line:
                    file_path = line.split(":")[0].strip()
                    line_number = int(line.split(":")[1].strip())
                    if "[" in line:
                        warning_type = line.split("[")[-1].replace("\n", "").replace("]", "").strip()
                    else:
                        warning_type = line.split(":")[-1].strip()

                    # TODO For some repos (e.g., autogluon at commit 0a00e065) mypy produces an error that doesn't have a line number,
                    # which leads to an incorrect entry in the warnings csv.
                    # The following is a temporary fix, which simply ignores such errors.
                    # if line_number.isdigit():
                    warning_object = Warning(file_path, warning_type, line_number)
                    warnings.append(warning_object)
                line = f.readline()

        return warnings 
    
    def write_warning_list(self, warnings, commit_results_dir):
        '''
        Write all reported warnings to a csv file.
        '''
        super(GetMypyWarnings, self).write_warning_list(warnings, commit_results_dir)


def main(repo_dir, commit_id, results_dir):
    init = GetMypyWarnings(repo_dir, commit_id, results_dir)
    report, commit_results_dir = init.run_checker()
    warnings = init.read_reports(report)
    init.write_warning_list(warnings, commit_results_dir)


if __name__=="__main__":
    args = parser.parse_args()
    main(args.repo_dir, args.commit_id, args.results_dir)
    
