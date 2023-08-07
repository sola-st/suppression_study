import argparse
import csv
import subprocess
import os
from git.repo import Repo
from os.path import join


from suppression_study.evolution.AnalyzeGitlogReport import FormatGitlogReport
from suppression_study.utils.SuppressionInfo import SuppressionInfo
from suppression_study.utils.FunctionsCommon import FunctionsCommon


parser = argparse.ArgumentParser(description="Extract change histories of all suppression at the repository level")
parser.add_argument("--repo_dir", help="Directory with the repository to check", required=True)
parser.add_argument("--commit_id", help=".csv file which stores a list of commit IDs", required=True)
parser.add_argument("--results_dir", help="Directory where to put the results", required=True)


class ExtractHistory(): 
    '''
    By receiving a repository and a commit list, 
    run "git log" command to check histories related to suppressions, 
    return a JSON file with suppression level change events.
    '''
    def __init__(self, repo_dir, all_commits, results_dir):
        self.repo_dir = repo_dir
        self.all_commits = all_commits
        self.results_dir = results_dir

        # suppressor = "# pylint:"
        # suppressor=["# type:", "# pylint:", "# pyre-fixme", "eslint-disable"]
        # self.suppressor = suppressor

    def read_suppression_files(self, specified_commit):
        '''
        Read the latest_suppression, and represent it as a class
        '''
        suppression_csv = join(self.results_dir, "grep", specified_commit + "_suppression.csv")

        suppression_commit_level = []
        with open(suppression_csv, 'r') as csvfile:
            reader = csv.reader(csvfile)
            for column in reader:
                file_path = column[0]
                warning_type = column[1]
                line_number = int(column[2])
                suppression_info = SuppressionInfo(file_path, warning_type, line_number)
                suppression_commit_level.append(suppression_info)
        return suppression_commit_level
    
    def get_gitlog_results_latest_commit(self):
        '''
        Run "git log" command to track histories based on all latest suppression, 
        Return a log_result file for each suppression. --> to log_result_folder
        '''
        log_result_folder = join(self.results_dir, "gitlog_latest_commit")
        if not os.path.exists(log_result_folder):
            os.makedirs(log_result_folder)

        latest_commit = self.all_commits[0]
        repo_base= Repo(self.repo_dir)
        repo_base.git.checkout(latest_commit)

        latest_suppression = self.read_suppression_files(latest_commit)
        for suppression in latest_suppression:
            line_range_start = suppression.line_number
            line_range_end = line_range_start + 1
            line_range_start_str = str(line_range_start)
            line_range_end_str =str(line_range_end)

            current_file = suppression.file_path
            current_file_name = current_file.split("/")[-1].strip()
            log_result_file_name = current_file_name.replace(".py", "_" + line_range_start_str + ".txt")
            
            log_result = join(log_result_folder, log_result_file_name)
            if os.path.exists(log_result): # Avoid duplicated source file names
                current_file_parent_folder = current_file.split("/")[-2].strip()
                log_result.replace(".txt", "_" + current_file_parent_folder + ".txt")
            '''
            1) git log command cannot find file delete cases.
               It extracts the histories from when the file was added, re-added is a new start.
            2) The result.stdout will not be empty.
                eg,. Assume that suppression only exists in latest commit, 
                     result.stdout will show the changes in latest commit.

            -C: cover copied files
            -M: cover renamed files
            -L: [line_range_start, line_range_end)
            --reverse: result starts from old history/ old commit
            '''
            command_line = "git log -C -M -L" + line_range_start_str + "," + line_range_end_str + ":" + current_file + " --reverse"
            result = subprocess.run(command_line, cwd=self.repo_dir, shell=True, stdout=subprocess.PIPE, universal_newlines=True)
            with open(log_result, "w") as f:
                f.writelines(result.stdout) 

        return log_result_folder # For easier to iterate all the log_result files
    
    # Update checking history commits  and suppression later.


def main(repo_dir, commit_id, results_dir):
    # Get commit list and suppression for all the commits.
    if not os.path.exists(commit_id):
        FunctionsCommon.get_commit_csv(repo_dir, commit_id)
    all_commits = FunctionsCommon.get_commit_list(commit_id)
    if not os.path.exists(join(args.results_dir, "grep")):
        subprocess.run(["python", "-m", "suppression_study.suppression.GrepSuppressionPython",
        "--repo_dir=" + repo_dir,
        "--commit_id=" + commit_id,
        "--results_dir=" + results_dir])

    init = ExtractHistory(repo_dir, all_commits, results_dir)
    # Get git log results for all the suppression in latest commit
    log_result_folder = init.get_gitlog_results_latest_commit()
    # Represent git log results to Json files (change histories of suppressions in latest commit)
    # FormatGitlogReport(log_result_folder).main()
    # Check history commits and suppression to extract full histories of all suppressions.
    # ...

    
if __name__=="__main__":
    args = parser.parse_args()
    main(args.repo_dir, args.commit_id, args.results_dir)

    print("Done.")
