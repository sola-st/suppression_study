import argparse
import csv
import subprocess
import os
from git.repo import Repo
from os.path import join
import json
import datetime

from suppression_study.utils.SuppressionInfo import SuppressionInfo
from suppression_study.utils.FunctionsCommon import FunctionsCommon


parser = argparse.ArgumentParser(description="Extract change histories of all suppressions at the repository level")
parser.add_argument("--repo_dir", help="Directory with the repository to check", required=True)
parser.add_argument("--commit_id", help=".csv file which stores a list of commit IDs", required=True)
parser.add_argument("--results_dir", help="Directory where to put the results", required=True)


class ExtractHistory(): 
    '''
    By receiving a repository and a commit list, 
    run "git blame" command to check histories related to suppressions, 
    return a JSON file with suppression level change events.
    '''
    def __init__(self, repo_dir, all_commits_list, all_dates_list, results_dir, blame_result_folder, history_json_file):
        self.repo_dir = repo_dir
        self.all_commits_list = all_commits_list
        self.all_dates_list = all_dates_list
        self.results_dir = results_dir
        self.blame_result_folder = blame_result_folder
        self.history_json_file = history_json_file

        change_events_accumulator_repository_level = []
        self.change_events_accumulator_repository_level = change_events_accumulator_repository_level

    def read_suppression_files(self, specified_commit):
        '''
        Read the all_suppression_commit_level, and represent it as a class
        '''
        suppressor_set = ["# pylint:", "# type:"]
        # Update later
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
    
    # def get_gitblame_results_oldest_commit(self):
    #     '''
    #     Run "git blame" command to track histories based on all oldest suppression, 
    #     Return a blame_result file for each suppression. --> to blame_result_folder
    #     '''
    #     oldest_commit = self.all_commits_list[0]
    #     oldest_date = self.all_dates_list[0]

    #     Repo(self.repo_dir) # Make it a repository to run git command
    #     change_events_list_oldest_commit = self.run_gitblame_command(oldest_commit, oldest_date)

    #     if change_events_list_oldest_commit:
    #         with open(self.history_json_file.replace(".json", "_" + oldest_commit + "_oldest.json"), "w", newline="\n") as ds:
    #             json.dump(change_events_list_oldest_commit, ds, indent=4, ensure_ascii=False)
    #         self.change_events_accumulator_repository_level = change_events_list_oldest_commit
        
    def run_gitblame_command(self, current_commit, current_date):
        change_events_commit_level = []
        
        all_suppression_commit_level = self.read_suppression_files(current_commit)
        if not all_suppression_commit_level:
            return # No suppression in current commit
        
        suppression_index = 0 
        for suppression in all_suppression_commit_level:
            suppression_index += 1
            line_range_start = suppression.line_number
            line_range_start_str = str(line_range_start)
            line_range_end_str = line_range_start_str

            current_file = suppression.file_path
            current_file_name = current_file.split("/")[-1].strip() # eg,. 'example.py'
            current_file_name_base = current_file_name.split(".")[0] # eg,. 'example'
            # Additional effort, avoid duplicated source file names, include the parent folder for easier manual checking
            # Get blame_result_file_name
            # eg,. with a python file, src/main/a.py, line 10, suppression_index 5,
            #      the corresponding blame_result_file_name is main_a_5_10.txt
            current_file_parent_folder = "root"
            try:
                current_file_parent_folder = current_file.split("/")[-2].strip()
            except:
                pass
            # To avoid duplicated source file names, set the format of blame_result_file_name as:
            # Format : <parent_folder>_<current_file_name_base>_<suppression_index>_<line_number>
            blame_result_file_name = current_file_parent_folder + "_" + current_file_name_base + "_" \
                    + str(suppression_index) + "_" + line_range_start_str + ".txt"
                        
            # Get the parent folder of blame_result_file_name, which is blame_result_commit_folder
            blame_result_commit_folder = join(self.blame_result_folder, current_commit)
            if not os.path.exists(blame_result_commit_folder):
                os.makedirs(blame_result_commit_folder)

            blame_result = join(blame_result_commit_folder, blame_result_file_name)

            '''
            Format of git blame command:
                git blame --reverse -L<start_line,end_line> file_path commit_id

            1) git blame command is able to cover file rename and suppression line number changes
            2) The result.stdout will always be one line that shows the last commit that the specified line exists.
            3) In the case of the latest commit, don't have to checkout to specified commit.
            
            -L: [line_range_start, line_range_end]  Overlapping ranges are allowed.
            --reverse: result starts from old history/ old commit
            '''
            command_line = "git blame --reverse -L" + line_range_start_str + "," + line_range_end_str + " " + current_file + " " + current_commit
            result = subprocess.run(command_line, cwd=self.repo_dir, shell=True, stdout=subprocess.PIPE, universal_newlines=True)
            blame_output = result.stdout
            # Write for manual checking, may removed later.
            with open(blame_result, "w") as f:
                f.writelines(blame_output) 

            # Represent suppression as a change_event, the start event of it's lifetime
            change_event_lifetime_start = self.represent_to_json_string(current_commit, current_date, suppression.file_path, 
                    suppression.warning_type, suppression.line_number, "add")
            change_event_lifetime_end = self.get_event_which_delete_suppressions(suppression, blame_output)

            if change_event_lifetime_end and (not isinstance(change_event_lifetime_end, bool)):
                change_events_suppression_level = []
                change_events_suppression_level.append(change_event_lifetime_start)
                change_events_suppression_level.append(change_event_lifetime_end)

                if change_events_suppression_level:
                    # Elements in change_events_commit_level mainly has 2 categories:
                    # 1) totally new suppression level change events (add + delete event)
                    # 2) a suppression level change event (only add, in latest commit, no next commit)
                    #       not sure if this add event exists in self.change_events_accumulator_repository_level, furthermore check later.
                    change_events_commit_level.append(change_events_suppression_level)
                    
        return change_events_commit_level
    
    def get_event_which_delete_suppressions(self, suppression, blame_output):
        '''
        Examples of blame_output:
        1) With file rename: 15c87719 folder1/bar.py (Author 2023-07-04 11:11:16 +0200 2) x = 42
        1) Without file rename: 58fg4he5 (Author 2023-07-04 11:11:16 +0200 2) x = 42
        '''
        delete_suppression_commit = ""
        delete_suppression_date = ""
        renamed_file_path = ""
        change_event_lifetime_end = ""

        tmp = blame_output.split(" ")
        last_exist_commit_tmp = tmp[0].strip()
        
        if "^" in last_exist_commit_tmp:
            specified_line_contents = blame_output.split(")", 1)[0]
            if suppression.waning_type not in specified_line_contents: # Suppression was changed
                # check suppression change to another type or the whole suppression removed.
                print() # Update later

        last_exist_commit = last_exist_commit_tmp.replace("^", "")
        last_exist_commit_index = self.all_commits_list.index(last_exist_commit)

        delete_suppression_index = last_exist_commit_index + 1
        all_commits_list_len = len(self.all_commits_list)
        if delete_suppression_index < all_commits_list_len:
            delete_suppression_commit = self.all_commits_list[delete_suppression_index]
            delete_suppression_date = self.all_dates_list[delete_suppression_index]
        else: # No next commit, which means the last_exist_commit here is latest and the suppression is never removed
            return

        potential_renamed_file_path = tmp[1].strip()
        if not potential_renamed_file_path.startswith("("): 
            renamed_file_path = potential_renamed_file_path

        if renamed_file_path:
            change_event_lifetime_end = self.represent_to_json_string(delete_suppression_commit, delete_suppression_date, renamed_file_path, 
                        suppression.warning_type, "unknown", "delete")
        else:
            change_event_lifetime_end = self.represent_to_json_string(delete_suppression_commit, delete_suppression_date, suppression.file_path, 
                        suppression.warning_type, "unknown", "delete")
            
        # Check if it's a already recorded suppression
        if str(change_event_lifetime_end) in str(self.change_events_accumulator_repository_level):
            # Current suppression is already recorded in self.change_events_accumulator_repository_level
            already_exists = True
            return already_exists
            
        return change_event_lifetime_end

    def represent_to_json_string(self, commit_id, date, file_path, warning_type, line_number, operation):
        change_event = {
            "commit_id" : commit_id,
            "date" : date,
            "file_path" : file_path,
            "warning_type" : warning_type,
            "line_number" : line_number,
            "change_operation" : operation,
        }
        return change_event

    def get_gitblame_commits_forward(self):
        # change_events_accumulator_repository_level comes from change_events_list_oldest_commit
        # Use it as a accumulator to get all histories (all commits)
        commit_1st_has_suppression = True
        all_commits_list_len = len(self.all_commits_list)
        for i in range(0, all_commits_list_len): # Except the latest commit
            commit = self.all_commits_list[i]
            date = self.all_dates_list[i]
            change_events_commit_level = self.run_gitblame_command(commit, date)
            if change_events_commit_level:
                # Write for manual checking, may removed later.
                if commit_1st_has_suppression:
                    with open(self.history_json_file.replace(".json", "_" + commit + "_1st.json"), "w", newline="\n") as ds:
                        json.dump(change_events_commit_level, ds, indent=4, ensure_ascii=False)
                    commit_1st_has_suppression = False
                else:
                    with open(self.history_json_file.replace(".json", "_" + commit + ".json"), "w", newline="\n") as ds:
                        json.dump(change_events_commit_level, ds, indent=4, ensure_ascii=False)
                
                for change_events_suppression_level in change_events_commit_level:
                    change_events_num_suppression_level = len(change_events_suppression_level)
                    if change_events_num_suppression_level == 1:
                        # need to check if it is a already recorded one
                        print() # git log?
                    elif change_events_num_suppression_level == 2:
                        self.change_events_accumulator_repository_level.append(change_events_suppression_level)

        history_repository_level = []
        suppression_index = 0
        for events_suppression_level in self.change_events_accumulator_repository_level:
            history_suppression_level = {"# S" + suppression_index : events_suppression_level}
            history_repository_level.append(history_suppression_level)
            suppression_index =+ 1
        
        with open(self.history_json_file.replace(".json", "_all.json"), "w", newline="\n") as ds:
            json.dump(history_repository_level, ds, indent=4, ensure_ascii=False)
    

