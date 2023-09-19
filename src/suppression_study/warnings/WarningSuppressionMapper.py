'''
For a given commit, computes a mapping between warnings and suppressions.
'''

import argparse
from os.path import join
from git.repo import Repo
from suppression_study.suppression.GrepSuppressionPython import GrepSuppressionPython
from suppression_study.checkers.GetPylintWarnings import main as get_pylint_warnings
from suppression_study.checkers.GetMypyWarnings import main as get_mypy_warnings
from suppression_study.suppression.SuppressionRemover import SuppressionRemover
from suppression_study.warnings.Warning import read_warning_from_file
from suppression_study.suppression.Suppression import read_suppressions_from_file
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
    # find suppressions
    grep = GrepSuppressionPython(repo_dir, commit_id, results_dir)
    grep.grep_suppression_for_specific_commit()

    # read them into a list
    suppression_file = join(results_dir, f"{commit_id}_suppression.csv")
    suppressions = read_suppressions_from_file(suppression_file)
    return suppressions


def get_all_warnings(repo_dir, commit_id, checker, results_dir):
    if checker == "pylint":
        get_pylint_warnings(repo_dir, commit_id, results_dir)
    elif checker == "mypy":
        get_mypy_warnings(repo_dir, commit_id, results_dir)

    # read them into a list
    warning_file = join(results_dir, "checker_results",
                        commit_id, f"{commit_id}_warnings.csv")
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


def compute_mapping_via_pylint_support(repo_dir, suppressions, original_warnings, commit_id, results_dir):
    # get suppression-warning pairs from Pylint
    suppression_warning_pairs = get_suppressed_pylint_warnings(
        repo_dir, commit_id, results_dir)

    # find useful suppressions and suppressed warnings
    all_suppressed_warnings = set()
    useful_suppressions = set()
    for suppression, warning in suppression_warning_pairs:
        useful_suppressions.add(suppression)
        all_suppressed_warnings.add(warning)

    # find useless suppressions
    useless_suppressions = set()
    for suppression in suppressions:
        if suppression not in useful_suppressions:
            useless_suppressions.add(suppression)
            suppression_warning_pairs.append((suppression, None))

    return suppression_warning_pairs, list(all_suppressed_warnings), list(useful_suppressions), list(useless_suppressions)


def main(repo_dir, commit_id, checker, results_dir, suppressions_file=None, warnings_file=None):
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

    if warnings_file is None:
        original_warnings = get_all_warnings(
            repo_dir, commit_id, checker, results_dir)
    else:
        original_warnings = read_warning_from_file(warnings_file)

    if checker == "pylint":
        suppression_warning_pairs, all_suppressed_warnings, useful_suppressions, useless_suppressions = compute_mapping_via_pylint_support(
            repo_dir, suppressions, original_warnings, commit_id, results_dir)
    elif checker == "mypy":
        # TODO any way to avoid this slow approach for mypy?
        suppression_warning_pairs, all_suppressed_warnings, useful_suppressions, useless_suppressions = compute_mapping_by_removing_suppressions(
            repo_dir, suppressions, original_warnings, commit_id, checker, results_dir)

    write_mapping_to_csv(suppression_warning_pairs, results_dir, commit_id)
    write_suppressed_warnings_to_csv(
        all_suppressed_warnings, results_dir, commit_id)
    write_suppression_to_csv(
        useless_suppressions, results_dir, commit_id, "useless")
    write_suppression_to_csv(
        useful_suppressions, results_dir, commit_id, "useful")


if __name__ == "__main__":
    args = parser.parse_args()
    main(args.repo_dir, args.commit_id, args.checker, args.results_dir,
         args.suppressions_file, args.warnings_file)
