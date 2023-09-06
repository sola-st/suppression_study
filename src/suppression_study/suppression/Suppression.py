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
    

def read_suppressions_from_file(csv_file):
    suppressions = set()
    with open(csv_file, "r") as f:
        reader = csv.reader(f)
        for s in reader:
            suppressions.add(Suppression(s[0], s[1], int(s[2])))
    return suppressions