import argparse
import subprocess
from os.path import join
import os


parser = argparse.ArgumentParser(description="Gather all Pylint warnings in a specific commit")
parser.add_argument("--language", help="target language (all with lower cases)", required=True)
parser.add_argument("--repo_dir", help="Directory with the repository to check", required=True)
parser.add_argument("--commit_id", help="Commit to check", required=True)
parser.add_argument("--grep_suppression_commit_level", help=".csv file with suppression in target repo_dir and target commit", required=True)
parser.add_argument("--results_dir", help="Result directory of the given repository", required=True)


class get_warning_list():
    ''' 
    Analyze which checkers are used in given repository.
    Run checkers to get reports, and analysis the reports.
    Return a warning list.
    (Cover both Mypy and Pylint)
    '''
    def __init__(self, language, repo_dir, commit_id, grep_suppression_commit_level, results_dir):
        self.language = language
        self.repo_dir = repo_dir
        self.commit_id = commit_id
        self.grep_suppression_commit_level = grep_suppression_commit_level
        self.results_dir = results_dir


    def get_checker_commit_level(self):
        '''
        May contains several different kinds of suppression from different checkers.
        Start from analysis suppression in specified commit, and check which checkers they are related to.
        Return a checker list, each element of the list is a checker's name.
        '''
        with open(self.grep_suppression_commit_level, "r") as f:
            suppression_lines = f.readlines()
        f.close()

        checker_reminder = []
        # Read single suppression line, Return which checker reports the suppression
        for single_suppression_line in suppression_lines:
            if self.language == "python":
                if "# pylint:" in single_suppression_line:
                    if "pylint" not in checker_reminder.__str__():
                        checker_reminder.append("pylint")
                if "# type: ignore" in single_suppression_line:
                    if "mypy" not in checker_reminder.__str__():
                        checker_reminder.append("mypy")
            if checker_reminder.__len__() == 2: # found both 2 target checkers
                break 
        return checker_reminder
    
    
    def run_checker(self, checker_reminder):
        # go to repo_dir to run checkers
        os.chdir(self.repo_dir)
        # print("** working dir: " + os.getcwd())
        '''
        If pylint, may be a warning for future pylint releases.
        Suppress the warning by change the following contents in repoitory's [pylintrc] file
            overgeneral-exceptions=BaseException,
                                Exception
            to
            overgeneral-exceptions=builtins.BaseException,
                                builtins.Exception
        '''
        
        checker_reports = [] # records reports' names, in case of run 2 checkers for 1 file.
        checkers = [] # map to checker_reports
        command_line = ""
        for checker in checker_reminder:
            commit_results_dir = self.results_dir + "commit_results/" + commit_id + "/"
            if not os.path.exists(commit_results_dir):
                os.makedirs(commit_results_dir)
            checker_report = commit_results_dir + commit_id + "_" + checker + ".txt"
            if self.language == "python":
                if checker == "pylint":
                    # option: choose to disable I, R message or not 
                    command_line = "pylint --recursive=y --disable=I,R " + self.repo_dir + " >> " + checker_report
                    '''
                    [I]nformational messages that Pylint emits (do not contribute to your analysis score)
                    [R]efactor for a "good practice" metric violation
                    [C]onvention for coding standard violation
                    [W]arning for stylistic problems, or minor programming issues
                    [E]rror for important programming issues (i.e. most probably bug)
                    [F]atal for errors which prevented further processing
                    here do not consider about I and F.
                    '''
                else: # mypy
                    command_line = "mypy " + self.repo_dir + " >> " + checker_report
            checker_reports.append(checker_report)
            checkers.append(checker)
            subprocess.run(command_line, shell=True)
        return checker_reports, checkers, commit_results_dir
    

    def read_reports(self, checker_reports, checkers): 
        '''
        Read reports, Return a warning list.
        Python: mypy, pylint
        Java:
        JavaScript:
        '''
        
        '''
        python - mypy
        format 1: chia/util/struct_stream_80.py:80: error: Signature of "from_bytes" incompatible with supertype "int"  [override]
                  end with "Found 8 errors in 1 files (checked 1 source file)"
        format 2: Success: no issues found in 1 source file
        '''
        warnings = [] # if not issues related to target file, the return warnings will be empty
        for report, checker in zip(checker_reports, checkers):
            if language == "python":
                if "mypy" == checker:
                    with open(report, "r") as f: 
                        line = f.readline()
                        while line:
                            if " error: " in line:
                                file_path = line.split(":")[0].strip()
                                line_number = line.split(":")[1].strip()
                                # may also get warnings from no-suppression files
                                # get warning code
                                if "[" in line:
                                    warning_type = "[" + line.split("[")[-1].replace("\n", "").strip()
                                else:
                                    warning_type = line.split(":")[-1].strip() 
                               
                                warning_dict = {"file_path" : file_path,
                                            "warning_type" : warning_type,
                                            "line_number" : line_number}
                                warnings.append(warning_dict)
                            line = f.readline()
                        f.close()
            
                '''
                python - pylint
                format 1: no issues found, the report will be empty.
                format 2: chia/daemon/windows_signal_25.py:25:8: E1101: Module 'signal' has no 'SIGBREAK' member (no-member)
                '''
                if "pylint" == checker:
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
                                        warning_type = line.split("(")[-1].replace(")", "").strip() # specific warning type
                                        warning_dict = {"file_path" : file_path,
                                            "warning_type" : warning_type,
                                            "line_number" : line_number}
                                        warnings.append(warning_dict)
                                line = f.readline()
                        f.close()

            return warnings 
    
    
if __name__=="__main__":
    args = parser.parse_args()
    language = args.language
    repo_dir = args.repo_dir
    commit_id = args.commit_id
    grep_suppression_commit_level = args.grep_suppression_commit_level
    results_dir = args.results_dir
    
    init = get_warning_list(language, repo_dir, commit_id, grep_suppression_commit_level, results_dir)
    checker_reminder = init.get_checker_commit_level() # get to know which checker to run
    checker_reports, checkers, commit_results_dir = init.run_checker(checker_reminder)
    warnings = init.read_reports(checker_reports, checkers)

    # write all warnings in the target commit to a csv file.
    with open(join(commit_results_dir, commit_id + "_warnings.csv"), "w") as f:
        write_str = ""
        for single_warning in warnings:
            single_write_str = single_warning['file_path'] + "," + single_warning['warning_type'] + "," + single_warning['line_number']
            write_str = write_str + single_write_str + "\n"
        f.write(write_str)
        f.close()