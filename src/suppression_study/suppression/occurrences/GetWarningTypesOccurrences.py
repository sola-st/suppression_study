'''
Get warning types and their occurrences (in suppressions or in warnings)
Part 1: get raw warning type
Part 2: get occurrences of the raw warning types
Expected results: csv files which records warning types and their occurrences
    1. All repository level: an overall from all repositories
    2. Single repository level: One individual csv file for a repository.
'''

from collections import Counter
import os
from os.path import join

from suppression_study.suppression.Suppression import get_raw_warning_type


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
            raw_warning_types = get_raw_warning_type(join(grep_folder, file))
            raw_warning_types_repo_level.extend(raw_warning_types)
    # Write raw_warning_types_repo_level to warning_type_occurrences_repo_csv
    # 1 repository with 1 occurrences file
    write_warning_types_occurrences(warning_type_occurrences_repo_csv, raw_warning_types_repo_level)
    return raw_warning_types_repo_level