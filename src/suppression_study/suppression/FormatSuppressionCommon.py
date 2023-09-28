import csv
import re

'''
These format steps can be used to format suppression from the following 3 checkers:
For Python:
    1) Pylint
    2) Mypy
# For JavaScript:
#     3) ESLint
'''
class FormatSuppressionCommon():

    def __init__(self, comment_symbol, raw_suppression_results, precessed_suppression_csv):
        self.comment_symbol = comment_symbol
        self.raw_suppression_results = raw_suppression_results
        self.precessed_suppression_csv = precessed_suppression_csv

    def represent_to_dict(self):
        '''
        Represent lines in raw_suppression_results file to dicts, 
        each suppression has a dict --> the following raw_suppression : dict
        return a list (the elements in it are dicts).
        '''
        raw_suppression_dict_list = []

        with open(self.raw_suppression_results, "r") as f:
            '''
            Represent raw_suppression_results to a list with several dict elements.
            raw_suppression_results: raw results of Grep command.
            Line format:
                eg,. (Mypy) src/compare/find_max.py:7:        return 0  # type: ignore
                eg,. (Pylint) src/fake/demo.py:121:   except Exception:  # pylint: disable=broad-except
            '''
            line = f.readline()
            while line:
                ''' 
                Avoid split ":" in source code and suppression 
                eg,. ":" in # type: ignore
                eg,. ":" in except Exception:  # pylint: disable=broad-except
                '''
                splits = line.split(":", 2) 
                file_path = splits[0]
                line_number = splits[1]
                code_suppression = splits[2] # In some cases, suppression mixed with source code
                raw_suppression : dict = {
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
        '''

        with open(self.precessed_suppression_csv,"w") as d:
            writer = csv.writer(d)

            raw_suppression_dict_list =self.represent_to_dict()
            for raw_suppression in raw_suppression_dict_list:
                if "/lib" in raw_suppression['file_path']: # Hard code to exclude dir, need to manual check folder names.
                    continue
                code_suppression = raw_suppression['code_suppression']
                preprocessed_suppression = ""
    
                # Confirm suppressor
                suppressor = ""
                if "# pylint:" in code_suppression:
                    suppressor = "# pylint:"
                elif "# type: ignore" in code_suppression:
                    suppressor = "# type: ignore"
                else: 
                    suppressor = "eslint-disable"

                '''
                special preprocess to control the suppression "#noqa" from another tool, flake8
                # 2 big catagories of possible order of these suppressions and other codes 
                # 1) noqa, pylint --> need to separate this 2 comments
                # 2) pylint, noqa --> noqa will regarded as a normal comment, and been truncated
                * also can mixed with other normal comments
                  only consider the cases that the normal comment comes at the end of code_suppression
                  otherwise, the suppression itself was "suppressed" by the normal comment
                ''' 
                if code_suppression.startswith("# noqa"): 
                    tmp_check = code_suppression.split("#")
                    noqa_comment = f"#{tmp_check[1]}" # 0 is an empty split
                    code_suppression = code_suppression.replace(noqa_comment, "")
                    # then start the following normal format steps

                suppressed_suppression_mark = False # the target suppression is "suppressed" by a normal comment
                if not code_suppression.startswith(suppressor): # mixed with source code or start with other comments.
                    if code_suppression.startswith(self.comment_symbol): # start with comment_symbol, but not start with suppressor
                        suppressed_suppression_mark = True
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
                            preprocessed_suppression =  suppression_content
                        else:
                            preprocessed_suppression = raw_suppression
                else: # starts with suppressor
                    if code_suppression.count(self.comment_symbol) >= 2:
                        # line has multiple comments --> ignore everything but the first one
                        index_of_second_comment = [m.start() for m in re.finditer(self.comment_symbol, code_suppression)][1]
                        preprocessed_suppression = code_suppression[:index_of_second_comment].strip()
                    else:
                        preprocessed_suppression =  code_suppression

                if suppressed_suppression_mark == False:
                    assert preprocessed_suppression != ""

                # Reorder suppression keys and combined to a whole one
                file_path_info = raw_suppression['file_path'].replace("./", "", 1)
                writer.writerow([file_path_info, preprocessed_suppression, raw_suppression["line_number"]])
