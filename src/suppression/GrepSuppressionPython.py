'''
Get suppression for Python, both Mypy and Pylint.
'''

import argparse
from src.suppression.GrepSuppressionSuper import GrepSuppressionSuper
from src.suppression.FormatSuppressionCommon import FormatSuppressionCommon
import os


parser = argparse.ArgumentParser(description="Find suppression in Python repositories")
parser.add_argument("--repo_dir", help="Directory with the repository to check", required=True)
parser.add_argument("--commit_id", help="A specific commit ID, or the .csv file which stores a list of commit IDs", required=True)
parser.add_argument("--results_dir", help="Directory where to put the results, endswith '/'", required=True)


class GrepSuppressionPython(GrepSuppressionSuper):

    def __init__(self, repo_name, repo_dir, commit_id, level_mark, output_path, source_file_extension, filter_keywords):
        self.repo_name = repo_name
        self.repo_dir = repo_dir
        self.commit_id = commit_id
        self.level_mark = level_mark
        self.output_path = output_path
        self.source_file_extension = source_file_extension
        self.filter_keywords = filter_keywords

    def grep_suppression_for_specific_commit(self):
        '''
        Run "Grep" command to find suppression in specified commit, return a .txt file 
        ''' 
        raw_suppression_results= super(GrepSuppressionPython, self).grep_suppression_for_specific_commit()
        self.format_to_csv(raw_suppression_results)

    def grep_suppression_for_all_commits(self):
        '''
        Run "Grep" command to find suppression in all the commits (multi-commit)
        Return .txt files, 1 commit --> 1 .txt 
        ''' 
        output_txt_files = super(GrepSuppressionPython, self).grep_suppression_for_all_commits()
        for raw_suppression_results in output_txt_files:
            if os.path.getsize(raw_suppression_results):
                self.format_to_csv(raw_suppression_results)


    def format_to_csv(self, raw_suppression_results): 
        comment_symbol = "#" 
        precessed_suppression_csv = raw_suppression_results.replace(".txt", "_suppression.csv")
        FormatSuppressionCommon(comment_symbol, raw_suppression_results, precessed_suppression_csv).format_suppression_common()

        
if __name__=="__main__":
    args = parser.parse_args()
    repo_dir = args.repo_dir
    commit_id = args.commit_id
    results_dir = args.results_dir

    repo_name = repo_dir.split("/")[-2].strip()
    level_mark = "folder"
    output_path = results_dir + repo_name + "/grep/" 
    source_file_extension = "\"*.py\""
    filter_keywords="\#\ pylint:\|\#\ type:\ ignore"

    init = GrepSuppressionPython(repo_name, repo_dir, commit_id, level_mark, output_path, source_file_extension, filter_keywords)

    try:
        if (type(commit_id), str):
            init.grep_suppression_for_specific_commit()
    except:
        init.grep_suppression_for_all_commits()

    