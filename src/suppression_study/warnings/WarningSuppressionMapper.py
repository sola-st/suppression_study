'''
For a given commit, computes a mapping between warnings and suppressions.
'''

from typing import List
import argparse
import os
from os.path import join
from git.repo import Repo
from suppression_study.suppression.GrepSuppressionPython import GrepSuppressionPython
from suppression_study.checkers.GetPylintWarnings import main as get_pylint_warnings
from suppression_study.checkers.GetMypyWarnings import main as get_mypy_warnings
from suppression_study.suppression.SuppressionRemover import SuppressionRemover
from suppression_study.warnings.Warning import read_warning_from_file
from suppression_study.suppression.Suppression import Suppression, read_suppressions_from_file
from suppression_study.checkers.GetSuppressedPylintWarnings import main as get_suppressed_pylint_warnings
from suppression_study.warnings.WarningSuppressionUtil import write_mapping_to_csv, write_suppressed_warnings_to_csv, write_suppression_to_csv


parser = argparse.ArgumentParser(
    description="Compute mapping between warnings and suppressions")
parser.add_argument(
    "--repo_dir", help="Directory with the repository to analyze", required=True)
parser.add_argument(
    "--commit_id", help="Commit hash to analyze", required=True)
parser.add_argument("--checker", help="The checker to run",
                    required=True, choices=["mypy", "pylint"])
parser.add_argument(
    "--results_dir", help="Directory where to put the results", required=True)
parser.add_argument("--suppressions_file",
                    help="File with suppressions to use (if not given, will compute it)")
parser.add_argument(
    "--warnings_file", help="File with warnings to use (if not given, will compute it)")


def get_all_suppressions(repo_dir, commit_id, results_dir):
    # read them into a list
    suppressions = set()
    suppression_file = join(results_dir.rsplit("/", 1)[0], "grep", f"{commit_id}_suppression.csv")
    if os.path.exists(suppression_file):
        suppressions = read_suppressions_from_file(suppression_file)
    else:
        # find suppressions
        grep = GrepSuppressionPython(repo_dir, commit_id, results_dir)
        grep.grep_suppression_for_specific_commit()
        suppression_file = join(results_dir, f"{commit_id}_suppression.csv")
        suppressions = read_suppressions_from_file(suppression_file)
    return suppressions


def get_all_warnings(repo_dir, commit_id, checker, results_dir):
    # run checkers
    if checker == "pylint":
        get_pylint_warnings(repo_dir, commit_id, results_dir)
    elif checker == "mypy":
        get_mypy_warnings(repo_dir, commit_id, results_dir)

    # read them into a list
    warning_file = join(results_dir, "check_results", checker, f"{commit_id}_warnings.csv")
    warnings = read_warning_from_file(warning_file)
    return warnings


def compute_mapping_by_removing_suppressions(repo_dir, suppressions, original_warnings, commit_id, checker, results_dir):
    # remove one suppression at a time and run the checker,
    # to see what warning(s) the suppression suppresses
    remover = SuppressionRemover(repo_dir)
    suppression_warning_pairs = []
    all_suppressed_warnings = set()
    useful_suppressions = []
    useless_suppressions = []
    for suppression in suppressions:
        remover.remove_suppression(suppression)
        warnings = get_all_warnings(repo_dir, commit_id, checker, results_dir)
        suppressed_warnings = warnings - original_warnings
        for suppressed_warning in suppressed_warnings:
            suppression_warning_pairs.append((suppression, suppressed_warning))
        if len(suppressed_warnings) == 0:
            suppression_warning_pairs.append((suppression, None))
            useless_suppressions.append(suppression)
        else:
            useful_suppressions.append(suppression)
        all_suppressed_warnings.update(suppressed_warnings)
        remover.restore()
    return suppression_warning_pairs, all_suppressed_warnings, useful_suppressions, useless_suppressions


def compute_mapping_via_pylint_support(repo_dir, suppressions, commit_id, relevant_files, results_dir):
    # get suppression-warning pairs from Pylint
    suppression_warning_pairs = get_suppressed_pylint_warnings(
        repo_dir, commit_id, results_dir, relevant_files)

    all_suppressed_warnings = set()
    useful_suppressions = set() # to write to file
    useful_suppressions_to_compare = set()
    useless_suppressions = set()

    if suppression_warning_pairs:
        # find useful suppressions and suppressed warnings
        for suppression, warning in suppression_warning_pairs:
            suppression_to_compare = Suppression(suppression.path, suppression.text.replace(" ", "").strip(), suppression.line)
            useful_suppressions_to_compare.add(suppression_to_compare) # avoid noise from " " when do the comparison
            # still add the original one, keep the original format to correctly get raw warning types in visualization
            useful_suppressions.add(suppression) 
            all_suppressed_warnings.add(warning)

        # find useless suppressions
        for suppression in suppressions:
            suppression_to_compare = Suppression(suppression.path, suppression.text.replace(" ", "").strip(), suppression.line)
            if suppression_to_compare not in useful_suppressions_to_compare:
                useless_suppressions.add(suppression) 
                suppression_warning_pairs.append((suppression, None))

    return suppression_warning_pairs, list(all_suppressed_warnings), list(useful_suppressions), list(useless_suppressions)


def main(repo_dir, commit_id, checker, results_dir, suppressions_file=None, \
        warnings_file=None, relevant_files: List[str] = None, file_specific=None):
    # checkout the commit
    target_repo = Repo(repo_dir)
    target_repo.git.checkout(commit_id, force=True)

    # get all suppressions and warnings
    if suppressions_file is None:
        suppressions = get_all_suppressions(repo_dir, commit_id, results_dir)
    else:
        suppressions = read_suppressions_from_file(suppressions_file)
    # keep only those suppressions that are for the current checker
    suppressions = [s for s in suppressions if s.get_checker() == checker]
    # keep only those suppressions that are in the relevant files
    if relevant_files is not None:
        suppressions = [s for s in suppressions if s.path in relevant_files]

    if checker == "pylint":
        suppression_warning_pairs, all_suppressed_warnings, useful_suppressions, useless_suppressions = compute_mapping_via_pylint_support(
            repo_dir, suppressions, commit_id, relevant_files, results_dir)
    elif checker == "mypy":
        # TODO any way to avoid this slow approach for mypy?

        if warnings_file is None:
            original_warnings = get_all_warnings(
                repo_dir, commit_id, checker, results_dir)
        else:
            original_warnings = read_warning_from_file(warnings_file)

        suppression_warning_pairs, all_suppressed_warnings, useful_suppressions, useless_suppressions = compute_mapping_by_removing_suppressions(
            repo_dir, suppressions, original_warnings, commit_id, checker, results_dir)

    if suppression_warning_pairs:
        write_mapping_to_csv(suppression_warning_pairs, results_dir, commit_id, file_specific)
    if all_suppressed_warnings:
        write_suppressed_warnings_to_csv(
            all_suppressed_warnings, results_dir, commit_id, file_specific)
    if useless_suppressions:
        write_suppression_to_csv(
            useless_suppressions, results_dir, commit_id, "useless", file_specific)
    if useful_suppressions:
        write_suppression_to_csv(
            useful_suppressions, results_dir, commit_id, "useful", file_specific)


if __name__ == "__main__":
    args = parser.parse_args()
    main(args.repo_dir, args.commit_id, args.checker, args.results_dir,
         args.suppressions_file, args.warnings_file)