def main(repo_dir, commit_id, results_dir):
    # Get commit list and suppression for all the commits.
    if not os.path.exists(commit_id):
        FunctionsCommon.get_commit_csv(repo_dir, commit_id)
    all_commits_list, all_dates_list = FunctionsCommon.get_commit_date_lists(commit_id)

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

    # Create a folder for storing 'git blame' results
    blame_result_folder = join(results_dir, "gitblame_history")
    if not os.path.exists(blame_result_folder):
        os.makedirs(blame_result_folder)
    
    # Specify a Json file path to store all change events at suppression level
    history_json_file = join(blame_result_folder, "histories_suppression_level.json")

    # Get git blame results for all the suppression in latest commit. results in blame_result_folder
    init = ExtractHistory(repo_dir, all_commits_list, all_dates_list, results_dir, blame_result_folder, history_json_file)
    # init.get_gitblame_results_oldest_commit()
    # Check history commits and suppression to extract histories of all suppressions.
    init.get_gitblame_commits_forward()

    
if __name__=="__main__":
    args = parser.parse_args()
    print("Running...")
    start_time = datetime.datetime.now()
    main(args.repo_dir, args.commit_id, args.results_dir)
    end_time = datetime.datetime.now()
    executing_time = (end_time - start_time).seconds
    print("Executing time:", executing_time, "seconds")
    print("Done.")
