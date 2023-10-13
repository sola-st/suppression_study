import argparse
from suppression_study.checkers.GetWarningsSuper import GetWarningsSuper
from suppression_study.warnings.Warning import Warning
import os


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

        Option: choose to disable a specific message category or not 
        [I]nformational messages that Pylint emits (do not contribute to your analysis score)
        [R]efactor for a "good practice" metric violation
        [C]onvention for coding standard violation
        [W]arning for stylistic problems, or minor programming issues
        [E]rror for important programming issues (i.e. most probably bug)
        [F]atal for errors which prevented further processing
        here do not consider I.
        '''
        checker = "pylint"
        command_line = "pylint --recursive=y --disable=I ./"
        report, commit_results_dir = super(GetPylintWarnings, self).run_checker(checker, command_line)

        return report, commit_results_dir

    def read_reports(self, report):
        '''
        Read reports, Return a warning list.
        Pylint report format: [all C, W, E, F, and part of R]
            eg,. folder1/bar.py:1:0: C0104: Disallowed name "bar" (disallowed-name)

        [R]efactor categories:
        Format 1] tests/unit/daemon.py:6:0: R0402: Use 'from xx import ff' instead (consider-using-from-import)
                  tests/unit/daemon.py:15:0: R0401: Cyclic import (xx.remote.base -> xx.remote.local) (cyclic-import)
        Format 2] test.py:1:0: R0801: Similar lines in 2 files
                    ==xx.remote.gs:[166:180]
                    ==xx.remote.s3:[212:226]
                                    continue

                                if to_info['scheme'] != 'local':
                                    raise NotImplementedError

                                msg = "Downloading '{}/{}' to '{}'".format(from_info['bucket'],
                                                                        from_info['path'],
                                                                        to_info['path'])
                                logger.debug(msg)

                                tmp_file = self.tmp_file(to_info['path'])
                                if not name:
                                    name = os.path.basename(to_info['path'])
                    (duplicate-code)
        '''
        warnings = [] 
        message_types = ("R", "C", "W", "E", "F")
        r_format_2 = False # if a warning_type is R
        r_file_path = "" # to temporally store the file_path of a R type message
        r_line_number = ""

        with open(report, "r") as f:
            lines = f.readlines()
        all_line_num = len(lines)
        for line, line_index in zip(lines, range(all_line_num)):
            if line.count(":") > 3:  # in general, with 4 ":".
                contents = line.split(":")
                warning_code = contents[3].strip()
                if warning_code.startswith(message_types):
                    # exactly the line show warning messages, not source code
                    if r_format_2 == True:
                        # finish the previous warning_type extraction
                        r_warning_type = lines[line_index-1].split("(")[-1].replace(")", "").strip()
                        assert r_warning_type != ""
                        warning_object = Warning(r_file_path, r_warning_type, r_line_number)
                        warnings.append(warning_object)
                        r_format_2 = False

                    file_path = contents[0].strip()
                    line_number = int(contents[1].strip())
                    # specific warning type
                    warning_type = line.split("(")[-1].replace(")", "").strip()
                    # special process for R format 2
                    if warning_code.startswith("R") and warning_type == line.strip():
                        r_format_2 = True
                        # keep extracted file_path and line_number
                        r_file_path = file_path
                        r_line_number = line_number
                    else:
                        assert warning_type != ""
                        warning_object = Warning(file_path, warning_type, line_number)
                        warnings.append(warning_object)
            elif r_format_2 == True and line_index == all_line_num - 1:
                # last line of this report, and still a R massage haven't get its warning type.
                '''
                End of Pylint report:
                    [last message] util.py:1:0: R0401: Cyclic import xxx (cyclic-import)
                    [empty line]
                    -----------------------------------
                    Your code has been rated at 7.22/10
                to get the last message line, current line_index - 3
                '''
                r_warning_type = lines[line_index-1].split("(")[-1].replace(")", "").strip()
                assert r_warning_type != ""
                warning_object = Warning(r_file_path, r_warning_type, r_line_number)
                warnings.append(warning_object)
        return warnings
    
    def write_warning_list(self, warnings, commit_results_dir):
        '''
        Write all reported warnings to a csv file.
        '''
        super(GetPylintWarnings, self).write_warning_list(warnings, commit_results_dir)


def main(repo_dir, commit_id, results_dir):
    init = GetPylintWarnings(repo_dir, commit_id, results_dir)
    report, commit_results_dir = init.run_checker()
    if os.path.getsize(report):
        warnings = init.read_reports(report)
        init.write_warning_list(warnings, commit_results_dir)

if __name__=="__main__":
    args = parser.parse_args()
    main(args.repo_dir, args.commit_id, args.results_dir)   