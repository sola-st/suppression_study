import json
from os.path import join

from suppression_study.evolution.ChangeEvent import ChangeEvent
from suppression_study.evolution.CommitBlockInfo import AllCommitBlock, CommitBlock
from suppression_study.evolution.IdentifyChangeOperation import IdentifyChangeOperation


class AnalyzeGitlogReport():
    def __init__(self, log_results_info_list, tracked_deleted_files, tracked_delete_commit, tracked_delete_date, \
                tracked_suppression_deleted_mark, log_result_folder):
        self.log_results_info_list = log_results_info_list
        self.tracked_deleted_files = tracked_deleted_files
        self.tracked_delete_commit = tracked_delete_commit
        self.tracked_delete_date = tracked_delete_date
        self.tracked_suppression_deleted_mark = tracked_suppression_deleted_mark
        self.log_result_folder = log_result_folder
        self.all_change_events_commit_level = []

    def from_gitlog_results_to_change_events(self): # Start point of this class
        '''
        Read git log results files, get commit blocks, and represent these commit blocks to change events.
        Return a list of change events at the commit level.
        
        An example of how information are recorded in log_result, which is defined as commit_block: 
            commit b8bxxx38xxx73533f98784700xx656b1780d
            Author: xxx xxx
            Date:   Tue Jul 4 10:50:41 2023 +0200

                <commit comment>

            diff --git a/foo.py b/foo.py
            --- /dev/null
            +++ b/foo.py
            @@ -0,0 +1,2 @@
            +def some_fun(a, b):
            +    return a + b
            \ No newline at end of file
        A 'git log' result contains one or more commit block(s).
        '''
        commit_block_commit_level = []
        commit_block = []
        
        for file_tmp in self.log_results_info_list:
            file = file_tmp.log_results
            # Read log_result, and separate all lines to several commit_block s
            if file.endswith(".txt"):
                with open(file, "r") as f:
                    lines = f.readlines()

                file_delete_check_tmp = file.split("/")[-1].split("_")[:2]
                file_delete_check = "/".join(file_delete_check_tmp)
                start_count = 0
                all_commit_block_file_level = []
                lines_len = len(lines)
                lines_max = lines_len-1
                for line, line_count in zip(lines, range(lines_len)): # There are empty lines in "lines"
                    line = line.replace("\n", "").strip()
                    # Deal with the start line of commit_block
                    if line:
                        if line.startswith("commit "):
                            start_count+=1 # found the start point of a commit_block
                            if start_count == 2: # basic setting: one commit block has one start
                                commit_block_instance= CommitBlock(commit_block).get_commit_block()
                                all_commit_block_file_level.append(commit_block_instance)
                                commit_block = []
                                start_count = 1
                        # Append lines to commit_block
                        if start_count == 1:
                            commit_block.append(line)
                    if line_count == lines_max:
                        commit_block_instance = CommitBlock(commit_block).get_commit_block()
                        all_commit_block_file_level.append(commit_block_instance)
                        commit_block = []
                commit_block_file_level_info = AllCommitBlock(all_commit_block_file_level, file_delete_check)
                commit_block_commit_level.append(commit_block_file_level_info)

        all_change_events_list_commit_level = self.get_change_events_commit_level(commit_block_commit_level)
        return all_change_events_list_commit_level

    def get_change_events_commit_level(self, commit_block_commit_level):
        all_index = 0

        for block_logfile_level in commit_block_commit_level:
            '''
            In general, block_logfile_level is about only 1 suppression.
            All the blocks at this level could be change events for the suppression (add, delete, 'change')
            Special cases: change warning type (delete old warning type, add new one)
            '''
            # Check if the file_path in current commit block was deleted 
            file_delete_mark = False
            if block_logfile_level.delete_check in str(self.tracked_deleted_files):
                file_delete_mark = True

            change_events_suppression_level = []
            for block in block_logfile_level.block:
                type_line_set, operation_set, tricky_mark = IdentifyChangeOperation(block).identify_change_operation() 

                if tricky_mark:
                    self.record_tricky_cases(block)
                    return self.all_change_events_commit_level
     
                # Get change event
                change_event = ""
                operation_count = len(operation_set)         
                if operation_count > 0:
                    if operation_set.count("delete") == operation_count: # all delete
                        for old_type_line, operation in zip(type_line_set, operation_set):
                            change_event_init = ChangeEvent(block.commit_id, block.date, block.file_path, 
                                    old_type_line.warning_type, old_type_line.line_number, operation)
                            change_event = change_event_init.get_change_event_dict()
                            # Avoid crossed suppression in changed hunk
                            change_events_suppression_level, all_index = self.handle_suppression_crossed_hunk(change_event, \
                                    change_events_suppression_level, all_index)
                    elif operation_set.count("add") == operation_count or operation_set.count("file add") == operation_count: # all add
                        for new_type_line, operation in zip(type_line_set, operation_set):
                            change_event_init = ChangeEvent(block.commit_id, block.date, block.file_path, 
                                    new_type_line.warning_type, new_type_line.line_number, operation)
                            change_event = change_event_init.get_change_event_dict()
                            change_events_suppression_level, all_index = self.handle_suppression_crossed_hunk(change_event, \
                                    change_events_suppression_level, all_index)
                    else: # delete and add mixed
                        for type_line, operation in zip(type_line_set, operation_set):
                            if operation == "delete":
                                change_event_init = ChangeEvent(block.commit_id, block.date, block.file_path, 
                                        type_line.warning_type, type_line.line_number, operation)
                                change_event = change_event_init.get_change_event_dict()
                            elif operation == "add":
                                change_event_init = ChangeEvent(block.commit_id, block.date, block.file_path, 
                                    type_line.warning_type, type_line.line_number, operation)
                                change_event = change_event_init.get_change_event_dict()
                            change_events_suppression_level, all_index = self.handle_suppression_crossed_hunk(change_event, \
                                    change_events_suppression_level, all_index)

            if change_events_suppression_level:
                # File delete, current change_events_suppression_level will be deleted in the next commit
                self.handle_delete_cases(change_events_suppression_level, file_delete_mark, all_index) 
                change_events_suppression_level = []
        return self.all_change_events_commit_level
    
    def record_tricky_cases(self, block):
            serializable_block = {}
            for key, value in block.__dict__.items():
                if isinstance(value, range):
                    serializable_block[key] = list(value)
                else:
                    serializable_block[key] = value

            tricky_recorder = join(self.log_result_folder, "tricky_recorder.txt")
            with open(tricky_recorder, "a") as f:
                json.dump(serializable_block, f, indent=4, ensure_ascii=False)

    def handle_delete_cases(self,change_events_suppression_level, file_delete_mark, all_index):
        '''
        This function covers 3 different cases:
        1) file delete happens in the next commit, the suppression in commit are all deleted.
        2) no suppression in the next commit, the suppression in commit are all deleted.
        3) above 1) and 2) didn't happened.
        '''
        delete_operation = ""
        if file_delete_mark:
            delete_operation = "file delete"
        elif self.tracked_suppression_deleted_mark:
            delete_operation = "delete" # No suppression in new commit, but there are in old commit.
        if delete_operation:
            last_event = change_events_suppression_level[-1]
            if "delete" not in last_event["change_operation"]:
                delete_change_event_init = ChangeEvent(self.tracked_delete_commit, self.tracked_delete_date, 
                        last_event["file_path"], last_event["warning_type"], last_event["line_number"], delete_operation)
                delete_change_event = delete_change_event_init.get_change_event_dict()
                change_events_suppression_level.append(delete_change_event)
                self.all_change_events_commit_level.append({"# S" + str(all_index) : change_events_suppression_level})
                change_events_suppression_level = []
                all_index+=1
        else: # No "file delete" and no "no suppression in the next commit"
            self.all_change_events_commit_level.append({"# S" + str(all_index) : change_events_suppression_level})
    
    def handle_suppression_crossed_hunk(self, change_event, change_events_suppression_level, all_index):
        '''
        Handle the cases that contain more than 1 suppression in the changed hunk.
        These suppression is mixed at the file level.
        To represent the suppressions at the suppression level, here recognize different suppression in one changed hunk.
        '''
        if str(change_event) not in str(self.all_change_events_commit_level):
            if change_events_suppression_level:
                last_event = change_events_suppression_level[-1]
                # Warning type changed cases: recognize different suppressions
                if last_event["warning_type"] == change_event["warning_type"]: 
                    if "delete" in change_event["change_operation"] and "delete" not in last_event["change_operation"]:
                        # The history of current suppression are all collected, append it to commit level, start to check the next suppression
                        change_events_suppression_level.append(change_event)
                        self.all_change_events_commit_level.append({"# S" + str(all_index) : change_events_suppression_level})
                        change_events_suppression_level = []
                        all_index+=1
                else: # A new suppression was added
                    # Append already exists suppression in all_change_events_commit_level
                    self.all_change_events_commit_level.append({"# S" + str(all_index) : change_events_suppression_level})
                    # Start to check the next totally new suppression
                    change_events_suppression_level = []
                    change_events_suppression_level.append(change_event)
            else:
                change_events_suppression_level.append(change_event)
        return change_events_suppression_level, all_index