from suppression_study.suppression.FormatSuppressionCommon import get_suppression_code_from_source


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
        comment_symbol = "#"

        for source_line, line_number in zip(self.source_code, self.hunk_line_range):
            '''
            source_line: def log_message(self, fmt, *args):  # pylint: disable=arguments-differ
            suppression_text:  # pylint: disable=arguments-differ
            '''
            if "# pylint:" in source_line or "# type: ignore" in source_line:
                suppression_text = get_suppression_code_from_source(comment_symbol, source_line)

                '''
                Multi-warning type suppression, eg,. ("unused-import", "invalid-name")
                here keep the multiple types, extract : "unused-import", "invalid-name" (line level)
                will separate to "unused-import" and "invalid-name" in class 'IdentifyChangeOperation'. (suppression level)

                The reason here keep multiple types aims to keep the feature to recognize inline changes to the suppressions.
                Change operation:
                eg,. "unused-import" -> keep
                        "invalid-name" -> delete
                ''' 
                raw_warning_type = ""
                if "(" in suppression_text:
                    raw_warning_type = suppression_text.split("(")[1].replace(")", "")
                elif "[" in suppression_text:
                    raw_warning_type = suppression_text.split("[")[1].replace("]", "")
                else:
                    raw_warning_type = suppression_text

                if "," in raw_warning_type:
                    raw_types = raw_warning_type.split(",")
                    for raw_type in raw_types:
                        raw_type = raw_type.strip()
                        if raw_type.startswith("# pylint: disable="):
                            warning_type_set.append(raw_type)
                        else:
                            warning_type_set.append(f"# pylint: disable={raw_type}")
                        line_number_set.append(line_number)
                else:
                    warning_type_set.append(suppression_text)
                    line_number_set.append(line_number)

            for warning_type, line_number in zip(warning_type_set, line_number_set):
                # warning_type can be multiple types.
                type_line = WarningTypeLine(warning_type, line_number)
                type_line_set.append(type_line)
        return type_line_set
    
