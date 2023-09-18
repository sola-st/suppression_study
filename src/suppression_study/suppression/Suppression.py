import csv


class Suppression():
    def __init__(self, path, text, line):
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
            raise ValueError(f"Unknown suppression type: {self.text}")


def read_suppressions_from_file(csv_file):
    suppressions = set()
    with open(csv_file, "r") as f:
        reader = csv.reader(f)
        for s in reader:
            suppressions.add(Suppression(s[0], s[1], int(s[2])))
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
        '''
        Suppression examples:
        # pylint: disable= no-member, arguments-differ, invalid-name
        # type: ignore[assignment]
        '''
        if "=" in suppression_text:  # Pylint
            raw_warning_type = suppression_text.split("=")[1]
            raw_warning_types = raw_warning_types_accumulator(raw_warning_type, raw_warning_types)
        elif "(" in suppression_text:  # Mypy
            raw_warning_type = suppression_text.split("(")[1].replace(")", "")
            raw_warning_types = raw_warning_types_accumulator(raw_warning_type, raw_warning_types)
        elif "[" in suppression_text:  # Mypy
            raw_warning_type = suppression_text.split("[")[1].replace("]", "")
            raw_warning_types = raw_warning_types_accumulator(raw_warning_type, raw_warning_types)
        else:
            # Could be: # type: ignore
            if suppression_text == "# type: ignore":
                suppression_text = "ignore"
            raw_warning_types.append(suppression_text)

    return raw_warning_types  # all raw warning type in specified csv_file

def raw_warning_types_accumulator(raw_warning_type, raw_warning_types):
    # Add extracted warning types to raw_warning_types
    if "," in raw_warning_type:  # multiple types
        multi_raw_warning_type_tmp = raw_warning_type.split(",")
        multi_raw_warning_type = [warning_type.strip() for warning_type in multi_raw_warning_type_tmp]
        raw_warning_types.extend(multi_raw_warning_type)
    else:
        raw_warning_types.append(raw_warning_type)

    return raw_warning_types
