import os
import json
from os.path import join

class WarningTypeLine():
    def __init__(self, warning_type, line_number):
        self.warning_type = warning_type
        self.line_number = line_number


class FormatGitlogReport():

    def __init__(self, log_result_folder):
        self.log_result_folder = log_result_folder

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

        return all_commit_block # 2 dimensions
        
    def get_warning_type_line(self, source_code, line_nums):
        '''
        -- Git log commit block level --
        With extracted changed line range and source code, locate suppression,
        and get warning type and line number.
        Return a list with warning types line numbers.
        '''
        warning_type_set = []
        line_number_set = []
        type_line_set = []
        the_suppressor = "# pylint:"
        comment_symbol = "#"

        for source_line, line_number in zip(source_code, line_nums):
            if the_suppressor in source_line:
                if source_line.startswith(the_suppressor):
                    warning_type_set.append(source_line)
                    line_number_set.append(line_number)
                else: # suppression mixed with code
                    if source_line.startswith(comment_symbol): # Current source_line is a comment.
                        pass 
                    else: 
                        suppression_content = ""
                        if source_line.count(comment_symbol) >= 1: # 1 comment_symbol for suppression
                            suppression_tmp = source_line.split(the_suppressor)[1]
                            if comment_symbol in suppression_tmp: # comments come after suppression
                                suppression_content = the_suppressor + suppression_tmp.split(self.comment_symbol, 1)[0]
                            else: 
                                suppression_content = the_suppressor + suppression_tmp

                        # Multi-type suppression
                        if "(" in suppression_content:
                            warning_type_tmp = suppression_content.split("(")[1].replace(")", "")
                            for warning_type in warning_type_tmp:
                                warning_type_set.append(warning_type)
                                line_number_set.append(line_number)
                        elif "[" in suppression_content:
                            warning_type_tmp = suppression_content.split("[")[1].replace("]", "")
                            for warning_type in warning_type_tmp:
                                warning_type_set.append(warning_type)
                                line_number_set.append(line_number)
                        else:
                            warning_type_set.append(suppression_content)
                            line_number_set.append(line_number)

        for warning_type, line_number in zip(warning_type_set, line_number_set):
            type_line = WarningTypeLine(warning_type, line_number)
            type_line_set.append(type_line)

        return type_line_set
    
    def get_change_operation(self, old_source_code, old_line_nums, new_source_code, new_line_nums, operation_set_helper):
        type_line_set = []
        operation_set = []
        operation = ""
        old_type_line_set = self.get_warning_type_line(old_source_code, old_line_nums)
        new_type_line_set = self.get_warning_type_line(new_source_code, new_line_nums)
        
        old_suppression_count = len(old_type_line_set)
        new_suppression_count = len(new_type_line_set)
        if not old_type_line_set: # no suppression in old commit
            if new_suppression_count == 0: # also no suppression in new commit
                pass
            else:
                operation = "add"
                for i, operation_helper in zip(range(new_suppression_count), operation_set_helper):
                    if operation_helper:
                        operation_set.append(operation_helper)
                    else:
                        operation_set.append(operation)
                type_line_set = new_type_line_set
        else: # update file delete later, write a made-up repository for test, or add new commit
            if new_suppression_count == 0:
                operation = "delete"
                for i, operation_helper in zip(range(old_suppression_count), operation_set_helper):
                    if operation_helper:
                        operation_set.append(operation_helper)
                    else:
                        operation_set.append(operation)
                type_line_set = old_type_line_set
            else: # suppression in both old and new commit
                if old_suppression_count == new_suppression_count:
                    for old, new in zip(old_type_line_set, new_type_line_set):
                        if old.warning_type == new.warning_type:
                            # suppression no change , and mixed source code changed
                            operation = "nochange" 
                            operation_set.append(operation)
                        else:
                            operation = "delete"
                            type_line_set.append(old)
                            operation_set.append(operation)
                            operation = "add"
                            type_line_set.append(new)
                            operation_set.append(operation)
                # Update later, In-line changes: eg,.2 warning types -> 1
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
        all_change_events = []
        all_index = 0
        commit_id = ""
        date = ""
        file_path = ""

        # Represent commit_block to Json string
        for block_file_level in all_commit_block:
            change_events_file_level = [] 
            for block in block_file_level:
                after_line_range_mark = ""
                old_line_nums = []
                new_line_nums = []
                old_source_code = []
                new_source_code = []
                operation_helper = ""
                operation_set_helper = []
                for line in block:
                    line = line
                    # Extract metadata from git log report.
                    if line.startswith("commit "): # Commit
                        commit_id = line.split(" ")[1].strip()
                    elif line.startswith("Date:"): # Date
                        date = line.split(":", 1)[1].strip()
                    elif line.startswith("--- /dev/null"): # File not exists in old commit
                        operation_helper = "file add"
                    elif line.startswith("+++"): # file path in new commit
                        file_path = line.split("/", 1)[1].strip()
                    elif line.startswith("@@ "): # Change line hunk
                        # eg,. @@ -1,2 +2,1 @@
                        #      @@ -7,2 +7,2 @@  
                        # Here the line number start from 1, and 0 means no lines.
                        tmp = line.split(" ")
                        old_line_tmp = tmp[1].replace("-", "").split(",")
                        old_start = int(old_line_tmp[0])
                        old_end = old_start + int(old_line_tmp[1])
                        old_line_nums = range(old_start, old_end)

                        new_line_tmp = tmp[2].replace("+", "").split(",")
                        new_start = int(new_line_tmp[0])
                        new_end = old_start + int(new_line_tmp[1])
                        new_line_nums = range(new_start, new_end)
                        after_line_range_mark = "yes"
                    
                    if after_line_range_mark: # Source code
                        if line.startswith("-"):
                            old_source_code.append(line.replace("-", "", 1).strip())
                        if line.startswith("+"):
                            new_source_code.append(line.replace("+", "", 1).strip())
                    
                    if operation_helper:
                        operation_set_helper.append(operation_helper)
                    else: 
                        operation_set_helper.append("") # Not file level changes

                # Get warning types, line numbers and operations
                type_line_set, operation_set = self.get_change_operation(
                        old_source_code, old_line_nums, new_source_code, new_line_nums, operation_set_helper)   
                
                # Represent to json string
                operation_count = len(operation_set)         
                if operation_count > 0:
                    if operation_set.count("delete") == operation_count:
                        for old_type_line, operation in zip(type_line_set, operation_set):
                            change_event = self.represent_to_json_string(commit_id, date, file_path, 
                                    old_type_line.warning_type, old_type_line.line_number, operation)
                            change_events_file_level.append(change_event)
                    elif operation_set.count("add") == operation_count:
                        for new_type_line, operation in zip(type_line_set, operation_set):
                            change_event = self.represent_to_json_string(commit_id, date, file_path, 
                                    new_type_line.warning_type, new_type_line.line_number, operation)
                            change_events_file_level.append(change_event)
                    else:
                        for type_line, operation in zip(type_line_set, operation_set):
                            if operation == "delete":
                                change_event = self.represent_to_json_string(commit_id, date, file_path, 
                                        type_line.warning_type, type_line.line_number, operation)
                            elif operation == "add":
                                change_event = self.represent_to_json_string(commit_id, date, file_path, 
                                    type_line.warning_type, type_line.line_number, operation)
                            elif operation == "nochange":
                                pass
                            else: # tricky
                                tricky_recorder = join(self.log_result_folder, "tricky_recorder.txt")
                                with open(tricky_recorder, "a") as f:
                                    f.writelines(block)

                            change_events_file_level.append(change_event)
            all_change_events.append({"# S" + str(all_index) : change_events_file_level})
            all_index+=1
        return all_change_events # commit level

    def write_to_json_file(self, output, all_change_events):
        with open(output,"a", newline="\n") as ds:
            json.dump(all_change_events, ds, indent=4, ensure_ascii=False)
        ds.close()

    def main(self):
        all_commit_block = self.get_commit_block()
        all_change_events = self.represent_log_result_to_json(all_commit_block)
        json_file = join(self.log_result_folder, "history_latest_commit.json")
        self.write_to_json_file(json_file, all_change_events)
