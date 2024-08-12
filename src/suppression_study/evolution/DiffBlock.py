from suppression_study.evolution.ChangeEvent import ChangeEvent, get_change_event_dict
from suppression_study.suppression.FormatSuppressionCommon import get_suppression_from_source_code, get_suppressor


class DiffBlock():
    def __init__(self, next_commit, next_date, diff_contents, suppression, target_raw_warning_type, specific_numeric_maps):
        self.next_commit = next_commit
        self.next_date = next_date
        self.diff_contents = diff_contents
        self.suppression = suppression # target suppression
        self.target_raw_warning_type = target_raw_warning_type # target single warning type
        self.specific_numeric_maps = specific_numeric_maps

        self.current_source_code = []
        self.next_source_code = []
        self.current_hunk_line_range = []

    def from_diff_block_to_delete_event(self):
        target_block_mark = False

        diffs = self.diff_contents.split("\n")
        diff_lines_num = len(diffs)
        diff_max_line = diff_lines_num - 1 
        mapped_line_num = self.suppression.line # the line number of the mapped suppression in next commit

        current_start = None
        current_step = 0
        target_step = 0
        for diff_line, diff_line_num in zip(diffs, range(diff_lines_num)):
            diff_line = diff_line.strip()
            if diff_line.startswith("@@"):
                if target_block_mark:
                    delete_event_ready_to_json = self.get_delete_event()
                    # actually here the returned line number should be None
                    # it records the line number where is last exists in the commit just before the deletion commit
                    if delete_event_ready_to_json:
                        return delete_event_ready_to_json, self.suppression.line  # event, mapped_line_num

                    # compute the middle statuses suppression line numbers, the suppression is not changed and line numbers may changed
                    if self.suppression.line > current_start:
                        hunk_delta = target_step - current_step
                        mapped_line_num += hunk_delta
                    else:
                        return mapped_line_num

                # eg,. @@ -168,14 +168,13 @@
                tmp = diff_line.split(" ")
                current_lines_tmp = tmp[1].lstrip("-")
                if "," in current_lines_tmp:
                    current_lines_tmp = current_lines_tmp.split(",")
                    current_start = int(current_lines_tmp[0])
                    current_step = int(current_lines_tmp[1])
                else:
                    current_start = int(current_lines_tmp)
                    # current_step = 0 
                end = current_start + current_step 
                self.current_hunk_line_range = range(current_start, end)
                if self.suppression.line in self.current_hunk_line_range:
                    target_block_mark = True
                target_tmp = tmp[2].lstrip("+")
                if "," in target_tmp:
                    target_step = int(target_tmp.split(",")[1])
                # else: target_step = 0

            if target_block_mark: # Source code
                if diff_line.startswith("+"):
                    self.next_source_code.append(diff_line.replace("+", "", 1).strip())
                if diff_line.startswith("-"):
                    self.current_source_code.append(diff_line.replace("-", "", 1).strip())

            if diff_line_num == diff_max_line: # the last diff block, the last line
                if target_block_mark:
                    delete_event_ready_to_json = self.get_delete_event()
                    if delete_event_ready_to_json:
                        return delete_event_ready_to_json, self.suppression.line  # event, mapped_line_num
                    
                if self.suppression.line > current_start:
                    hunk_delta = target_step - current_step
                    mapped_line_num += hunk_delta
                
                return mapped_line_num

                
    def get_delete_event(self):
        comment_symbol = "#"
        '''
        sometimes the changed hunk includes the target line number, but no changes to the line.
        eg,.  @@ -10,2
            result = str1 + str2  # pylint: disable=W1401,W1402
            - return result
            changed hunk is from line 10 to line 11(included), but only "-" symbol to line 11, no changes to line 10
        to get more accurate results, here check if the suppression real exists in current_source_code'''
        target_warning_type_exists_in_current = False # default set as no suppression in old commit
        suppression_text_from_code_in_current = None
        for code in self.current_source_code:
            suppressor = get_suppressor(code)
            if suppressor: # make sure suppression in current code
                suppression_text_from_code_in_current = str(get_suppression_from_source_code(suppressor, 
                        comment_symbol, code, self.specific_numeric_maps))
                if suppression_text_from_code_in_current: 
                    if self.target_raw_warning_type in suppression_text_from_code_in_current:
                        target_warning_type_exists_in_current = True
                        break

        if target_warning_type_exists_in_current == True:
            # has suppression in current commit, check if suppression exists in next commit
            target_warning_type_exists_in_next = False
            for code in self.next_source_code:
                suppressor = get_suppressor(code)
                if suppressor: 
                    suppression_text_from_code_in_next = str(get_suppression_from_source_code(suppressor, 
                            comment_symbol, code, self.specific_numeric_maps))
                    if suppression_text_from_code_in_next and suppression_text_from_code_in_current == suppression_text_from_code_in_next:
                        if self.target_raw_warning_type in suppression_text_from_code_in_next:
                            # if needed, here we can extract the line number of suppression where it is deleted.
                            target_warning_type_exists_in_next = True
                            break

            if target_warning_type_exists_in_next == False: 
                delete_event_object = ChangeEvent(
                        self.next_commit, self.next_date, self.suppression.path, 
                        self.suppression.text, self.suppression.line, "delete")
                delete_event_ready_to_json = get_change_event_dict(delete_event_object)
                return delete_event_ready_to_json
            else: # no deletions, as the suppression included in current change hunk also in the next commit's changed hunk
                self.current_hunk_line_range = []
                self.next_source_code = []
                self.current_source_code = []
                return None
        else: # no deletions, as no suppression in current hunk
            # generally, will not happen, to handle the inaccurate report from diff
            self.current_hunk_line_range = []
            self.next_source_code = []
            self.current_source_code = []
            return None