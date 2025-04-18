'''
Common functions for getting warnings from running checkers.
'''

import csv
import subprocess
from git.repo import Repo
import os
from os.path import join
from suppression_study.utils.GitRepoUtils import get_current_commit


class GetWarningsSuper():

    def run_checker(self, checker, command_line, file_specific=None):
        '''
        Run the specified checker, Return a report file
        Here also return the commit_results_dir which is a subfolder of results_dir

        Use the same output folder architecture for all the checkers and repositories,
        Only different in checkers and command_line 
        '''
        # checkout the target commit, but only if we're not yet at this commit anyway
        # (the check is needed because we may otherwise overwrite local changes,
        # e.g., made by SuppressionRemover)
        current_commit_id = get_current_commit(self.repo_dir)
        if self.commit_id != current_commit_id:
            target_repo = Repo(self.repo_dir)
            target_repo.git.checkout(self.commit_id, force=True)

        # used to store checker results and extracted warning csv file
        commit_results_dir = join(self.results_dir, "checker_results", checker)
        if not os.path.exists(commit_results_dir):
            os.makedirs(commit_results_dir)
        if file_specific:
            report = join(commit_results_dir, f"{self.commit_id}_report_{file_specific}.txt")
        else:
            report = join(commit_results_dir, f"{self.commit_id}_report.txt")
        
        result = subprocess.run(command_line, cwd=self.repo_dir, shell=True, stdout=subprocess.PIPE, universal_newlines=True)
        output_txt = result.stdout
        with open(report, "w") as f:
            f.writelines(output_txt)

        return report, commit_results_dir

    def write_warning_list(self, warnings, commit_results_dir):
        '''
        Write all reported warnings to a .csv file.
        '''
        with open(join(commit_results_dir, self.commit_id + "_warnings.csv"), "w") as csvfile:
            csv_writer = csv.writer(csvfile)
            for single_warning in warnings:
                csv_writer.writerow([single_warning.path, single_warning.kind, single_warning.line])