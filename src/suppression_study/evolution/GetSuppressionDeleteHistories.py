import subprocess
from suppression_study.evolution.ChangeEvent import ChangeEvent, get_change_event_dict
from suppression_study.evolution.DiffBlock import DiffBlock
from os.path import join, exists
from suppression_study.suppression.Suppression import (
    get_raw_warning_type_from_formatted_suppression_text, read_suppressions_from_file)


class DeleteEventAndSuppression:
    def __init__(self, delete_event, suppression, last_exists_commit):
        self.delete_event = delete_event
        self.suppression = suppression
        self.last_exists_commit = last_exists_commit


class GetSuppressionDeleteHistories:
    '''
    By receiving a repository and a commit list,
    1) return a history list that includes all never removed suppressions
    2) return a history list that includes all deleted suppressions and their delete events
    '''

    def __init__(self, repo_dir, selected_1000_commits_list, selected_1000_dates_list, grep_folder, specific_numeric_maps):
        self.repo_dir = repo_dir
        self.selected_1000_commits_list = selected_1000_commits_list
        self.selected_1000_dates_list = selected_1000_dates_list
        self.grep_folder = grep_folder
        self.specific_numeric_maps = specific_numeric_maps

    def file_status_check(self, current_commit, next_commit):
        # get file delete cases
        get_deleted_files_command = f"git diff --name-only --diff-filter=D {current_commit} {next_commit}"
        deleted_result = subprocess.run(get_deleted_files_command, cwd=self.repo_dir, shell=True,
            stdout=subprocess.PIPE, universal_newlines=True)
        deleted_files = deleted_result.stdout

        # get file renamed cases
        get_renamed_files_command = f"git diff --name-status --diff-filter=R {current_commit} {next_commit}"
        renamed_result = subprocess.run(get_renamed_files_command, cwd=self.repo_dir, shell=True,
            stdout=subprocess.PIPE, universal_newlines=True)
        renamed_files = renamed_result.stdout
        file_paths_in_current_commit = []
        file_paths_in_next_commit = []

        if renamed_files:
            rename_cases = renamed_files.strip().split("\n")
            for rename in rename_cases:
                # R094    src/traverse.py src/common/traverse.py
                tmp = rename.split("\t")
                if tmp[1].endswith(".py"):
                    file_paths_in_current_commit.append(tmp[1])
                    file_paths_in_next_commit.append(tmp[2])

        return deleted_files, file_paths_in_current_commit, file_paths_in_next_commit
    
    def diff_computation(self, current_commit, next_commit, current_file, file_path_in_next_commit):
        command_prefix = "git diff --ignore-space-at-eol --unified=0"
        # no file rename
        commit_diff_command = f"{command_prefix} {current_commit} {next_commit} -- {current_file}"
        # file rename
        if file_path_in_next_commit:
            commit_diff_command = f"{command_prefix} {current_commit}:{current_file} {next_commit}:{file_path_in_next_commit}"
        diff_result = subprocess.run(commit_diff_command, cwd=self.repo_dir, shell=True,
            stdout=subprocess.PIPE, universal_newlines=True)
        return diff_result

    def track_commits_forward(self):
        '''
        Compare commit_1 and commit_2,
        deleted_files : current commit is commit_1, check which files was deleted in commit_2
        '''
        delete_event_suppression_commit_list = []
        middle_line_number_chain = []
        current_suppression_order_one_round = {}
        next_suppression_order_one_round = {} 

        max_commits_num = len(self.selected_1000_commits_list) - 1
        for i in range(0, max_commits_num):  # Start from oldest
            current_commit = self.selected_1000_commits_list[i]
            next_commit = self.selected_1000_commits_list[i + 1]
            next_date = self.selected_1000_dates_list[i + 1]
            deleted_files, file_paths_in_current_commit, file_paths_in_next_commit = self.file_status_check(current_commit, next_commit)
            last_exists_commit = ""

            current_suppression_csv = join(self.grep_folder, f"{current_commit}_suppression.csv")
            if exists(current_suppression_csv):
                previous_file = ""
                diff_result = ""
                suppression_set = read_suppressions_from_file(current_suppression_csv)
                for j, suppression in enumerate(suppression_set):
                    raw_warning_type = None
                    raw_warning_type_tmp = "aaa" # a random value that is not a warning type
                    delete_event_ready_to_json_info = None
                    file_path_in_next_commit = None

                    current_file = suppression.path
                    if current_file in file_paths_in_current_commit: # file rename check
                        current_file_index = file_paths_in_current_commit.index(current_file)
                        file_path_in_next_commit = file_paths_in_next_commit[current_file_index]

                    file_delete_mark = current_file in deleted_files # file deletion check
                    if file_delete_mark == True:
                        delete_event_object = ChangeEvent(
                                next_commit, next_date, current_file, suppression.text, suppression.line, "file delete")
                        delete_event_ready_to_json = get_change_event_dict(delete_event_object)
                        assert delete_event_ready_to_json != None
                        last_exists_commit = current_commit
                    else:
                        raw_warning_type = get_raw_warning_type_from_formatted_suppression_text(suppression.text) # can be numeric code or text
                        if raw_warning_type[1:].isnumeric() == True:
                            raw_warning_type_tmp = raw_warning_type
                            # always use the text warning type
                            map_check = [specific for specific, numeric in self.specific_numeric_maps.items() if raw_warning_type == numeric]
                            if map_check:
                                raw_warning_type = map_check[0]
                        assert raw_warning_type != None

                        # if "2d77053d" in next_commit:
                        #     pass
                        if current_file != previous_file: # for the same file, run git diff only once
                            diff_result = self.diff_computation(current_commit, next_commit, current_file, file_path_in_next_commit)
                        diff_contents = diff_result.stdout
                        
                        if diff_contents:
                            delete_event_ready_to_json_info = DiffBlock(
                                next_commit, next_date, diff_contents, suppression, raw_warning_type, \
                                self.specific_numeric_maps).from_diff_block_to_delete_event()
                        else:
                            delete_event_ready_to_json_info = suppression.line
                        last_exists_commit = current_commit

                    next_suppression_csv = join(self.grep_folder, f"{next_commit}_suppression.csv")

                    if isinstance(delete_event_ready_to_json_info, int):
                        # it is not deleted, and here the int is the mapped line number of the suppression
                        remain_idx = None
                        if i == 0:
                            middle_line_number_chain.append([{next_commit: delete_event_ready_to_json_info}])
                            remain_idx = len(middle_line_number_chain) - 1
                        else:
                            keys = list(current_suppression_order_one_round.keys())
                            if j in keys:
                                remain_idx = current_suppression_order_one_round[j]
                                middle_line_number_chain[remain_idx].append({next_commit: delete_event_ready_to_json_info})
                            else:
                                middle_line_number_chain.append([{next_commit: delete_event_ready_to_json_info}])
                                remain_idx = len(middle_line_number_chain) - 1

                        if not file_path_in_next_commit:
                            file_path_in_next_commit = current_file

                        mapped_idx = self.update_suppression_order(next_suppression_csv, file_path_in_next_commit, raw_warning_type, \
                            raw_warning_type_tmp, delete_event_ready_to_json_info)
                        next_suppression_order_one_round.update({mapped_idx: remain_idx})

                    else:# the suppression is deleted
                        if delete_event_ready_to_json_info: # and not isinstance(delete_event_ready_to_json_info, dict): 
                            delete_event_ready_to_json, middle_line_number = delete_event_ready_to_json_info
                        delete_event_and_suppression = DeleteEventAndSuppression(
                            delete_event_ready_to_json, suppression, last_exists_commit)
                        delete_event_suppression_commit_list.append(delete_event_and_suppression)
                        if i == 0:
                            middle_line_number_chain.append([{next_commit: middle_line_number}])
                            middle_line_number_chain.append(["delete"])
                        else:
                            # in theory, j should always in current_suppression_order_one_round
                            # but in case it fails to map the indices, we use a filter
                            if j in current_suppression_order_one_round:
                                delete_idx = current_suppression_order_one_round[j]
                                middle_line_number_chain[delete_idx].append({next_commit: suppression.line})
                                middle_line_number_chain[delete_idx].append("delete")
                            # else: ignore the case
                        # next_suppression_order_one_round.update({"delete": delete_idx})
                            
                    previous_file = current_file
                
            # if current_suppression_order_one_round != next_suppression_order_one_round:
            #     print(next_suppression_order_one_round)
            
            current_suppression_order_one_round = next_suppression_order_one_round
            next_suppression_order_one_round = {}

        middle_line_number_chain_remain, middle_line_number_chain_delete = separate_the_line_chains(middle_line_number_chain)
        # assert len(delete_event_suppression_commit_list) == len(middle_line_number_chain_delete)
        return delete_event_suppression_commit_list, middle_line_number_chain_remain, middle_line_number_chain_delete
    
    def update_suppression_order(self, next_suppression_csv, file_path_in_next_commit, \
            raw_warning_type, raw_warning_type_tmp, mapped_line_num):
        if exists(next_suppression_csv):
            next_suppression_set = read_suppressions_from_file(next_suppression_csv)
            for i, suppression in enumerate(next_suppression_set):
                if suppression.path == file_path_in_next_commit and \
                    (raw_warning_type in suppression.text or raw_warning_type_tmp in suppression.text) and \
                    suppression.line == mapped_line_num:
                    return i
                
            print("Mapped idx, not as expected.")
            return None # lower confidence, ignore this


def separate_the_line_chains(middle_line_number_chain):
    middle_line_number_chain_remain = [] 
    middle_line_number_chain_delete = []

    for chain in middle_line_number_chain:
        if "delete" in chain:
            middle_line_number_chain_delete.append(chain)
        else:
            middle_line_number_chain_remain.append(chain)
    return middle_line_number_chain_remain, middle_line_number_chain_delete
