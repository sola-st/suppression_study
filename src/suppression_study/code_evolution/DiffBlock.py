from suppression_study.code_evolution.ChangeEvent import ChangeEvent


class DiffBlock():
    def __init__(self, next_commit, next_date, diff_contents, suppression):
        self.next_commit = next_commit
        self.next_date = next_date
        self.diff_contents = diff_contents
        self.suppression = suppression

    def from_diff_block_to_delete_event(self):
        current_hunk_line_range = []
        next_source_code = []
        target_block_mark = False

        diffs = self.diff_contents.split("\n")

        diff_block_num = 0
        for diff_line in diffs:
            if diff_line.startswith("@@"):
                diff_block_num+=1

        diff_block_idx = 0
        for diff_line in diffs:
            diff_line = diff_line.strip()
            if diff_line.startswith("@@"):
                diff_block_idx +=1
                if current_hunk_line_range:
                    # check if target suppressor in collected source code
                    suppression_in_next_mark = "# pylint:" in next_source_code or "# type: ignore" in next_source_code
                    if suppression_in_next_mark == False: 
                        # no suppression in the changed hunk which includes target suppression in current commit 
                        # target suppression is deleted
                        delete_event_object = ChangeEvent(self.next_commit, self.next_date, self.suppression.path, 
                                self.suppression.text, self.suppression.line, "delete")
                        return delete_event_object
                    else:
                        current_hunk_line_range = []
                        next_source_code = []

                # eg,. @@ -168,14 +168,13 @@
                tmp = diff_line.split(" ")
                current_lines_tmp = tmp[1].lstrip("+").split(",")
                start = int(current_lines_tmp[0])
                step = int(current_lines_tmp[1])
                end = start + step 
                current_hunk_line_range = range(start, end)
                if self.suppression.line in current_hunk_line_range:
                    target_block_mark = True

            if target_block_mark: # Source code
                if diff_line.startswith("+"):
                    next_source_code.append(diff_line.replace("+", "", 1).strip())
            
        if diff_block_idx == diff_block_num:
            return None # get to the end of all diff blocks, but still not find the delete