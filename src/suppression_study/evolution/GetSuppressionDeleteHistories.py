import os
import subprocess
from suppression_study.evolution.ChangeEvent import ChangeEvent, get_change_event_dict
from suppression_study.evolution.DiffBlock import DiffBlock
from os.path import join

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

    def __init__(self, repo_dir, selected_1000_commits_list, selected_1000_dates_list, grep_folder):
        self.repo_dir = repo_dir
        self.selected_1000_commits_list = selected_1000_commits_list
        self.selected_1000_dates_list = selected_1000_dates_list
        self.grep_folder = grep_folder

    def track_commits_forward(self):
        '''
        Compare commit_1 and commit_2,
        deleted_files : current commit is commit_1, check which files was deleted in commit_2
        '''
        delete_event_suppression_commit_list = []

        max_commits_num = len(self.selected_1000_commits_list) - 1
        for i in range(0, max_commits_num):  # Start from  oldest
            current_commit = self.selected_1000_commits_list[i]
            next_commit = self.selected_1000_commits_list[i + 1]
            next_date = self.selected_1000_dates_list[i + 1]

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

            last_exists_commit = ""
            current_suppression_csv = join(self.grep_folder, f"{current_commit}_suppression.csv")
            if os.path.exists(current_suppression_csv):
                suppression_set = read_suppressions_from_file(current_suppression_csv)
                previous_file = ""
                diff_result = ""
                for suppression in suppression_set:
                    current_file = suppression.path
                    file_delete_mark = current_file in deleted_files
                    if file_delete_mark == True:
                        delete_event_object = ChangeEvent(
                                next_commit, next_date, current_file, suppression.text, suppression.line, "file delete")
                        delete_event_ready_to_json = get_change_event_dict(delete_event_object)
                        last_exists_commit = current_commit
                    else:
                        raw_warning_type = get_raw_warning_type_from_formatted_suppression_text(suppression.text)
                        # no file rename
                        if current_file != previous_file: # for the same file, run git diff only once
                            commit_diff_command = f"git diff {current_commit} {next_commit} -- {current_file}"
                            # file rename
                            if current_file in file_paths_in_current_commit:
                                current_file_index = file_paths_in_current_commit.index(current_file)
                                file_path_in_next_commit = file_paths_in_next_commit[current_file_index]
                                commit_diff_command = f"git diff {current_commit}:{current_file} {next_commit}:{file_path_in_next_commit}"
                            diff_result = subprocess.run(commit_diff_command, cwd=self.repo_dir, shell=True,
                                stdout=subprocess.PIPE, universal_newlines=True)
                        diff_contents = diff_result.stdout
                        delete_event_ready_to_json = DiffBlock(
                            next_commit, next_date, diff_contents, suppression, raw_warning_type
                        ).from_diff_block_to_delete_event()
                        last_exists_commit = current_commit

                    if delete_event_ready_to_json:
                        delete_event_and_suppression = DeleteEventAndSuppression(
                            delete_event_ready_to_json, suppression, last_exists_commit
                        )
                        delete_event_suppression_commit_list.append(delete_event_and_suppression)
                    previous_file = current_file
        return delete_event_suppression_commit_list
