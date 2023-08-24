import csv


class Warning():
    def __init__(self, path, kind, line):
        self.path = path
        self.kind = kind
        self.line = line

    def __hash__(self):
        return hash((self.path, self.kind, self.line))

    def __eq__(self, __value: object) -> bool:
        return self.path == __value.path and self.kind == __value.kind and self.line == __value.line
    

def read_warning_from_file(csv_file):
    warnings = set()
    with open(csv_file, "r") as f:
        reader = csv.reader(f)
        for w in reader:
            warnings.add(Warning(w[0], w[1], int(w[2])))
    return warnings 