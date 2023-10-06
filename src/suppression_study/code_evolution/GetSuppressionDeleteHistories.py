import os
import subprocess
from suppression_study.code_evolution.ChangeEvent import ChangeEvent, get_change_event_dict
from suppression_study.code_evolution.DiffBlock import DiffBlock
from os.path import join

from suppression_study.suppression.Suppression import read_suppressions_from_file


class DeleteEventAndSuppression:
    def __init__(self, delete_event, suppression):
        self.delete_event = delete_event
        self.suppression = suppression


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
        delete_event_and_suppression_list = []
        suppression_final_commits_list = []

        self.selected_1000_commits_list.reverse()
        max_commits_num = len(self.selected_1000_commits_list) - 1
        for i in range(0, max_commits_num):  # Start from  oldest
            current_commit = self.selected_1000_commits_list[i]
            next_commit = self.selected_1000_commits_list[i + 1]
            next_date = self.selected_1000_dates_list[i + 1]

            # get file delete cases
            get_deleted_files_command = f"git diff --name-only --diff-filter=D {current_commit} {next_commit}"
            result = subprocess.run(
                get_deleted_files_command,
                cwd=self.repo_dir,
                shell=True,
                stdout=subprocess.PIPE,
                universal_newlines=True,
            )
            deleted_files = result.stdout

            current_suppression_csv = join(self.grep_folder, f"{current_commit}_suppression.csv")
            if os.path.exists(current_suppression_csv):
                suppression_set = read_suppressions_from_file(current_suppression_csv)
                for suppression in suppression_set:
                    current_file = suppression.path
                    file_delete_mark = current_file in deleted_files
                    if file_delete_mark == True:
                        delete_event_object = ChangeEvent(
                                next_commit, next_date, current_file, suppression.text, suppression.line, "delete")
                        suppression_final_commits_list.append(current_commit)
                    else:
                        commit_diff_command = f"git diff {current_commit} {next_commit} -- {current_file}"
                        result = subprocess.run(commit_diff_command, cwd=self.repo_dir, shell=True,
                                stdout=subprocess.PIPE, universal_newlines=True,)
                        diff_contents = result.stdout
                        # if result.stderr:
                        #     print(f"**hu {result.stderr}")
                        delete_event_object = DiffBlock(
                            next_commit, next_date, diff_contents, suppression
                        ).from_diff_block_to_delete_event()
                        suppression_final_commits_list.append(current_commit)

                    if delete_event_object:
                        delete_event_ready_to_json = get_change_event_dict(delete_event_object)
                        delete_event_and_suppression = DeleteEventAndSuppression(
                            delete_event_ready_to_json, suppression
                        )
                        delete_event_and_suppression_list.append(delete_event_and_suppression)
        return delete_event_and_suppression_list, suppression_final_commits_list
