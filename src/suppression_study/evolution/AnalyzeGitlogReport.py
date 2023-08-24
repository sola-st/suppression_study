import json
from os.path import join

from suppression_study.evolution.ChangeEvent import ChangeEvent
from suppression_study.evolution.CommitBlockInfo import AllCommitBlock, CommitBlock

class WarningTypeLine():
    def __init__(self, warning_type, line_number):
        self.warning_type = warning_type
        self.line_number = line_number


class AnalyzeGitlogReport():
    def __init__(self, log_results_info_list, tracked_deleted_files, tracked_delete_commit, tracked_delete_date, log_result_folder):
        self.log_results_info_list = log_results_info_list
        self.tracked_deleted_files = tracked_deleted_files
        self.tracked_delete_commit = tracked_delete_commit
        self.tracked_delete_date = tracked_delete_date
        self.log_result_folder = log_result_folder
        self.all_change_events_commit_level = []

    def from_gitlog_results_to_change_events(self):
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
                                commit_block_instance = CommitBlock(commit_block).get_commit_block()
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
        
    def get_warning_type_line(self, source_code, hunk_line_range):
        '''
        With extracted changed line range and source code, locate suppression, and get warning type and line number.
        Return a list with warning types and line numbers.
        '''
        warning_type_set = []
        line_number_set = []
        type_line_set = []
        suppressor_set = ["# pylint:", "# type:"]
        comment_symbol = "#"

        for source_line, line_number in zip(source_code, hunk_line_range):
            for the_suppressor in suppressor_set:
                if the_suppressor in source_line:
                    if source_line.startswith(the_suppressor):
                        warning_type_set.append(source_line)
                        line_number_set.append(line_number)
                    else: # Suppression mixed with code
                        if source_line.startswith(comment_symbol): # Current source_line is a comment.
                            pass 
                        else: 
                            suppression_content = ""
                            if source_line.count(comment_symbol) >= 1: # 1 of the comment_symbol s is for suppression
                                suppression_tmp = source_line.split(the_suppressor)[1]
                                if comment_symbol in suppression_tmp: # comments come after suppression
                                    suppression_content = the_suppressor + suppression_tmp.split(self.comment_symbol, 1)[0]
                                else: 
                                    suppression_content = the_suppressor + suppression_tmp
                            '''
                            Multi- warning type suppression
                            Here keep the multiple types, 
                            eg,. ("unused-import", "invalid-name")
                            here extract : "unused-import", "invalid-name" (line level)
                            will separate to "unused-import" and "invalid-name" in function 'get_change_operation'. (suppression level)

                            The reason here keep multiple types aims to keep the feature to recognize inline changes to the suppressions.
                            Change operation:
                            eg,. "unused-import" -> keep
                                 "invalid-name" -> delete
                            ''' 
                            if "(" in suppression_content:
                                raw_warning_type = suppression_content.split("(")[1].replace(")", "")
                                warning_type_set.append(raw_warning_type)
                                line_number_set.append(line_number)
                            elif "[" in suppression_content:
                                raw_warning_type = suppression_content.split(".)[1].replace(", "")
                                warning_type_set.append(raw_warning_type)
                                line_number_set.append(line_number)
                            else:
                                warning_type_set.append(suppression_content)
                                line_number_set.append(line_number)
                    break # The suppressor found, not check other suppression anymore.

        for warning_type, line_number in zip(warning_type_set, line_number_set):
            # warning_type can be multiple types.
            type_line = WarningTypeLine(warning_type, line_number)
            type_line_set.append(type_line)
        return type_line_set
    
    def get_change_operation(self, old_source_code, old_hunk_line_range, new_source_code, new_hunk_line_range, operation_helper):
        type_line_set = []
        operation_set = []
        operation = ""
        old_type_line_set = self.get_warning_type_line(old_source_code, old_hunk_line_range)
        new_type_line_set = self.get_warning_type_line(new_source_code, new_hunk_line_range)
        
        old_suppression_count = len(old_type_line_set)
        new_suppression_count = len(new_type_line_set)
        if old_suppression_count == 0: # no suppression in old commit
            if new_suppression_count > 0: 
                operation = "add"
                if operation_helper: # if operation_helper exists, it's a file add case.
                    operation_set.append(operation_helper)
                else:
                    operation_set.append(operation)
                type_line_set = new_type_line_set
        else: # old_suppression_count > 0
            if new_suppression_count == 0:
                operation = "delete"
                operation_set.append(operation)
                type_line_set = old_type_line_set
            else: # suppression in both old and new commit
                if old_suppression_count == new_suppression_count: 
                    # old/new_suppression_count can be 1 or more, here count # type: ignore[A, B] as 1
                    for old, new in zip(old_type_line_set, new_type_line_set):
                        old_multi_num = 1
                        new_multi_num = 1
                        old_warning_types = []
                        new_warning_types = []
                        # Separate "# type: ignore[A, B]"" to "A" and "B", to handle multiple warning types in one suppression line
                        if "," in old.warning_type:
                            old_warning_types = old.warning_type.split(",")
                            old_multi_num = len(old_warning_types)
                        else:
                            old_warning_types.append(old.warning_type)

                        if "," in new.warning_type:
                            new_warning_types = new.warning_type.split(",")
                            new_multi_num = len(new_warning_types)
                        else:
                            new_warning_types.append(new.warning_type)
                        # Get change operations, cover different in-line change sub-cases
                        type_line_set, operation_set = self.identify_change_operation_helper(old_multi_num, new_multi_num, \
                                old, new, old_warning_types, new_warning_types)
                else:
                    operation_set.append("tricky")
        return type_line_set, operation_set
    
    def identify_change_operation_helper(self, old_multi_num, new_multi_num, old, new, old_warning_types, new_warning_types):
        type_line_set = []
        operation_set = []
        operation = ""

        # Sub-case: the number of warnings in a line is the same, includes 0.
        if old_multi_num == new_multi_num:
            if old.warning_type != new.warning_type:
                operation = "delete"
                type_line_set.append(old)
                operation_set.append(operation)
                operation = "add"
                type_line_set.append(new)
                operation_set.append(operation)
        # Sub-case: delete existing warning types in-line
        elif old_multi_num > new_multi_num: 
            real_delete = 0
            for old_type in old_warning_types:
                old_type = old_type.strip()
                if old_type.strip() not in str(new_warning_types):
                    real_delete +=1
                    operation = "delete"
                    deleted_old = WarningTypeLine(old_type, old.line_number)
                    type_line_set.append(deleted_old)
                    operation_set.append(operation)
            # All old warning type were deleted, and add a totally new warning type
            if real_delete == old_multi_num and new_multi_num != 0:
                for new_type in new_warning_types:
                    operation = "add"
                    added_new = WarningTypeLine(new_type, new.line_number)
                    type_line_set.append(added_new)
                    operation_set.append(operation)
        # Sub-case: add new warning types in-line
        elif old_multi_num < new_multi_num: 
            real_add = 0
            for new_type in new_warning_types:
                new_type = new_type.strip()
                if new_type.strip() not in str(old_warning_types):
                    real_add +=1
                    operation = "add"
                    added_new = WarningTypeLine(new_type, new.line_number)
                    type_line_set.append(added_new)
                    operation_set.append(operation)
            # All new warning type are newly added, and the existing warning types were deleted
            if real_add == new_multi_num and old_multi_num != 0:
                for old_type in old_warning_types:
                    operation = "delete"
                    deleted_old = WarningTypeLine(old_type, old.line_number)
                    type_line_set.append(deleted_old)
                    operation_set.append(operation)
        return type_line_set, operation_set

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
                type_line_set, operation_set = self.get_change_operation(block.old_source_code, \
                        block.old_hunk_line_range, block.new_source_code, block.new_hunk_line_range, block.operation_helper)   
     
                # Get change event
                change_event = ""
                operation_count = len(operation_set)         
                if operation_count > 0:
                    if operation_set.count("delete") == operation_count:
                        for old_type_line, operation in zip(type_line_set, operation_set):
                            change_event_init = ChangeEvent(block.commit_id, block.date, block.file_path, 
                                    old_type_line.warning_type, old_type_line.line_number, operation)
                            change_event = change_event_init.get_change_event_dict()
                            # Avoid crossed suppression in changed hunk
                            change_events_suppression_level, all_index = self.handle_suppression_crossed_hunk(change_event, \
                                    change_events_suppression_level, all_index)
                    elif operation_set.count("add") == operation_count or operation_set.count("file add") == operation_count:
                        for new_type_line, operation in zip(type_line_set, operation_set):
                            change_event_init = ChangeEvent(block.commit_id, block.date, block.file_path, 
                                    new_type_line.warning_type, new_type_line.line_number, operation)
                            change_event = change_event_init.get_change_event_dict()
                            change_events_suppression_level, all_index = self.handle_suppression_crossed_hunk(change_event, \
                                    change_events_suppression_level, all_index)
                    elif operation_set[0] == "tricky":
                        tricky_recorder = join(self.log_result_folder, "tricky_recorder.txt")
                        with open(tricky_recorder, "a") as f:
                            f.write(json.dumps(block)+ "\n")
                    else:
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
                        if file_delete_mark:
                            last_event = change_events_suppression_level[-1]
                            if "delete" not in last_event["change_operation"]:
                                delete_change_event_init = ChangeEvent(self.tracked_delete_commit, self.tracked_delete_date, 
                                        last_event["file_path"], last_event["warning_type"], last_event["line_number"], "file delete")
                                delete_change_event = delete_change_event_init.get_change_event_dict()
                                change_events_suppression_level.append(delete_change_event)

                        self.all_change_events_commit_level.append({"# S" + str(all_index) : change_events_suppression_level})
                        all_index+=1
        return self.all_change_events_commit_level
    
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
                    if "delete" in change_event["change_operation"]:
                        change_events_suppression_level.append(change_event)
                        self.all_change_events_commit_level.append({"# S" + str(all_index) : change_events_suppression_level})
                        change_events_suppression_level = []
                        all_index+=1
            else:
                change_events_suppression_level.append(change_event)
        return change_events_suppression_level, all_index