'''
Get warning types and their occurrences
Part 1: get raw warning type from suppressions
Part 2: get occurrences of the raw warning types
Expected results: csv files which records warning types and their occurrences
    1. All repository level: an overall from all repositories
    2. Single repository level: One individual csv file for a repository.
'''

from collections import Counter
import csv
import os
from os.path import join


def extract_raw_warning_type_from_suppression(grep_suppression_csv):
    '''
    Get raw warning types from suppressions
    eg,. Suppression: # type: ignore[assignment]
         Raw warning type: assignment
    '''
    raw_warning_types = []
    with open(grep_suppression_csv, "r") as f:
        reader = csv.reader(f)
        # Line format: [path, suppression, line number]
        # eg,. src/flask/globals.py	# type: ignore[assignment]	48
        suppressions = [row[1] for row in reader]
    for suppression in suppressions:
        '''
        Suppression examples:
        # pylint: disable= no-member, arguments-differ, invalid-name
        # type: ignore[assignment]
        '''
        if "=" in suppression:  # Pylint
            raw_warning_type = suppression.split("=")[1]
            raw_warning_types = raw_warning_types_accumulator(raw_warning_type, raw_warning_types)
        elif "(" in suppression:  # Mypy
            raw_warning_type = suppression.split("(")[1].replace(")", "")
            raw_warning_types = raw_warning_types_accumulator(raw_warning_type, raw_warning_types)
        elif "[" in suppression:  # Mypy
            raw_warning_type = suppression.split("[")[1].replace("]", "")
            raw_warning_types = raw_warning_types_accumulator(raw_warning_type, raw_warning_types)
        else:
            # Could be: # type: ignore
            if suppression == "# type: ignore":
                suppression = "ignore"
            raw_warning_types.append(suppression)

    return raw_warning_types  # all raw warning type in current grep_suppression_csv

def raw_warning_types_accumulator(raw_warning_type, raw_warning_types):
    # Add extracted warning types to raw_warning_types
    if "," in raw_warning_type:  # multiple types
        multi_raw_warning_type_tmp = raw_warning_type.split(",")
        multi_raw_warning_type = [warning_type.strip() for warning_type in multi_raw_warning_type_tmp]
        raw_warning_types.extend(multi_raw_warning_type)
    else:
        raw_warning_types.append(raw_warning_type)

    return raw_warning_types

def write_warning_types_occurrences(warning_type_occurrences_csv, raw_warning_types):
    # Write all warning types (raw_warning_types) and its occurrences to a csv file

    # Use Counter to count occurrences
    element_count = Counter(raw_warning_types)

    to_write = ""
    # Iterate through the Counter object and print the counts
    for element, count in element_count.items():
        to_write = f"{to_write}{element},{count}\n"

    with open(warning_type_occurrences_csv, "w") as f:
        f.write(f"warning_type,occurrences\n{to_write}")

def get_warning_type_single_repository(grep_folder, warning_type_occurrences_repo_csv):
    raw_warning_types_repo_level = []
    files = os.listdir(grep_folder)
    for file in files:
        if file.endswith(".csv"):
            # Accumulate suppression-file level extracted warning types to raw_warning_types_repo_level
            raw_warning_types = extract_raw_warning_type_from_suppression(join(grep_folder, file))
            raw_warning_types_repo_level.extend(raw_warning_types)
    # Write raw_warning_types_repo_level to warning_type_occurrences_repo_csv
    # 1 repository with 1 occurrences file
    write_warning_types_occurrences(warning_type_occurrences_repo_csv, raw_warning_types_repo_level)
    return raw_warning_types_repo_level