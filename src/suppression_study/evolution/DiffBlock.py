from suppression_study.evolution.ChangeEvent import ChangeEvent, get_change_event_dict
from suppression_study.suppression.FormatSuppressionCommon import get_suppression_from_source_code


class DiffBlock():
    def __init__(self, next_commit, next_date, diff_contents, suppression, target_raw_warning_type):
        self.next_commit = next_commit
        self.next_date = next_date
        self.diff_contents = diff_contents
        self.suppression = suppression # target suppression
        self.target_raw_warning_type = target_raw_warning_type # target single warning type

        self.current_source_code = []
        self.next_source_code = []
        self.current_hunk_line_range = []

    def from_diff_block_to_delete_event(self):
        target_block_mark = False

        diffs = self.diff_contents.split("\n")
        diff_lines_num = len(diffs)
        diff_max_line = diff_lines_num - 1 

        for diff_line, diff_line_num in zip(diffs, range(diff_lines_num)):
            diff_line = diff_line.strip()
            if diff_line.startswith("@@"):
                if self.current_hunk_line_range:
                    delete_event_ready_to_json = self.get_delete_event()
                    return delete_event_ready_to_json

                # eg,. @@ -168,14 +168,13 @@
                tmp = diff_line.split(" ")
                current_lines_tmp = tmp[1].lstrip("-").split(",")
                start = int(current_lines_tmp[0])
                step = int(current_lines_tmp[1])
                end = start + step 
                self.current_hunk_line_range = range(start, end)
                if self.suppression.line in self.current_hunk_line_range:
                    target_block_mark = True

            if target_block_mark: # Source code
                if diff_line.startswith("+"):
                    self.next_source_code.append(diff_line.replace("+", "", 1).strip())
                if diff_line.startswith("-"):
                    self.current_source_code.append(diff_line.replace("-", "", 1).strip())

            if diff_line_num == diff_max_line: # the last diff block, the last line
                if self.current_hunk_line_range:
                    last_block_mark = True
                    delete_event_ready_to_json = self.get_delete_event(last_block_mark)
                    return delete_event_ready_to_json
                else:
                    return None # get to the end of all diff blocks, but still not find the delete
                
    def get_delete_event(self, last_block_mark=False):
        comment_symbol = "#"
        # not sure if all the code lines contains suppression, 
        # set to not check the return of get_suppression_from_source_code
        empty_check = False 

        '''
        sometimes the changed hunk includes the target line number, but no changes to the line.
        eg,.  @@ -10,2
            result = str1 + str2  # pylint: disable=W1401,W1402
            - return result
            changed hunk is from line 10 to line 11(included), but only "-" symbol to line 11, no changes to line 10
        to get more accurate results, here check if the suppression real exists in current_source_code'''
        target_warning_type_exists_in_current = False # default set as no suppression in old commit
        for code in self.current_source_code:
            suppression_text_from_code = str(get_suppression_from_source_code(comment_symbol, code, empty_check))
            if suppression_text_from_code: 
                if self.target_raw_warning_type in suppression_text_from_code:
                    target_warning_type_exists_in_current = True
                    break

        if target_warning_type_exists_in_current == True:
            # has suppression in current commit, check if suppression exists in next commit
            target_warning_type_exists_in_next = False
            for code in self.next_source_code:
                suppression_text_from_code = str(get_suppression_from_source_code(comment_symbol, code, empty_check))
                if suppression_text_from_code:
                    if self.target_raw_warning_type in suppression_text_from_code:
                        target_warning_type_exists_in_next = True
                        break

            if target_warning_type_exists_in_next == False: 
                delete_event_object = ChangeEvent(
                        self.next_commit, self.next_date, self.suppression.path, 
                        self.suppression.text, self.suppression.line, "delete")
                delete_event_ready_to_json = get_change_event_dict(delete_event_object)
                return delete_event_ready_to_json
            else: # no deletions, as the suppression included in current change hunk also in the next commit's changed hunk
                if last_block_mark == True:
                    return None
                else:
                    self.current_hunk_line_range = []
                    self.next_source_code = []
                    self.current_source_code = []
        else: # no deletions, as no delete suppression in current commit
            if last_block_mark == True:
                return None
            else:
                self.current_hunk_line_range = []
                self.next_source_code = []
                self.current_source_code = []