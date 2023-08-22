import argparse
import csv
import subprocess
import os
from git.repo import Repo
from os.path import join
import json
import datetime


from suppression_study.evolution.AnalyzeGitlogReport import AnalyzeGitlogReport
from suppression_study.utils.SuppressionInfo import SuppressionInfo
from suppression_study.utils.FunctionsCommon import FunctionsCommon


parser = argparse.ArgumentParser(description="Extract change histories of all suppressions at the repository level")
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

        all_change_events_accumulator = []
        self.all_change_events_accumulator = all_change_events_accumulator

    def read_suppression_files(self, specified_commit):
        '''
        Read the all_suppression_commit_level, and represent it as a class
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
        
    def run_gitlog_command(self, current_commit):
        repo_base= Repo(self.repo_dir)
        repo_base.git.checkout(current_commit)
        
        all_suppression_commit_level = self.read_suppression_files(current_commit)
        if not all_suppression_commit_level:
            return
        
        suppression_index = 0 
        for suppression in all_suppression_commit_level:
            suppression_index += 1
            line_range_start = suppression.line_number
            line_range_end = line_range_start + 1
            line_range_start_str = str(line_range_start)
            line_range_end_str =str(line_range_end)

            current_file = suppression.file_path
            current_file_name = current_file.split("/")[-1].strip() # eg,. 'example.py'
            current_file_name_base = current_file_name.split(".")[0] # eg,. 'example'
            # Additional effort, avoid duplicated source file names, include the parent folder for easier manual checking
            # Get log_result_file_name
            # eg,. with a python file, src/main/a.py, line 10, suppression_index 5,
            #      the corresponding log_result_file_name is main_a_5_10.txt
            current_file_parent_folder = "root"
            try:
                current_file_parent_folder = current_file.split("/")[-2].strip()
            except:
                pass
            # To avoid duplicated source file names, set the format of log_result_file_name as:
            # Format : <parent_folder>_<current_file_name_base>_<suppression_index>_<line_number>
            log_result_file_name = current_file_parent_folder + "_" + current_file_name_base + "_" \
                    + str(suppression_index) + "_" + line_range_start_str + ".txt"
                        
            # Get the parent folder of log_result_file_name, which is log_result_commit_folder
            log_result_commit_folder = join(self.log_result_folder, current_commit)
            if not os.path.exists(log_result_commit_folder):
                os.makedirs(log_result_commit_folder)

            log_result = join(log_result_commit_folder, log_result_file_name)

            '''
            Format 
            1) git log command cannot find file delete cases.
               It extracts the histories from when the file was added, re-added is a new start.
            2) The result.stdout will not be empty.
                eg,. Assume that there is a repository, suppression only exists in latest commit, 
                     the result.stdout will show the changes in latest commit.

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

    def track_commits_backward(self):
        # Use self.all_change_events_accumulator as a accumulator to get all histories (all commits)
        all_commits_num = len(self.all_commits)
        for i in range(0, all_commits_num): # Start from latest commit
            commit = self.all_commits[i]
            log_result_commit_folder = self.run_gitlog_command(commit)
            if log_result_commit_folder:
                all_change_events_list_commit_level = AnalyzeGitlogReport(log_result_commit_folder).get_commit_block()
                if all_change_events_list_commit_level:
                    # Write for manual checking, may remove later
                    with open(self.history_json_file.replace(".json", "_" + commit + ".json"), "w", newline="\n") as ds:
                        json.dump(all_change_events_list_commit_level, ds, indent=4, ensure_ascii=False)
                    '''
                    The format of all_change_events_list_commit_level:

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
                    key_continuous_int = -1
                    check_exists = -1
                    if self.all_change_events_accumulator:
                        # Only one key in .key(), as a suppression has one suppression ID.
                        dict_keys_to_list = list(self.all_change_events_accumulator[-1].keys())
                        key_continuous_int = int(dict_keys_to_list[0].replace("# S", ""))

                        try:
                            check_exists = self.all_change_events_accumulator.index(change_events_suppression_level)
                        except:
                            pass
                    
                    for suppression_level_dict in all_change_events_list_commit_level:
                        old_key = list(suppression_level_dict.keys())[0]
                        change_events_suppression_level = suppression_level_dict[old_key]
                        
                        if check_exists == -1: # New events
                            for single_change_event in change_events_suppression_level:
                                # Totally new events
                                if str(single_change_event) not in str(self.all_change_events_accumulator):
                                    key_continuous_int += 1
                                    updated_key = "# S" + str(key_continuous_int)
                                    updated_suppression_level_dict = {updated_key : change_events_suppression_level}
                                    self.all_change_events_accumulator.append(updated_suppression_level_dict)
                                    break
                                else:
                                    for suppression_level_events in self.all_change_events_accumulator:
                                        get_key = ""
                                        if str(single_change_event) in str(suppression_level_events) \
                                                and len(change_events_suppression_level) < len(suppression_level_events):
                                            # Part new events, should update to new version
                                            for key, value in self.all_change_events_accumulator[0].items():
                                                if value == suppression_level_events:
                                                    get_key = key
                                                self.all_change_events_accumulator[0][get_key] = change_events_suppression_level
                                                break 
                                            
        with open(self.history_json_file.replace(".json", "_all.json"), "w", newline="\n") as ds:
            json.dump(self.all_change_events_accumulator, ds, indent=4, ensure_ascii=False)

def main(repo_dir, commit_id, results_dir):
    # Get commit list and suppression for all the commits.
    if not os.path.exists(commit_id):
        FunctionsCommon.get_commit_csv(repo_dir, commit_id)
    all_commits = FunctionsCommon.get_commit_list(commit_id)

    # Get suppression
    suppression_result = join(results_dir, "grep")
    if not os.path.exists(suppression_result):
        subprocess.run(["python", "-m", "suppression_study.suppression.GrepSuppressionPython",
        "--repo_dir=" + repo_dir,
        "--commit_id=" + commit_id,
        "--results_dir=" + results_dir])

    if not os.listdir(suppression_result):
        os.rmdir(suppression_result)
        print("No suppression found by running GrepSuppressionPython.")
        return

    # Create a folder for storing 'git log' results
    log_result_folder = join(results_dir, "gitlog_history")
    if not os.path.exists(log_result_folder):
        os.makedirs(log_result_folder)
    
    # Specify a Json file path to store all change events at suppression level
    history_json_file = join(log_result_folder, "histories_suppression_level.json")

    # Get git log results for all the suppression in latest commit. results in log_result_folder
    init = ExtractHistory(repo_dir, all_commits, results_dir, log_result_folder, history_json_file)

    # Check commits and suppression to extract histories of all suppressions.
    init.track_commits_backward()

    
if __name__=="__main__":
    args = parser.parse_args()
    print("Running...")
    start_time = datetime.datetime.now()
    main(args.repo_dir, args.commit_id, args.results_dir)
    end_time = datetime.datetime.now()
    executing_time = (end_time - start_time).seconds
    print("Executing time:", executing_time, "seconds")
    print("Done.")
