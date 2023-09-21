"""
Helper functions used mostly by WarningSuppressionMapper.
These functions are in a separate file to avoid circular imports.
"""

from os.path import join
import csv
from suppression_study.suppression.Suppression import Suppression
from suppression_study.warnings.Warning import Warning


def write_mapping_to_csv(suppression_warning_pairs, results_dir, commit_id):
    with open(join(results_dir, f"{commit_id}_mapping.csv"), "w") as f:
        writer = csv.writer(f)
        for suppression, warning in suppression_warning_pairs:
            if warning is None:
                writer.writerow(
                    [suppression.path, suppression.text, suppression.line, "", "", ""])
            else:
                writer.writerow([suppression.path, suppression.text,
                                suppression.line, warning.path, warning.kind, warning.line])


def read_mapping_from_csv(results_dir, commit_id):
    pairs = []
    with open(join(results_dir, f"{commit_id}_mapping.csv"), "r") as f:
        reader = csv.reader(f)
        for row in reader:
            suppression = Suppression(row[0], row[1], int(row[2]))
            if row[3] == "":  # no warning for this suppression
                warning = None
            else:
                warning = Warning(row[3], row[4], int(row[5]))
            pairs.append([suppression, warning])
    return pairs


def write_suppressed_warnings_to_csv(all_suppressed_warnings, results_dir, commit_id):
    with open(join(results_dir, f"{commit_id}_suppressed_warnings.csv"), "w") as f:
        writer = csv.writer(f)
        for warning in all_suppressed_warnings:
            writer.writerow([warning.path, warning.kind, warning.line])


def write_suppression_to_csv(
        useless_suppressions, results_dir, commit_id, kind):
    with open(join(results_dir, f"{commit_id}_{kind}_suppressions.csv"), "w") as f:
        writer = csv.writer(f)
        for suppression in useless_suppressions:
            writer.writerow(
                [suppression.path, suppression.text, suppression.line])
