from suppression_study.code_evolution.ChangeEvent import ChangeEvent, get_change_event_dict
from suppression_study.suppression.FormatSuppressionCommon import get_suppression_from_source_code


class CommitBlock:
    def __init__(self, commit_block, suppressor, target_raw_warning_type, current_file):
        self.commit_block = commit_block
        self.suppressor = suppressor
        self.target_raw_warning_type = target_raw_warning_type # single warning type
        self.current_file = current_file # if merge commit, this is the file path of the added suppression

        self.commit_id = ""
        self.date = ""
        self.file_path = ""
        self.old_hunk_line_range = []
        self.new_hunk_line_range = []
        self.old_source_code = []
        self.new_source_code = []
        self.operation_helper = ""

    def from_single_commit_block_to_add_event(self, last_commit_block_mark=False):
        '''
        Represent git log results(commit_block) to dict,
        and then pass it to helper class to get the instance
        '''
        after_line_range_mark = ""

        for line in self.commit_block:
            # Extract metadata from commit_block
            if line.startswith("commit "):  # Commit
                self.commit_id = line.split(" ")[1].strip()[:8]
            elif line.startswith("Date:"):  # Date
                self.date = line.split(":", 1)[1].strip()
            elif line.startswith("Merge:"):
                self.operation_helper = "merge add"
            elif line.startswith("--- /dev/null"):  # File not exists in old commit
                self.operation_helper = "file add"  # Only able to report "file add", not "file delete"
            elif line.startswith("+++"):  # File path in new commit
                self.file_path = line.split("/", 1)[1].strip()
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
                self.old_hunk_line_range = range(old_start, old_end)

                new_line_tmp = tmp[2].replace("+", "").split(",")
                new_start = int(new_line_tmp[0])
                new_end = new_start + int(new_line_tmp[1])
                self.new_hunk_line_range = range(new_start, new_end)
                after_line_range_mark = "yes"

            if after_line_range_mark:  # Source code
                if line.startswith("-"):
                    self.old_source_code.append(line.replace("-", "", 1).strip())
                if line.startswith("+"):
                    self.new_source_code.append(line.replace("+", "", 1).strip())
        # read commit block done
        add_event = self.get_add_event(last_commit_block_mark)
        return add_event

    def get_add_event(self, last_commit_block_mark):
        # for merge commit
        if self.operation_helper == "merge add":
            suppression_text = self.get_suppression_text()
            suppression_line_number = "merge unknown"
            add_event_object = ChangeEvent(
                    self.commit_id, self.date, self.current_file, suppression_text, suppression_line_number, self.operation_helper)
            add_event_ready_to_json = get_change_event_dict(add_event_object)
            if last_commit_block_mark:
                return add_event_ready_to_json
            else:
                add_event_ready_to_json.update(backup="backup")
                return add_event_ready_to_json
        
        # for normal commit (not merge commit)
        '''
        check if suppression exists in old commit
        all the names with "_from_code" indicates the results extracted from source code
        all the names with "_from_grep" indicates the results from grep suppression

        self.raw_warning_types are warning types in one suppression line
        '''
        comment_symbol = "#"
        suppression_exists_in_old_mark = False # default set as no suppression in old commit
        for code, line_num in zip(self.old_source_code, self.old_hunk_line_range):
            suppression_text_from_code = str(get_suppression_from_source_code(comment_symbol, code))
            if suppression_text_from_code: 
                if self.target_raw_warning_type in suppression_text_from_code:
                    suppression_exists_in_old_mark = True
                    break
        
        if suppression_exists_in_old_mark == False:
            # no suppression in old commit, check if suppression exists in new commit
            # gitlog results start from newest histories
            suppression_line_number = None
            # get line number for add event
            for code, line_num in zip(self.new_source_code, self.new_hunk_line_range):
                suppression_text_from_code = str(get_suppression_from_source_code(comment_symbol, code))
                if suppression_text_from_code:
                    if self.target_raw_warning_type in suppression_text_from_code:
                        suppression_line_number = line_num
                        break

            if suppression_line_number != None:        
                operation = "add"
                if self.operation_helper: # can be "file add"
                    operation = self.operation_helper
                suppression_text = self.get_suppression_text()
                add_event_object = ChangeEvent(
                    self.commit_id, self.date, self.file_path, suppression_text, suppression_line_number, operation)
                add_event_ready_to_json = get_change_event_dict(add_event_object)
                return add_event_ready_to_json
            else:
                return None
        else:
            return None
        
    def get_suppression_text(self):
        suppression_text = ""
        if self.suppressor == "# pylint:":
            suppression_text = f"{self.suppressor} disable={self.target_raw_warning_type}"
        else:  # suppressor: type: ignore from mypy
            if self.target_raw_warning_type == "ignore": # raw type of suppression "# type: ignore" was set to "ignore"
                suppression_text = f"# type :{self.target_raw_warning_type}"
            else:
                suppression_text = f"{self.suppressor}[{self.target_raw_warning_type}]"
        return suppression_text
