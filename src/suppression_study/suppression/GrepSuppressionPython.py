'''
Get suppression for Python, both Mypy and Pylint.
'''

import argparse
from suppression_study.suppression.GrepSuppressionSuper import GrepSuppressionSuper
from suppression_study.suppression.FormatSuppressionCommon import FormatSuppressionCommon
import os


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
        ''' 
        output_txt_files : list = super(GrepSuppressionPython, self).grep_suppression_for_all_commits()
        for raw_suppression_results in output_txt_files:
            if os.path.getsize(raw_suppression_results):
                format_to_csv(raw_suppression_results)
            else:
                os.remove(raw_suppression_results)


def format_to_csv(raw_suppression_results): 
    comment_symbol = "#" 
    preprocessed_suppression_csv = raw_suppression_results.replace(".txt", "_suppression.csv")
    FormatSuppressionCommon(comment_symbol, raw_suppression_results, preprocessed_suppression_csv).format_suppression_common()

        
if __name__=="__main__":
    args = parser.parse_args()
    repo_dir = args.repo_dir
    commit_id = args.commit_id
    results_dir = args.results_dir

    output_path = os.path.join(results_dir, "grep")

    init = GrepSuppressionPython(repo_dir, commit_id, output_path)

    if os.path.exists(commit_id): # It's a file
        init.grep_suppression_for_all_commits()  
    else:
        init.grep_suppression_for_specific_commit()
