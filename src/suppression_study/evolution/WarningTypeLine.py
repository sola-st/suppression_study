class WarningTypeLine():
    def __init__(self, warning_type, line_number):
        self.warning_type = warning_type
        self.line_number = line_number


class GetWarningTypeLine():
    def __init__(self, source_code, hunk_line_range):
        self.source_code = source_code
        self.hunk_line_range = hunk_line_range

    def get_warning_type_line(self):
        '''
        With extracted changed line range and source code, locate suppression, and get warning type and line number.
        Return a list with warning types and line numbers.
        '''
        warning_type_set = []
        line_number_set = []
        type_line_set = []
        suppressor_set = ["# pylint:", "# type:"]
        comment_symbol = "#"

        for source_line, line_number in zip(self.source_code, self.hunk_line_range):
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
                                    suppression_content = the_suppressor + suppression_tmp.split(comment_symbol, 1)[0]
                                else: 
                                    suppression_content = the_suppressor + suppression_tmp
                            '''
                            Multi-warning type suppression, eg,. ("unused-import", "invalid-name")
                            here keep the multiple types, extract : "unused-import", "invalid-name" (line level)
                            will separate to "unused-import" and "invalid-name" in class 'IdentifyChangeOperation'. (suppression level)

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
    
