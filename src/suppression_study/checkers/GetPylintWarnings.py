import argparse
from suppression_study.checkers.GetWarningsSuper import GetWarningsSuper
import os
import shutil


parser = argparse.ArgumentParser(description="Gather all Pylint warnings in a specific commit")
parser.add_argument("--repo_dir", help="Directory with the repository to check", required=True)
parser.add_argument("--commit_id", help="Specify which commit to run checkers", required=True)
parser.add_argument("--results_dir", help="Directory where to put the results", required=True)


class GetPylintWarnings(GetWarningsSuper): 
    '''
    By receiving a repository and a commit, this script will run Pylint checker 
    on the specified commit, and return a warning list (written to a csv file.).
    '''
    def __init__(self, repo_dir, commit_id, results_dir):
        self.repo_dir = repo_dir
        self.commit_id = commit_id
        self.results_dir = results_dir
    
    def run_checker(self):
        '''
        Run Pylint checker, Return a report file

        Option: choose to disable I, R message or not 
        [I]nformational messages that Pylint emits (do not contribute to your analysis score)
        [R]efactor for a "good practice" metric violation
        [C]onvention for coding standard violation
        [W]arning for stylistic problems, or minor programming issues
        [E]rror for important programming issues (i.e. most probably bug)
        [F]atal for errors which prevented further processing
        here do not consider about I and F.
        '''
        checker = "pylint"
        command_line = "pylint --recursive=y --disable=I,R ./"
        report, commit_results_dir = super(GetPylintWarnings, self).run_checker(checker, command_line)

        return report, commit_results_dir

    def read_reports(self, report): 
        '''
        Read reports, Return a warning list.
        Pylint report format: 
            eg,. folder1/bar.py:1:0: C0104: Disallowed name "bar" (disallowed-name)
        '''
        warnings = [] # If no issues related to target file, the return warnings will be empty
        if os.path.getsize(report): 
            message_types = ("R", "C", "W", "E")
            with open(report, "r") as f:
                line = f.readline()
                while line:
                    if line.count(":") > 3: # in general, with 4 ":".
                        contents = line.split(":")
                        warning_code = contents[3].strip()
                        if warning_code.startswith(message_types):
                            file_path = contents[0].strip()
                            line_number = contents[1].strip()
                            # specific warning type
                            warning_type = line.split("(")[-1].replace(")", "").strip() 
                            warning_dict = {"file_path" : file_path,
                                    "warning_type" : warning_type,
                                    "line_number" : line_number}
                            warnings.append(warning_dict)
                    line = f.readline()

        return warnings 
    
    def write_warning_list(self, warnings, commit_results_dir):
        '''
        Write all reported warnings to a csv file.
        '''
        super(GetPylintWarnings, self).write_warning_list(warnings, commit_results_dir)


def main(repo_dir, commit_id, results_dir):
    init = GetPylintWarnings(repo_dir, commit_id, results_dir)
    report, commit_results_dir = init.run_checker()
    warnings = init.read_reports(report)
    init.write_warning_list(warnings, commit_results_dir)


if __name__=="__main__":
    args = parser.parse_args()
    main(args.repo_dir, args.commit_id, args.results_dir)   
    