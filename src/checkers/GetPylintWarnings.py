import argparse
import subprocess
from git.repo import Repo
import os
from os.path import join
import shutil


parser = argparse.ArgumentParser(description="Gather all Pylint warnings in a specific commit")
parser.add_argument("--repo_dir", help="Directory with the repository to check, endswith '/'", required=True)
parser.add_argument("--commit_id", help="Specify which commit to run checkers", required=True)
parser.add_argument("--results_dir", help="Directory where to put the results, endswith '/'", required=True)


class GetPylintWarnings(): 
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
        '''
        target_repo = Repo(self.repo_dir)
        target_repo.git.checkout(self.commit_id)
        os.chdir(self.repo_dir) # go to repo_dir to run checkers
        
        commit_results_dir = self.results_dir + "checker_results/" + self.commit_id + "/"
        if not os.path.exists(commit_results_dir):
            os.makedirs(commit_results_dir)
        report = commit_results_dir + self.commit_id + "_pylint.txt"
        '''
        Option: choose to disable I, R message or not 

        [I]nformational messages that Pylint emits (do not contribute to your analysis score)
        [R]efactor for a "good practice" metric violation
        [C]onvention for coding standard violation
        [W]arning for stylistic problems, or minor programming issues
        [E]rror for important programming issues (i.e. most probably bug)
        [F]atal for errors which prevented further processing
        here do not consider about I and F.
        '''
        command_line = "pylint --recursive=y --disable=I,R ./ > " + report
        subprocess.run(command_line, shell=True)

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
            f.close()

        return warnings 
    
    def write_warning_list(self, warnings, commit_results_dir):
        '''
        Write all reported warnings to a csv file.
        '''
        with open(join(commit_results_dir, self.commit_id + "_warnings.csv"), "w") as f:
            write_str = ""
            for single_warning in warnings:
                single_write_str = single_warning['file_path'] + "," + single_warning['warning_type'] + "," + single_warning['line_number']
                write_str = write_str + single_write_str + "\n"
            f.write(write_str)
        f.close()


def main(repo_dir, commit_id, results_dir):
    init = GetPylintWarnings(repo_dir, commit_id, results_dir)
    report, commit_results_dir = init.run_checker()
    warnings = init.read_reports(report)
    if warnings:
        init.write_warning_list(warnings, commit_results_dir)
    else:
        shutil.rmtree(commit_results_dir)
        print("No reported warnings.")

    print("Done.")

    
if __name__=="__main__":
    args = parser.parse_args()
    main(args.repo_dir, args.commit_id, args.results_dir)
