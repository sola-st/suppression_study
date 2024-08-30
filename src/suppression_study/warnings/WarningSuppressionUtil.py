"""
Helper functions used mostly by WarningSuppressionMapper.
These functions are in a separate file to avoid circular imports.
"""

import os
from os.path import join
import csv
from suppression_study.suppression.Suppression import Suppression
from suppression_study.warnings.Warning import Warning


def write_mapping_to_csv(suppression_warning_pairs, results_dir, commit_id, file_specific=None):
    if suppression_warning_pairs == None:
        suppression_warning_pairs = []
    to_write_file = join(results_dir, f"{commit_id}_mapping.csv")
    if file_specific:
        to_write_file = join(results_dir, f"{commit_id}_mapping_{file_specific}.csv")
    with open(to_write_file, "w") as f:
        writer = csv.writer(f)
        for suppression, warning in suppression_warning_pairs:
            if warning is None:
                writer.writerow(
                    [suppression.path, suppression.text, suppression.line, "", "", ""])
            else:
                writer.writerow([suppression.path, suppression.text,
                                suppression.line, warning.path, warning.kind, warning.line])


def read_mapping_from_csv(file: str = None, results_dir=None, commit_id=None):
    if file is None:
        file = join(results_dir, f"{commit_id}_mapping.csv")

    pairs = []
    if os.path.exists(file):
        with open(file, "r") as f:
            reader = csv.reader(f)
            for row in reader:
                suppression = Suppression(row[0], row[1], int(row[2]))
                if row[3] == "":  # no warning for this suppression
                    warning = None
                else:
                    warning = Warning(row[3], row[4], int(row[5]))
                pairs.append([suppression, warning])
    return pairs


def write_suppressed_warnings_to_csv(all_suppressed_warnings, results_dir, commit_id, file_specific=None):
    file_to_write = join(results_dir, f"{commit_id}_suppressed_warnings.csv")
    if file_specific:
        file_to_write = join(results_dir, f"{commit_id}_suppressed_warnings_{file_specific}.csv")
    with open(file_to_write, "w") as f:
        writer = csv.writer(f)
        for warning in all_suppressed_warnings:
            writer.writerow([warning.path, warning.kind, warning.line])


def write_suppression_to_csv(
        useless_suppressions, results_dir, commit_id, kind, file_specific=None):
    file_to_write = join(results_dir, f"{commit_id}_{kind}_suppressions.csv")
    if file_specific:
        file_to_write = join(results_dir, f"{commit_id}_{kind}_suppressions_{file_specific}.csv")

    with open(file_to_write, "w") as f:
        writer = csv.writer(f)
        for suppression in useless_suppressions:
            writer.writerow(
                [suppression.path, suppression.text, suppression.line])
