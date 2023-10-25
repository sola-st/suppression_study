import csv
import re


'''
These format steps can be used to format suppression from the following 3 checkers:
For Python:
    1) Pylint
    2) Mypy
'''
class FormatSuppressionCommon():

    def __init__(self, comment_symbol, raw_suppression_results, precessed_suppression_csv, specific_numeric_maps):
        self.comment_symbol = comment_symbol
        self.raw_suppression_results = raw_suppression_results
        self.precessed_suppression_csv = precessed_suppression_csv
        self.specific_numeric_maps = specific_numeric_maps

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
                    preprocessed_suppression_texts = get_suppression_from_source_code(suppressor, self.comment_symbol, 
                            code_suppression, self.specific_numeric_maps)
                    # Reorder suppression keys and combined to a whole one
                    file_path_info = raw_suppression['file_path'].replace("./", "", 1)
                    for suppression_text in preprocessed_suppression_texts:
                        writer.writerow([file_path_info, suppression_text, raw_suppression["line_number"]])

def get_suppressor(suppression_text):
    # Given the text of a suppression, return the suppressor of this suppression
    suppressor = ""
    if "pylint:" in suppression_text and "disable" in suppression_text:
        suppressor = "# pylint:"
    # elif "# type: ignore" in suppression_text:
    #     suppressor = "# type: ignore"
    # else:
    #     suppressor = None
    return suppressor
             
def get_suppression_from_source_code(suppressor, comment_symbol, code_suppression, specific_numeric_maps):
    '''
    Give a code_suppression, 
    eg,. def log_message(self, fmt, *args):  # pylint: disable=arguments-differ
    Return the preprocessed_suppression:  # pylint: disable=arguments-differ
    '''
    if suppressor == "":
        # no suppression in current code_suppression
        return [] # return preprocessed_suppression_texts
    
    '''
    Avoid impacts from # noqa, a suppression from checker flake8
    It can be mixed with pylint and mypy, 
    that is, when the two suppressions appear on the same line, both suppressions can work normally.
    eg,. # noqa # pylint: disable= no-member
        # noqa pylint: disable= no-member
        in this case, # pylint: disable= no-member still work as designed.
    Here cover these cases.
    '''
    preprocessed_suppression = ""

    if code_suppression.startswith("# noqa"): 
        tmp_check = code_suppression.split("pylint")[1]
        if comment_symbol in tmp_check:
            tmp_check = tmp_check.split(comment_symbol)[0]
        code_suppression = f"# pylint{tmp_check}"

    if not code_suppression.startswith(suppressor): # mixed with source code or start with other comments.
        suppression_content = ""
        if comment_symbol in code_suppression:
            # TODO readd mypy
            suppression_tmp = code_suppression.split("pylint:")[1]
            if comment_symbol in suppression_tmp: # comments come after suppression
                # may other comments follow, further solution in get_separated_suppressions
                suppression_content = suppressor + suppression_tmp.split(comment_symbol, 1)[0]
            else: 
                suppression_content = suppressor + suppression_tmp
            preprocessed_suppression = suppression_content
        else:
            preprocessed_suppression = None # not correct way to use pylint suppressions

    else: # starts with suppressor
        if code_suppression.count(comment_symbol) >= 2:
            # line has multiple comments 
            index_of_second_comment = [m.start() for m in re.finditer(suppressor, code_suppression)][1]
            # may other comments follow. further solution in get_separated_suppressions
            preprocessed_suppression = code_suppression[:index_of_second_comment].strip()
        else:
            preprocessed_suppression = code_suppression

    assert preprocessed_suppression != ""
    
    # further format steps, separate multiple warning types into single ones, 
    # and change numeric types with specific types
    preprocessed_suppression_texts = get_separated_suppressions(preprocessed_suppression, specific_numeric_maps)

    return preprocessed_suppression_texts

def get_separated_suppressions(suppression_text, specific_numeric_maps):
    '''
    Get single warning types and change numeric waring types to specific types
    Suppression examples:
    # pylint: disable= no-member, arguments-differ, invalid-name
    # type: ignore[assignment]

    For the example for Pylint:
        [inputs]
        suppression_text: # pylint: disable=no-member, arguments-differ
                            # pylint: disable=W0703

        [return]
        # pylint: disable=no-member
        # pylint: disable=arguments-differ
        # pylint: disable=broad-except (W0703)
    '''
    preprocessed_suppression_texts = []
    separator = ""
    raw_warning_type = ""
    suppressor_part = ""

    if "=" in suppression_text:  # Pylint
        separator = "="
    elif "(" in suppression_text:  # Mypy
        separator = "("
    elif "[" in suppression_text:  # Mypy
        separator = "["
    else: # suppression: pylint: disable-all
        if "disable-all" in suppression_text and "pylint" in suppression_text:
            raw_warning_type = "all"
            suppressor_part = "# pylint: disable"

    if separator:
        tmp = suppression_text.split(separator)
        suppressor_part = tmp[0] # eg,. # pylint: disable
        # raw waning type can a single one, or multiple
        # eg,. no-member
        # eg,. arguments-differ, invalid-name
        raw_warning_type = tmp[1].replace("]", "", 1).strip()

    last_type = ""
    multi_raw_warning_type = []
    if "," in raw_warning_type:
        multi_raw_warning_type_tmp = raw_warning_type.split(",")
        multi_raw_warning_type = [warning_type.strip() for warning_type in multi_raw_warning_type_tmp]
        last_type = multi_raw_warning_type[-1]
    else:
        multi_raw_warning_type.append(raw_warning_type)
        last_type = raw_warning_type
    
    if " " in last_type: # mixed with natural sentences
        multi_raw_warning_type[-1] = last_type.split(" ")[0]

    # let raw warning types back to suppression format
    for t in multi_raw_warning_type:
        if bool(re.search(r'\d', t)) == True:
            for specific, numeric in specific_numeric_maps.items():
                if t == numeric:
                    t = specific
                    break
                    
        if "# pylint:" in suppressor_part:
            suppression_text = f"{suppressor_part}={t}"
        else: # suppressor: type: ignore from mypy
            suppression_text = f"{suppressor_part}[{t}]"
        preprocessed_suppression_texts.append(suppression_text)

    return preprocessed_suppression_texts