'''
Common functions for getting warnings from running checkers.
'''

import subprocess
from git.repo import Repo
import os

class GetWarningsSuper():

    def run_checker(self, checker, command_line):
        '''
        Run the specified checker, Return a report file
        Here also return the commit_results_dir which is a subfolder of results_dir

        Use the same output folder architecture for all the checkers and repositories,
        Only different in checkers and command_line 
        '''
        target_repo = Repo(self.repo_dir)
        target_repo.git.checkout(self.commit_id)
        os.chdir(self.repo_dir) # go to repo_dir to run checkers
        
        commit_results_dir = self.results_dir + "checker_results/" + self.commit_id + "/"
        if not os.path.exists(commit_results_dir):
            os.makedirs(commit_results_dir)
        report = commit_results_dir + self.commit_id + "_" + checker + ".txt"
        
        result = subprocess.run(command_line, shell=True, stdout=subprocess.PIPE, universal_newlines=True)
        output_txt = result.stdout
        with open(report, "w") as f:
            f.writelines(output_txt)
        f.close()

        return report, commit_results_dir

    def write_warning_list(self, warnings, commit_results_dir):
        '''
        Write all reported warnings to a .csv file.
        '''
        with open(os.path.join(commit_results_dir, self.commit_id + "_warnings.csv"), "w") as f:
            write_str = ""
            for single_warning in warnings:
                single_write_str = single_warning['file_path'] + "," + single_warning['warning_type'] + "," + single_warning['line_number']
                write_str = write_str + single_write_str + "\n"
            f.write(write_str)
        f.close()