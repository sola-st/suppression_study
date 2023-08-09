import os
from os.path import join

class WarningTypeLine():
    def __init__(self, warning_type, line_number):
        self.warning_type = warning_type
        self.line_number = line_number


class AnalyzeGitlogReport():
    def __init__(self, log_result_folder):
        self.log_result_folder = log_result_folder

        all_change_events = []
        self.all_change_events = all_change_events

    def get_commit_block(self):
        '''
        An example of how information are recorded in log_result, 
        which is defined as commit_block: (commit level information)
            commit b8b38907473533f98784700b4cf6e9a656b1780d
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
        all_commit_block = []
        commit_block = []

        files = os.listdir(self.log_result_folder)
        for file in files:
            # Read log_result, and separate all lines to several commit_block s
            if file.endswith(".txt"):
                with open(os.path.join(self.log_result_folder, file), "r") as f:
                    lines = f.readlines()

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
                                all_commit_block_file_level.append(commit_block)
                                commit_block = []
                                start_count = 1
                        # Append lines to commit_block
                        if start_count == 1:
                            commit_block.append(line)
                    if line_count == lines_max:
                        all_commit_block_file_level.append(commit_block)
                        commit_block = []

                all_commit_block.append(all_commit_block_file_level)

        all_change_events_list_commit_level = self.represent_log_result_to_json(all_commit_block)
        return all_change_events_list_commit_level
        
    def get_warning_type_line(self, source_code, hunk_line_range):
        '''
        -- Git log commit block level --
        With extracted changed line range and source code, locate suppression,
        and get warning type and line number.
        Return a list with warning types line numbers.
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
                                raw_warning_type = suppression_content.split("[")[1].replace("]", "")
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
                    for old, new in zip(old_type_line_set, new_type_line_set):
                        # Handle multiple warning types in one line.
                        old_multi_num = 1
                        new_multi_num = 1
                        old_warning_types = []
                        new_warning_types = []

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
                else:
                    operation_set.append("tricky")
        
        return type_line_set, operation_set
    
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

    def represent_log_result_to_json(self, all_commit_block):
        '''
        Represent git log results to JSON strings, return a change_events_file_level list.
        '''
        all_index = 0
        commit_id = ""
        date = ""
        file_path = ""

        # Represent commit_block to Json string
        for block_file_level in all_commit_block:
            change_events_file_level = [] 
            for block in block_file_level:
                after_line_range_mark = ""
                old_hunk_line_range = []
                new_hunk_line_range = []
                old_source_code = []
                new_source_code = []
                operation_helper = ""
                for line in block:
                    # Extract metadata from git log report.
                    if line.startswith("commit "): # Commit
                        commit_id = line.split(" ")[1].strip()
                    elif line.startswith("Date:"): # Date
                        date = line.split(":", 1)[1].strip()
                    elif line.startswith("--- /dev/null"): # File not exists in old commit
                        operation_helper = "file add" # Only able to report "file add", not "file delete"
                    elif line.startswith("+++"): # File path in new commit
                        file_path = line.split("/", 1)[1].strip()
                    elif line.startswith("@@ "): # Changed hunk
                        '''
                        Assume 'ab' means 'absolute value of the number of changed lines'
                        Format: @@ -old_start,ab +new_start,ab @@
                                eg,. @@ -1,2 +2,1 @@
                                    @@ -7,2 +7,2 @@  
                        Here the line number start from 1, and 0 means no lines.
                        ''' 
                        tmp = line.split(" ")
                        old_line_tmp = tmp[1].replace("-", "").split(",")
                        old_start = int(old_line_tmp[0])
                        old_end = old_start + int(old_line_tmp[1])
                        old_hunk_line_range = range(old_start, old_end)

                        new_line_tmp = tmp[2].replace("+", "").split(",")
                        new_start = int(new_line_tmp[0])
                        new_end = new_start + int(new_line_tmp[1])
                        new_hunk_line_range = range(new_start, new_end)
                        after_line_range_mark = "yes"
                    
                    if after_line_range_mark: # Source code
                        if line.startswith("-"):
                            old_source_code.append(line.replace("-", "", 1).strip())
                        if line.startswith("+"):
                            new_source_code.append(line.replace("+", "", 1).strip())

                # Get warning types, line numbers and operations
                type_line_set, operation_set = self.get_change_operation(
                        old_source_code, old_hunk_line_range, new_source_code, new_hunk_line_range, operation_helper)   
                
                # Represent to json string
                change_event = ""
                operation_count = len(operation_set)         
                if operation_count > 0:
                    if operation_set.count("delete") == operation_count:
                        for old_type_line, operation in zip(type_line_set, operation_set):
                            change_event = self.represent_to_json_string(commit_id, date, file_path, 
                                    old_type_line.warning_type, old_type_line.line_number, operation)
                            # Avoid crossed suppression in changed hunk, step 1
                            change_events_file_level, all_index = self.handle_suppression_crossed_hunk(change_event, 
                                    change_events_file_level, all_index)
                    elif operation_set.count("add") == operation_count or operation_set.count("file add") == operation_count:
                        for new_type_line, operation in zip(type_line_set, operation_set):
                            change_event = self.represent_to_json_string(commit_id, date, file_path, 
                                    new_type_line.warning_type, new_type_line.line_number, operation)
                            change_events_file_level, all_index = self.handle_suppression_crossed_hunk(change_event, 
                                    change_events_file_level, all_index)
                    elif operation_set[0] == "tricky":
                        tricky_recorder = join(self.log_result_folder, "tricky_recorder.txt")
                        write_str = ""
                        for line in block:
                            write_str = write_str + line + "\n"
                        with open(tricky_recorder, "a") as f:
                            f.writelines(write_str+ "\n")
                    else:
                        for type_line, operation in zip(type_line_set, operation_set):
                            if operation == "delete":
                                change_event = self.represent_to_json_string(commit_id, date, file_path, 
                                        type_line.warning_type, type_line.line_number, operation)
                            elif operation == "add":
                                change_event = self.represent_to_json_string(commit_id, date, file_path, 
                                    type_line.warning_type, type_line.line_number, operation)
                            change_events_file_level, all_index = self.handle_suppression_crossed_hunk(change_event, 
                                    change_events_file_level, all_index)
            # Avoid crossed suppression in changed hunk, step 2
            if change_events_file_level:
                self.all_change_events.append({"# S" + str(all_index) : change_events_file_level})
                all_index+=1

        return self.all_change_events # commit level
    
    def handle_suppression_crossed_hunk(self, change_event, change_events_file_level, all_index):
        '''
        Handle the cases that contain more than 1 suppression in the changed hunk.
        These suppression will be presented in one 'element' at the file level.
        To represent the suppressions at the suppression level, here recognize different suppression in one changed hunk.
        '''
        if str(change_event) not in str(self.all_change_events):
            if change_events_file_level:
                last_event = change_events_file_level[-1]
                # Recognize different suppressions
                if last_event["warning_type"] != change_event["warning_type"] or \
                        (last_event["warning_type"] == change_event["warning_type"] \
                                and "delete" not in last_event["change_operation"]): 
                    # and last_event["line_number"] != change_event["line_number"]
                    self.all_change_events.append({"# S" + str(all_index) : change_events_file_level})
                    change_events_file_level = []
                    all_index+=1
                    change_events_file_level.append(change_event)
                else:
                    change_events_file_level.append(change_event)
            else:
                change_events_file_level.append(change_event)
        return change_events_file_level, all_index

