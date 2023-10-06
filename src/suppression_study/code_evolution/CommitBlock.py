from suppression_study.code_evolution.ChangeEvent import ChangeEvent, get_change_event_dict
from suppression_study.suppression.FormatSuppressionCommon import get_suppression_from_source_code


class CommitBlock:
    def __init__(self, commit_block, suppressor, target_raw_warning_type):
        self.commit_block = commit_block
        self.suppressor = suppressor
        self.target_raw_warning_type = target_raw_warning_type # single warning type

    def from_commit_block_to_add_event(self):
        '''
        Represent git log results(commit_block) to dict,
        and then pass it to helper class to get the instance
        '''
        commit_id = ""
        date = ""
        file_path = ""
        after_line_range_mark = ""
        old_hunk_line_range = []
        new_hunk_line_range = []
        old_source_code = []
        new_source_code = []
        operation_helper = ""

        for line in self.commit_block:
            # Extract metadata from commit_block
            if line.startswith("commit "):  # Commit
                commit_id = line.split(" ")[1].strip()[:8]
            elif line.startswith("Date:"):  # Date
                date = line.split(":", 1)[1].strip()
            elif line.startswith("--- /dev/null"):  # File not exists in old commit
                operation_helper = "file add"  # Only able to report "file add", not "file delete"
            elif line.startswith("+++"):  # File path in new commit
                file_path = line.split("/", 1)[1].strip()
            elif line.startswith("@@ "):  # Changed hunk
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

            if after_line_range_mark:  # Source code
                if line.startswith("-"):
                    old_source_code.append(line.replace("-", "", 1).strip())
                if line.startswith("+"):
                    new_source_code.append(line.replace("+", "", 1).strip())
        # read commit block done
        
        '''
        check if suppression exists in old commit
        all the names with "_from_code" indicates the results extracted from source code
        all the names with "_from_grep" indicates the results from grep suppression

        self.raw_warning_types are warning types in one suppression line
        '''
        suppression_exists_in_old_mark = False # default set as no suppression in old commit
        for code, line_num in zip(old_source_code, old_hunk_line_range):
            suppression_text_from_code = get_suppression_from_source_code(comment_symbol, code)
            if suppression_text_from_code: 
                if self.target_raw_warning_type in suppression_text_from_code:
                    suppression_exists_in_old_mark = True
                    break
        
        if suppression_exists_in_old_mark == False:
            add_events = []
            # no suppression in old commit, check if suppression exists in new commit
            # gitlog results start from newest histories
            suppression_line_number = None
            comment_symbol = "#"
            # get line number for add event
            for code, line_num in zip(new_source_code, new_hunk_line_range):
                suppression_text_from_code = get_suppression_from_source_code(comment_symbol, code)
                if suppression_text_from_code:
                    if self.target_raw_warning_type in suppression_text_from_code:
                        suppression_line_number = line_num
                        break

            if suppression_line_number != None:        
                operation = "add"
                if operation_helper: # can be "file add"
                    operation = operation_helper

                suppression_text = ""
                if self.suppressor == "# pylint: ":
                    suppression_text = f"{self.suppressor} disable={self.target_raw_warning_type}"
                else:  # suppressor: type: ignore from mypy
                    if self.target_raw_warning_type == "ignore": # raw type of suppression "# type: ignore" was set to "ignore"
                        suppression_text = f"# type :{self.target_raw_warning_type}"
                    else:
                        suppression_text = f"{self.suppressor}[{self.target_raw_warning_type}]"
        
                add_event_object = ChangeEvent(
                    commit_id, date, file_path, suppression_text, suppression_line_number, operation
                )
                add_event_ready_to_json = get_change_event_dict(add_event_object)
                add_events.append(add_event_ready_to_json)
            return add_events
        else:
            return None
