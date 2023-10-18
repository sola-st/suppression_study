import csv
from os.path import join

class SpecificNumericMap():
    def __init__(self, specific, numeric):
        self.specific = specific
        self.numeric = numeric


def get_specific_numeric_type_map_csv_from_page_source():
    # original_page_source is obtained from Pylint documentation
    original_page_source = join("data", "results", "specific_numeric_type_map.txt")
    specific_numeric_type_csv = original_page_source.replace(".txt", ".csv")
    maps = []

    with open(original_page_source, "r") as f:
        lines = f.readlines()
    for line in lines:
        if "/" in line:
            tmp = line.split("/")
            specific = tmp[0].strip()
            numeric = tmp[1].strip()
            maps.append([specific, numeric])

    with open(specific_numeric_type_csv, 'w') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerows(maps)

def get_specific_numeric_type_map_list():
    specific_numeric_type_csv = join("data", "results", "specific_numeric_type_map.csv")
    maps = set()
    with open(specific_numeric_type_csv, "r") as f:
        reader = csv.reader(f)
        for s in reader:
            maps.add(SpecificNumericMap(s[0], s[1]))
    return maps
