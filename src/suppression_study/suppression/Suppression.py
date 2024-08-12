import csv
import re
from typing import List


class Suppression():
    def __init__(self, path: str, text: str, line: int):
        assert type(line) == int
        self.path = path
        self.text = text
        self.line = line

    def __hash__(self):
        return hash((self.path, self.text, self.line))

    def __eq__(self, __value: object) -> bool:
        return self.path == __value.path and self.text == __value.text and self.line == __value.line

    def get_checker(self):
        if self.text.startswith("# type: ignore"):
            return "mypy"
        elif self.text.startswith("# pylint:"):
            return "pylint"
        else:
            # raise ValueError(f"Unknown suppression type: {self.text}")
            return None

    def get_short_names(self) -> List[str]:
        """
        Heuristically extracts a short description of the kind(s) of 
        suppressed warnings. Returns a list of strings, which will contain
        multiple short names if the suppression is for multiple kinds of warnings.
        """
        if self.text.startswith("# type: ignore"):
            # mypy
            if self.text == "# type: ignore":
                return ["all (M)"]
            elif "ignore[" in self.text:
                m = re.match(r"# type: ignore\[(.*)\].*", self.text)
                if m:
                    return [f"{m.groups()[0]} (M)"]
        elif self.text.startswith("# pylint:"):
            # pylint
            m = re.match(r"# pylint: *disable.*=(.*)", self.text)
            if m:
                kind_text = m.groups()[0]
                if "," not in kind_text:
                    return [kind_text]
                else:
                    parts = kind_text.split(",")
                    return [f"{part.strip().rstrip()}" for part in parts]
            else:
                if re.match(r"# pylint: *disable-all*", self.text):
                    return ["all"]
                else:
                    print(f"Unknown pylint suppression: {self.text}")

        return [self.text]


# def read_suppressions_from_file(csv_file): # unfixed order
#     suppressions = set()
#     with open(csv_file, "r") as f:
#         reader = csv.reader(f)
#         for s in reader:
#             suppressions.add(Suppression(s[0], s[1], int(s[2])))
#     return suppressions

def read_suppressions_from_file(csv_file): # to fix the order of suppressions
    suppressions = []
    with open(csv_file, "r") as f:
        reader = csv.reader(f)
        for s in reader:
            suppressions.append(Suppression(s[0], s[1], int(s[2])))
    return suppressions


def get_suppression_text_from_file(csv_file):
    with open(csv_file, "r") as f:
        reader = csv.reader(f)
        # Line format: [path, suppression, line number]
        # eg,. src/flask/globals.py	# type: ignore[assignment]	48
        # Here the suppression_texts stores a list of suppression["text"],
        # eg,. suppression["text"] : "# type: ignore[assignment]"
        suppression_texts = [row[1] for row in reader]
        return suppression_texts


def get_raw_warning_type(csv_file):
    '''
    Get raw warning types from suppression_texts
    eg,. Suppression text: # type: ignore[assignment]
         Raw warning type: assignment
    '''
    raw_warning_types = []
    suppression_texts = get_suppression_text_from_file(csv_file)
    for suppression_text in suppression_texts:
        raw_warning_type = get_raw_warning_type_from_formatted_suppression_text(suppression_text)
        raw_warning_types.append(raw_warning_type)
        
    return raw_warning_types  # all raw warning type in specified csv_file

def get_raw_warning_type_from_formatted_suppression_text(suppression_text):
    separator = ""
    if "=" in suppression_text: # Pylint
        separator = "="
    elif "[" in suppression_text: # Mypy
        separator = "["

    if separator:
        raw_warning_type = suppression_text.split(separator)[1].replace("]", "")
    else: # eg,. # type: ignore, # pylint: disable-all
        raw_warning_type = suppression_text
    return raw_warning_type
