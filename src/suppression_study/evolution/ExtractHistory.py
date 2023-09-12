import argparse
import subprocess
import os
from git.repo import Repo
from os.path import join
import datetime


from suppression_study.evolution.AnalyzeGitlogReport import AnalyzeGitlogReport
from suppression_study.evolution.SuppressionHistory import SuppressionHistory
from suppression_study.utils.SuppressionInfo import SuppressionInfo
from suppression_study.utils.FunctionsCommon import write_commit_info_to_csv, get_commit_date_lists


parser = argparse.ArgumentParser(description="Extract change histories of all suppressions at the repository level")
parser.add_argument("--repo_dir", help="Directory with the repository to check", required=True)
parser.add_argument("--commit_id_csv_list", help=".csv file which stores a list of commit IDs", required=True)
parser.add_argument("--results_dir", help="Directory where to put the results", required=True)


class LogResultsInfo():
    # Run git log on a specified line of 'file', get the 'log_results', here map 'log_results' and 'file'
    def __init__(self, log_results, file):
        self.log_results = log_results
        self.file = file


class ExtractHistory(): 
    '''
    By receiving a repository and a commit list, 
    run "git log" command to check histories related to suppressions, 
    return a JSON file with suppression level change events.
    '''
    def __init__(self, repo_dir, all_commits_list, all_dates_list, results_dir, log_result_folder, history_json_file):
        self.repo_dir = repo_dir
        self.all_commits_list = all_commits_list
        self.all_dates_list = all_dates_list
        self.results_dir = results_dir
        self.log_result_folder = log_result_folder
        self.history_json_file = history_json_file
        self.history_accumulator = []
        
    def run_gitlog_command(self, previous_commit, current_commit):
        log_results_info_list = []
        repo_base= Repo(self.repo_dir)
        
        suppression_csv = join(self.results_dir, "grep", current_commit + "_suppression.csv")
        all_suppression_commit_level = SuppressionInfo(current_commit, suppression_csv).read_suppression_files()
        if not all_suppression_commit_level: # No suppression in current commit
            # Return: log_results_info_list, deleted_files, log_result_commit_folder
            # All suppressions in old commit were deleted 
            return log_results_info_list, [], "" 
        
        # Suppression in deleted_files(previous_commit) are deleted
        deleted_files = repo_base.git.diff("--name-only", "--diff-filter=D", previous_commit, current_commit) 
        
        repo_base.git.checkout(current_commit)
        suppression_index = 0 
        for suppression in all_suppression_commit_level:
            suppression_index += 1
            # Line start and end can be the same, eg,. [6,6] means line 6
            line_range_start_end = suppression.line_number 
            line_range_str = str(line_range_start_end)

            current_file = suppression.file_path
            current_file_name = current_file.split("/")[-1].strip() # eg,. 'example.py'
            current_file_name_base = current_file_name.split(".")[0] # eg,. 'example'
            # To avoid duplicated source file names, include the parent folder for easier manual checking
            # set the format of log_result_file_name as:
            # Format : <parent_folder>_<current_file_name_base>_<suppression_index>_<line_number>
            # eg,. with a python file, src/main/a.py, line 10, suppression_index 5,
            #      the corresponding log_result_file_name is "main_a_5_10.txt"
            current_file_parent_folder = "root"
            try:
                current_file_parent_folder = current_file.split("/")[-2].strip()
            except:
                pass
            log_result_file_name = f"{current_file_parent_folder}_{current_file_name_base}_{suppression_index}_{line_range_str}.txt"
                        
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
            -L: [line_range_start, line_range_end]
            --reverse: result starts from old history/ old commit
            '''
            command_line = "git log -C -M -L" + line_range_str + "," + line_range_str + ":" + current_file + " --reverse"
            result = subprocess.run(command_line, cwd=self.repo_dir, shell=True, stdout=subprocess.PIPE, universal_newlines=True)
            with open(log_result, "w") as f:
                f.writelines(result.stdout) 

            log_results_info = LogResultsInfo(log_result, current_file)
            log_results_info_list.append(log_results_info)
       
        return log_results_info_list, deleted_files, log_result_commit_folder

    def track_commits_backward(self):
        # Use self.history_accumulator as a accumulator to get all histories (all commits)   
        '''
        Compare commit_1 and commit_2,
        deleted_files : current commit is commit_2, check which files was deleted
        tracked_deleted_files : current commit is commit_1, connect delete events to corresponding suppressions' histories 
        '''
        extraction_start_time = datetime.datetime.now()

        tracked_deleted_files = [] # Files
        tracked_suppression_deleted_mark = False # Suppressions inside a file
        tracked_delete_commit = ""
        tracked_delete_date = ""
        all_commits_num = len(self.all_commits_list)
        for i in range(0, all_commits_num): # Start from latest commit
            previous_commit = ""
            get_results = ""
            current_commit = self.all_commits_list[i]
            if i+1 < all_commits_num:
                previous_commit = self.all_commits_list[i+1]
                get_results = self.run_gitlog_command(previous_commit, current_commit)

            if (i+1) % 100 == 0: # check running time every 100 commits
                current_running_time = (datetime.datetime.now() - extraction_start_time).seconds
                print(f"Current: commit #{i}, running time since starting extracting histories {current_running_time} s")

            log_results_info_list = []
            deleted_files= [] 
            log_result_commit_folder = ""
            suppression_deleted_mark = False
            if get_results:
                log_results_info_list, deleted_files, log_result_commit_folder = get_results
                if log_result_commit_folder:
                    start_analyze = AnalyzeGitlogReport(log_results_info_list, tracked_deleted_files, tracked_delete_commit, \
                            tracked_delete_date, tracked_suppression_deleted_mark, log_result_commit_folder)
                    all_change_events_list_commit_level = start_analyze.from_gitlog_results_to_change_events()
                    # Add commit level histories to repository level histories.
                    SuppressionHistory(self.history_accumulator, all_change_events_list_commit_level, "").add_unique_history_to_accumulator()
                else:
                    suppression_deleted_mark = True # No suppression in current commit_id

            if deleted_files:
                tracked_deleted_files = deleted_files
            else:
                tracked_deleted_files = []

            if suppression_deleted_mark:
                tracked_suppression_deleted_mark = suppression_deleted_mark # True
            else:
                tracked_suppression_deleted_mark = False
            
            # To avoid these 2 marks make impacts on each other
            if deleted_files or suppression_deleted_mark: 
                tracked_delete_commit = current_commit
                tracked_delete_date = self.all_dates_list[i]  
            elif not (deleted_files and suppression_deleted_mark): # Both false
                tracked_delete_commit = ""
                tracked_delete_date = ""

        # Write repository level histories to a JSON file.
        SuppressionHistory(self.history_accumulator, "", self.history_json_file).write_all_accumulated_histories_to_json()   


def main(repo_dir, commit_id_csv_list, results_dir):
    # Get commit list and suppression for all the commits.
    if not os.path.exists(commit_id_csv_list):
        write_commit_info_to_csv(repo_dir, commit_id_csv_list) # commit_info: commit and date
    all_commits_list, all_dates_list = get_commit_date_lists(commit_id_csv_list)

    # Get suppression
    suppression_result = join(results_dir, "grep")
    if not os.path.exists(suppression_result):
        subprocess.run(["python", "-m", "suppression_study.suppression.GrepSuppressionPython",
        "--repo_dir=" + repo_dir,
        "--commit_id=" + commit_id_csv_list,
        "--results_dir=" + results_dir])

    if not os.listdir(suppression_result):
        os.rmdir(suppression_result)
        print("No suppression found by running GrepSuppressionPython.")
        return

    # Create a folder for storing 'git log' results
    # with tempfile.TemporaryDirectory() as work_path:
    log_result_folder = join(results_dir, "gitlog_history")
    if not os.path.exists(log_result_folder):
        os.makedirs(log_result_folder)
    
    # Specify a Json file path to store all change events at suppression level
    history_json_file = join(log_result_folder, "histories_suppression_level_all.json")

    # Get git log results for all the suppression in latest commit. results in log_result_folder
    init = ExtractHistory(repo_dir, all_commits_list, all_dates_list, results_dir, log_result_folder, history_json_file)

    # Check commits and suppression to extract histories of all suppressions.
    init.track_commits_backward()

    
if __name__=="__main__":
    args = parser.parse_args()
    print("Running...")
    start_time = datetime.datetime.now()
    main(args.repo_dir, args.commit_id_csv_list, args.results_dir)
    end_time = datetime.datetime.now()
    executing_time = (end_time - start_time).seconds
    print(f"Executing time: {executing_time} seconds")
    print("Done.")
