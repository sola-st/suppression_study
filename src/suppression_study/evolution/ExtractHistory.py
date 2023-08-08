import argparse
import csv
import subprocess
import os
from git.repo import Repo
from os.path import join
import json


from suppression_study.evolution.AnalyzeGitlogReport import AnalyzeGitlogReport
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
    def __init__(self, repo_dir, all_commits, results_dir, log_result_folder, history_json_file):
        self.repo_dir = repo_dir
        self.all_commits = all_commits
        self.results_dir = results_dir
        self.log_result_folder = log_result_folder
        self.history_json_file = history_json_file

    def read_suppression_files(self, specified_commit):
        '''
        Read the latest_suppression, and represent it as a class
        '''
        suppression_csv = join(self.results_dir, "grep", specified_commit + "_suppression.csv")
 
        if not os.path.exists(suppression_csv):
            return 

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
        latest_commit = self.all_commits[0]
        log_result_commit_folder = self.run_gitlog_command(latest_commit)
        if not log_result_commit_folder:
            return

        # Represent git log results to Json files (change histories of suppressions in latest commit)  
        all_change_events_list_latest_commit = AnalyzeGitlogReport(log_result_commit_folder).get_commit_block()
        # write to a file for check at the first stage, may removed later
        if all_change_events_list_latest_commit:
            with open(self.history_json_file, "w", newline="\n") as ds:
                json.dump(all_change_events_list_latest_commit, ds, indent=4, ensure_ascii=False)

        return all_change_events_list_latest_commit
        
    def run_gitlog_command(self, current_commit):
        repo_base= Repo(self.repo_dir)
        repo_base.git.checkout(current_commit)

        latest_suppression = self.read_suppression_files(current_commit)
        if not latest_suppression:
            return
        
        for suppression in latest_suppression:
            line_range_start = suppression.line_number
            line_range_end = line_range_start + 1
            line_range_start_str = str(line_range_start)
            line_range_end_str =str(line_range_end)

            current_file = suppression.file_path
            current_file_name = current_file.split("/")[-1].strip()
            current_file_name_base = current_file_name.split(".")[0]
            # Get log_result_file_name
            # eg,. with a python file, a.py, line 10, the corresponding log_result_file_name is a_10.txt
            log_result_file_name = current_file_name_base + "_" + line_range_start_str + ".txt"
            
            # Get the parent folder of log_result_file_name, which is log_result_commit_folder
            log_result_commit_folder = join(self.log_result_folder, current_commit)
            if not os.path.exists(log_result_commit_folder):
                os.makedirs(log_result_commit_folder)

            log_result = join(log_result_commit_folder, log_result_file_name)

            if os.path.exists(log_result): # Avoid duplicated source file names and line numbers
                current_file_parent_folder = "root"
                try:
                    current_file_parent_folder = current_file.split("/")[-2].strip()
                except:
                    pass
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
       
        return log_result_commit_folder


    def track_back_history_commits(self, all_change_events_accumulator):
        # all_change_events_accumulator comes from all_change_events_list_latest_commit
        # Use it as a accumulator to get all histories (all commits)
        all_commits_num = len(self.all_commits)
        for i in range(1, all_commits_num): # Except the latest commit
            commit = self.all_commits[i]
            log_result_commit_folder = self.run_gitlog_command(commit)
            if log_result_commit_folder:
                all_change_events_list_history_commit = AnalyzeGitlogReport(log_result_commit_folder).get_commit_block()
                if all_change_events_list_history_commit:
                    with open(self.history_json_file.replace(".json", "_" + commit + ".txt"), "w", newline="\n") as ds:
                        json.dump(all_change_events_list_history_commit, ds, indent=4, ensure_ascii=False)
                '''
                The format of all_change_events_list_history_commit:

                [ ---- commit level: the element is a suppression level dict [suppression ID : change event(s)]
                    {
                        "# S0": [ ---- suppression level: the element is a change event
                            {
                                "commit_id": "xxxx",
                                "date": "xxx",
                                "file_path": "xxx.py",
                                "warning_type": "# pylint: disable=missing-module-docstring",
                                "line_number": 1,
                                "change_operation": "add"
                            },
                            {...}
                        ]
                    },
                    {
                        "# S1": [...]
                    }
                    ...
                ]
                '''
                # key_continuous_int: the last number in key from history sequence
                key_continuous_int = 0
                if all_change_events_accumulator:
                    # Only one key in .key(), as a suppression has one suppression ID.
                    dict_keys_to_list = list(all_change_events_accumulator[-1].keys())
                    key_continuous_int = int(dict_keys_to_list[0].replace("# S", ""))
                
                for suppression_level_dict in all_change_events_list_history_commit:
                    old_key = list(suppression_level_dict.keys())[0]
                    change_events_suppression_level = suppression_level_dict[old_key]
                    for single_change_event in change_events_suppression_level:
                        if str(single_change_event) not in str(all_change_events_accumulator):
                            key_continuous_int += 1
                            updated_key = "# S" + str(key_continuous_int)
                            updated_suppression_level_dict = {updated_key : change_events_suppression_level}
                            all_change_events_accumulator.append(updated_suppression_level_dict)
                        break # If a single change event is new, all the change events for the same suppression will be new
        
        with open(self.history_json_file.replace(".json", "_all.json"), "w", newline="\n") as ds:
            json.dump(all_change_events_accumulator, ds, indent=4, ensure_ascii=False)

def main(repo_dir, commit_id, results_dir):
    # Get commit list and suppression for all the commits.
    if not os.path.exists(commit_id):
        FunctionsCommon.get_commit_csv(repo_dir, commit_id)
    all_commits = FunctionsCommon.get_commit_list(commit_id)

    # Get suppression
    if not os.path.exists(join(results_dir, "grep")):
        subprocess.run(["python", "-m", "suppression_study.suppression.GrepSuppressionPython",
        "--repo_dir=" + repo_dir,
        "--commit_id=" + commit_id,
        "--results_dir=" + results_dir])

    # Create a folder for storing 'git log' results
    log_result_folder = join(results_dir, "gitlog_history")
    if not os.path.exists(log_result_folder):
        os.makedirs(log_result_folder)
    
    # Specify a Json file path to store all change events at suppression level
    history_json_file = join(log_result_folder, "histories_suppression_level.json")

    # Get git log results for all the suppression in latest commit. results in log_result_folder
    init = ExtractHistory(repo_dir, all_commits, results_dir, log_result_folder, history_json_file)
    all_change_events_list_latest_commit = init.get_gitlog_results_latest_commit()

    # Check history commits and suppression to extract histories of all suppressions.
    init.track_back_history_commits(all_change_events_list_latest_commit)

    
if __name__=="__main__":
    args = parser.parse_args()
    main(args.repo_dir, args.commit_id, args.results_dir)

    print("Done.")