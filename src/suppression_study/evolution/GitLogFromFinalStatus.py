import subprocess

from suppression_study.evolution.AnalyzeGitlogReport import AnalyzeGitlogReport
from suppression_study.suppression.FormatSuppressionCommon import get_suppressor
from suppression_study.suppression.Suppression import get_raw_warning_type_from_formatted_suppression_text
from git.repo import Repo


class GitLogFromFinalStatus():

    def __init__(self, repo_dir, never_removed_suppressions, delete_event_suppression_commit_list):
        self.repo_dir = repo_dir
        self.never_removed_suppressions = never_removed_suppressions
        self.delete_event_suppression_commit_list = delete_event_suppression_commit_list

        self.only_add_event_histories = []
        self.add_delete_histories = []

        self.repo_base = Repo(self.repo_dir)

    def run_git_log(self, suppression, log_result, run_command_mark):
        # always only one suppressor for a suppression
        suppressor = get_suppressor(suppression.text)
        raw_warning_type = get_raw_warning_type_from_formatted_suppression_text(suppression.text)
       
        '''
        About git log command:
        1) git log command cannot find file delete cases.
        It extracts the histories from when the file was added, re-added is a new start.
        2) The result.stdout will not be empty.
            eg,. Assume that there is a repository, suppression only exists in latest commit, 
                the result.stdout will show the changes in latest commit.

        -C: cover copied files
        -M: cover renamed files
        -L: [line_range_start, line_range_end]
        --first-parent: only focus on main/master branch
        '''
        current_file = suppression.path
        if run_command_mark == True:
            # Line start and end can be the same, eg,. [6,6] means line 6
            line_range_start_end = suppression.line 
            line_range_str = str(line_range_start_end)
            command_line = "git log -C -M -L" + line_range_str + "," + line_range_str + ":'" + current_file + "' --first-parent"
            result = subprocess.run(command_line, cwd=self.repo_dir, shell=True, stdout=subprocess.PIPE, universal_newlines=True)
            log_result = result.stdout
            
        expected_add_event = AnalyzeGitlogReport(log_result, suppressor, raw_warning_type, current_file).from_gitlog_results_to_change_events()

        return expected_add_event, log_result
    
    def git_log_never_removed_suppression(self, last_commit_with_suppression):
        ''' 
        all the suppression here are only with 1 warning type
        which means there could be several suppressions has the same line number in the never_removed_suppressions list

        To avoid repeatedly run the git log command, here set a run_command_mark.
        run_command_mark: 
            false, use previously obtained git log results    
            true, run git log command to get results
        '''
        self.repo_base.git.checkout(last_commit_with_suppression, force=True)

        previous_file_and_line = ""
        log_result = ""
        for suppression in self.never_removed_suppressions:
            run_command_mark = False
            file_and_line = f"{suppression.path} {suppression.line}"
            if file_and_line != previous_file_and_line:
                run_command_mark = True
            # expected_add_event is a dict, and ready to write to history json file.
            expected_add_event, log_result = self.run_git_log(suppression, log_result, run_command_mark)
            # all the suppression level events in histories is a list
            # 1) [add event]
            # 2) [add event, delete event]
            self.only_add_event_histories.append([expected_add_event])
            previous_file_and_line = file_and_line

        return self.only_add_event_histories

    def git_log_deleted_suppression(self):
        previous_file_and_line = ""
        previous_checkout_commit = ""
        log_result = ""
        for delete_info in self.delete_event_suppression_commit_list:
            if delete_info.last_exists_commit != previous_checkout_commit:
                self.repo_base.git.checkout(delete_info.last_exists_commit, force=True)

            delete_suppression = delete_info.suppression
            run_command_mark = False
            file_and_line = f"{delete_suppression.path} {delete_suppression.line}"
            if file_and_line != previous_file_and_line:
                run_command_mark = True

            expected_add_event, log_result = self.run_git_log(delete_suppression, log_result, run_command_mark)
            delete_event = delete_info.delete_event
            self.add_delete_histories.append([expected_add_event, delete_event])
            previous_file_and_line = file_and_line
            previous_checkout_commit = delete_info.last_exists_commit

        return self.add_delete_histories
