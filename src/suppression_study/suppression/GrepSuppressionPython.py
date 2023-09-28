'''
Get suppression for Python, both Mypy and Pylint.
'''

import argparse
from suppression_study.suppression.GrepSuppressionSuper import GrepSuppressionSuper
from suppression_study.suppression.FormatSuppressionCommon import FormatSuppressionCommon
import os
from os.path import join


parser = argparse.ArgumentParser(description="Find suppression in Python repositories")
parser.add_argument("--repo_dir", help="Directory with the repository to check", required=True)
parser.add_argument("--commit_id", help="A specific commit ID, or the .csv file which stores a list of commit IDs", required=True)
parser.add_argument("--results_dir", help="Directory where to put the results", required=True)

class GrepSuppressionPython(GrepSuppressionSuper):

    def __init__(self, repo_dir, commit_id, output_path, checker=None):
        if checker == None:
            super().__init__("*.py", "# pylint: *disable|# type: ignore")
        elif checker == "pylint":
            super().__init__("*.py", "# pylint: *disable")
        elif checker == "mypy":
            super().__init__("*.py", "# type: ignore")
        else:
            raise ValueError("Checker must be 'pylint', 'mypy', or None")
        self.repo_dir = repo_dir
        self.commit_id = commit_id
        self.output_path = output_path

    def grep_suppression_for_specific_commit(self):
        '''
        Run "Grep" command to find suppression in specified commit, return a .txt file 
        ''' 
        raw_suppression_results = super(GrepSuppressionPython, self).grep_suppression_for_specific_commit()
        if os.path.getsize(raw_suppression_results):
            format_to_csv(raw_suppression_results)
        else:
            os.remove(raw_suppression_results)

    def grep_suppression_for_all_commits(self):
        '''
        Run "Grep" command to find suppression in all the commits (multi-commit)
        Return .txt files, 1 commit --> 1 .txt 
        Also write a file that records how many suppression are there in these commits
        ''' 
        suppression_num = 0
        all_suppression_nums = []
        # The output_txt_files are well mapped with the given all commits
        output_txt_files : list = super(GrepSuppressionPython, self).grep_suppression_for_all_commits()
        for raw_suppression_results in output_txt_files:
            if os.path.getsize(raw_suppression_results):
                format_to_csv(raw_suppression_results)
                preprocessed_suppression_csv = raw_suppression_results.replace(".txt", "_suppression.csv")
                suppression_num = len(open(preprocessed_suppression_csv, "r").readlines())
            else:
                os.remove(raw_suppression_results)
                suppression_num = 0
            all_suppression_nums.append(suppression_num)

        data_to_write = ""
        commit_max_index = len(all_suppression_nums) + 1 # set to start from 1
        all_suppression_nums.reverse() # let it start from older commits
        for i, suppression_num in zip(range(1, commit_max_index), all_suppression_nums):
            data_to_write = f"{data_to_write}{i},{suppression_num}\n"
        suppression_num_csv = join(os.path.dirname(self.output_path), "all_suppression_nums.csv")
        with open(suppression_num_csv, "w") as f:
            f.writelines(data_to_write)

def format_to_csv(raw_suppression_results): 
    comment_symbol = "#" 
    preprocessed_suppression_csv = raw_suppression_results.replace(".txt", "_suppression.csv")
    FormatSuppressionCommon(comment_symbol, raw_suppression_results, preprocessed_suppression_csv).format_suppression_common()

        
if __name__=="__main__":
    args = parser.parse_args()
    repo_dir = args.repo_dir
    commit_id = args.commit_id
    results_dir = args.results_dir

    output_path = join(results_dir, "grep")

    init = GrepSuppressionPython(repo_dir, commit_id, output_path)

    if os.path.exists(commit_id): # It's a file
        init.grep_suppression_for_all_commits()  
    else:
        init.grep_suppression_for_specific_commit()
