import csv
import re


'''
These format steps can be used to format suppression from the following 3 checkers:
For Python:
    1) Pylint
    2) Mypy
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

            raw_suppression_dict_list = self.represent_to_dict()
            for raw_suppression in raw_suppression_dict_list:
                if "/lib" in raw_suppression['file_path']: # Hard code to exclude dir, need to manual check folder names.
                    continue
                code_suppression = raw_suppression['code_suppression']
                suppressor = get_suppressor(code_suppression)
                if suppressor:
                    preprocessed_suppression_texts = get_suppression_from_source_code(suppressor, self.comment_symbol, code_suppression)
                    # Reorder suppression keys and combined to a whole one
                    file_path_info = raw_suppression['file_path'].replace("./", "", 1)
                    for suppression_text in preprocessed_suppression_texts:
                        writer.writerow([file_path_info, suppression_text, raw_suppression["line_number"]])

def get_suppressor(suppression_text):
    # Given the text of a suppression, return the suppressor of this suppression
    suppressor = ""
    if "# pylint:" in suppression_text and "disable" in suppression_text:
        suppressor = "# pylint:"
    elif "# type: ignore" in suppression_text:
        suppressor = "# type: ignore"
    else:
        suppressor = None
    return suppressor
             
def get_suppression_from_source_code(suppressor, comment_symbol, code_suppression):
    '''
    Give a code_suppression, 
    eg,. def log_message(self, fmt, *args):  # pylint: disable=arguments-differ
    Return the preprocessed_suppression:  # pylint: disable=arguments-differ
    '''
    preprocessed_suppression = ""

    '''
    Avoid impacts from # noqa, a suppression from checker flake8
    It can be mixed with pylint and mypy, 
    that is, when the two suppressions appear on the same line, both suppressions can work normally.
    eg,. # noqa # pylint: disable= no-member
        in this case, # pylint: disable= no-member still work as designed.
    
    To prevent subsequent processing from treating it as a regular comment, 
        a regular comment will invalidate pylint suppression.
    Here remove # noqa suppression.
    '''
    if code_suppression.startswith("# noqa"): 
        tmp_check = code_suppression.split("#")
        noqa_comment = f"#{tmp_check[1]}" # 0 is an empty split
        code_suppression = code_suppression.replace(noqa_comment, "")
        # then start the following normal format steps

    suppressed_suppression_mark = False # the target suppression is "suppressed" by a normal comment
    if not code_suppression.startswith(suppressor): # mixed with source code or start with other comments.
        if code_suppression.startswith(comment_symbol): # start with comment_symbol, but not start with suppressor
            suppressed_suppression_mark = True
            pass # a comment contains suppress comment, suppress comment is suppressed in source code
        else: # mixed with source code, source code comes first. may with another comment at the end.
            suppression_content = ""
            if comment_symbol in code_suppression:
                if code_suppression.count(comment_symbol) >= 1: # 1 comment_symbol for suppression
                    suppression_tmp = code_suppression.split(suppressor)[1]
                    if comment_symbol in suppression_tmp: # comments come after suppression
                        suppression_content = suppressor + suppression_tmp.split(comment_symbol, 1)[0]
                    else: # count(self.comment_symbol) == 1
                        suppression_content = suppressor + suppression_tmp
                preprocessed_suppression = suppression_content
            else:
                preprocessed_suppression = None 

    else: # starts with suppressor
        if code_suppression.count(comment_symbol) >= 2:
            # line has multiple comments --> ignore everything but the first one
            index_of_second_comment = [m.start() for m in re.finditer(comment_symbol, code_suppression)][1]
            preprocessed_suppression = code_suppression[:index_of_second_comment].strip()
        else:
            preprocessed_suppression = code_suppression

    if suppressed_suppression_mark == False:
        assert preprocessed_suppression != ""
    
    # further format steps, separate multiple warning types into single ones
    preprocessed_suppression_texts = []
    if "," in preprocessed_suppression: # multiple warning types
        preprocessed_suppression_texts = get_separated_suppressions(preprocessed_suppression)
    else:
        preprocessed_suppression_texts.append(preprocessed_suppression)

    return preprocessed_suppression_texts

def get_separated_suppressions(suppression_text):
    '''
    Suppression examples:
    # pylint: disable= no-member, arguments-differ, invalid-name
    # type: ignore[assignment]

    For the example for Pylint:
        [inputs]
        suppression_text: # pylint: disable= no-member, arguments-differ, invalid-name

        [return]
        # pylint: disable=no-member
        # pylint: disable=arguments-differ
        # pylint: disable=invalid-name
    '''
    preprocessed_suppression_texts = []
    separator = ""

    if "=" in suppression_text:  # Pylint
        separator = "="
    elif "(" in suppression_text:  # Mypy
        separator = "("
    elif "[" in suppression_text:  # Mypy
        separator = "["

    tmp = suppression_text.split(separator)
    suppressor_part = tmp[0] # eg,. # pylint: disable
    raw_warning_type = tmp[1].replace("]", "", 1) # eg,. no-member, arguments-differ, invalid-name
    
    multi_raw_warning_type_tmp = raw_warning_type.split(",")
    multi_raw_warning_type = [warning_type.strip() for warning_type in multi_raw_warning_type_tmp]

    # let raw warning types back to suppression format
    for t in multi_raw_warning_type:
        if "# pylint:" in suppressor_part:
            suppression_text = f"{suppressor_part}={t}"
        else: # suppressor: type: ignore from mypy
            suppression_text = f"{suppressor_part}[{t}]"
        preprocessed_suppression_texts.append(suppression_text)

    return preprocessed_suppression_texts
