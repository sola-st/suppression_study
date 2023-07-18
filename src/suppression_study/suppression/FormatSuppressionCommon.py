'''
This script can be used to format suppression from the following 3 checkers:
For Python:
    1) Pylint
    2) Mypy
For JavaScript:
    3) ESLint
'''
class FormatSuppressionCommon():

    def __init__(self, comment_symbol, raw_suppression_results, precessed_suppression_csv):
        self.comment_symbol = comment_symbol
        self.raw_suppression_results = raw_suppression_results
        self.precessed_suppression_csv = precessed_suppression_csv

    def represent_to_dict(self):
        '''
        Represent lines in raw_suppression_results file to dict,
        return a list.
        '''
        raw_suppression_dict_list = []

        with open(self.raw_suppression_results, "r") as f:
            '''
            Represent raw_suppression_results to a list with several dict elements.
            raw_suppression_results: raw results of Grep command.
            Line format:
                eg,. (Mypy) src/compare/find_max.py:7:        return 0  # type: ignore
            '''
            line = f.readline()
            while line:
                splits = line.split(":", 2) # Avoid replace ":" in source annotations and comments.
                file_path = splits[0]
                line_number = splits[1]
                code_suppression = splits[2] # In some cases, suppression mixed with source code
                raw_suppression = {
                        "file_path" : file_path,
                        "line_number" : line_number,
                        "code_suppression" : str(code_suppression).strip()
                }
                raw_suppression_dict_list.append(raw_suppression)
                line=f.readline()

        return raw_suppression_dict_list

     
    def format_suppression_common(self):
        '''
        Python:
        1) comments start with "#"
        2) suppression comments can mixed with source code, source code comes first.
        3) cannot mixed with other comments
        Has several representation ways:

        Pylint:
        --1 # pylint: 
        --2 source code # pylint: 

        Mypy:
        --1 source code # type: 
        --1 source code # type: # other comments (eg,. # noqa)


        JavaScript:
        1) comments start with "//" or "/*"
        2) can follow with natural language description (relatively complicated to format)
        3) Flow cannot mixed with source code
        Has 2 representation ways:
        eslint:
        --1 // or /* eslint (description or not)
        --2 source code // or /* eslint (description or not)
        '''

        csv_txt = ""

        raw_suppression_dict_list =self.represent_to_dict()
        for raw_suppression in raw_suppression_dict_list:
            if "/lib" in raw_suppression['file_path']: # Hard code to exclude dir, need to manual check folder names.
                continue
            code_suppression = raw_suppression['code_suppression']
            processed_suppression = ""
 
            # Confirm suppressor
            suppressor = ""
            if "# pylint:" in code_suppression:
                suppressor = "# pylint:"
            elif "# type: ignore" in code_suppression:
                suppressor = "# type: ignore"
            else: 
                suppressor = "eslint-disable"

            if not code_suppression.startswith(suppressor): # mixed with source code or start with other comments.
                if code_suppression.startswith(self.comment_symbol): # start with comment_symbol, but not start with suppressor
                    pass # a comment contains suppress comment, suppress comment is suppressed in source code
                else: # mixed with source code, source code comes first. may with another comment at the end.
                    suppression_content = ""
                    if self.comment_symbol:
                        # what about comment symbol in source code? haven't found any cases yet
                        if code_suppression.count(self.comment_symbol) >= 1: # 1 comment_symbol for suppression
                            suppression_tmp = code_suppression.split(suppressor)[1]
                            if self.comment_symbol in suppression_tmp: # comments come after suppression
                                suppression_content = suppressor + suppression_tmp.split(self.comment_symbol, 1)[0]
                            else: # self.comment_symbol == 1
                                suppression_content = suppressor + suppression_tmp
                        processed_suppression =  "\"" + suppression_content + "\""
                    else:
                        processed_suppression = "\"" + raw_suppression + "\""
            else: # starts with suppressor
                if code_suppression.count(self.comment_symbol) >= 2: # one for suppression
                    content_filter2 = code_suppression.split(self.comment_symbol, 1)[1].strip()
                    if content_filter2.startswith(suppressor): # only the first comment be suppression will work
                        suppression_content = self.comment_symbol + " " + content_filter2
                        processed_suppression =  "\"" + suppression_content + "\""
                else:
                    processed_suppression =  "\"" + code_suppression + "\""

            # Reorder suppression keys and combined to a whole one
            processed_info = raw_suppression['file_path'].replace("./", "", 1) + "," + processed_suppression + "," + raw_suppression['line_number']
            csv_txt = csv_txt + processed_info + "\n"

        with open(self.precessed_suppression_csv,"w") as d:
            d.writelines(csv_txt)