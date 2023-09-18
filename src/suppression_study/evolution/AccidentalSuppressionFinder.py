'''
For a given repository, find any warnings that are accidentally suppressed,
i.e., that are suppressed by a suppression that was added before the warning itself appeared.
'''

import argparse
from os.path import join
from typing import List
from suppression_study.evolution.SuppressionHistory import read_histories_from_json
from suppression_study.utils.FunctionsCommon import get_commit_list
from suppression_study.warnings.WarningSuppressionMapper import main as compute_warning_suppression_mapping, read_mapping_from_csv
from suppression_study.evolution.AccidentallySuppressedWarning import AccidentallySuppressedWarning, write_accidentally_suppressed_warnings
from suppression_study.evolution.ChangeEvent import ChangeEvent


parser = argparse.ArgumentParser(
    description="Find any warnings that are accidentally suppressed, i.e., that are suppressed by a suppression that was added before the warning itself appeared.")
parser.add_argument(
    "--repo_dir", help="Directory with the repository to analyze", required=True)
parser.add_argument("--commits_file",
                    help=".csv file which stores a list of commit IDs", required=True)
parser.add_argument("--history_file",
                    help="JSON file with the suppression histories of the repository", required=True)
parser.add_argument(
    "--results_dir", help="Directory where to put the results", required=True)


def find_relevant_range_of_commits(suppression_history, commits):
    """
    Find range of commits in the repo's history that overlap with
    the suppression history (including commits that don't change
    the suppression).

    Returns a list with the oldest relevant commit first.
    """
    oldest_event = suppression_history[0]
    begin_commit = oldest_event.commit_id
    newest_event = suppression_history[-1]
    if newest_event.change_operation in ["delete", "file delete"]:
        # the suppression was removed before the end of the repo's history
        end_commit = newest_event.commit_id
    else:
        # the suppression remains in the code until the end of the repo's history
        end_commit = commits[0]

    range_of_commits = []
    in_range = False
    for commit in reversed(commits):  # we want the oldest commit first
        if commit == begin_commit:
            in_range = True
            range_of_commits.append(commit)
        elif commit == end_commit:
            range_of_commits.append(commit)
            break
        elif in_range:
            range_of_commits.append(commit)

    return range_of_commits


def find_closest_change_event(commit, suppression_history: List[ChangeEvent]):
    """
    Find the ChangeEvent that is either at the commit or the latest before it.
    """
    closest = suppression_history[0]
    for event in suppression_history:
        if event.commit_id == commit:
            closest = event
    return closest


def analyze_suppression_history(results_dir, suppression_history, all_commits):
    accidentally_suppressed_warnings = []
    commits = find_relevant_range_of_commits(suppression_history, all_commits)

    warnings_suppressed_at_previous_commit = None
    for commit in commits:
        event = find_closest_change_event(commit, suppression_history)
        suppression_warning_pairs = read_mapping_from_csv(results_dir, commit)

        # find warnings that the suppression suppresses at the current point in time
        warnings_suppressed_at_commit = []
        for s, w in suppression_warning_pairs:
            if s.path == event.file_path and s.text == event.warning_type and s.line == event.line_number:
                if w is not None:
                    warnings_suppressed_at_commit.append(w)

        # if a new warning shows up that wasn't suppressed by this suppression
        # at the previous commit, create an AccidentallySuppressedWarning
        if warnings_suppressed_at_previous_commit is not None:
            # TODO currently, we compare warnings exactly, but a warning may move to a different location
            new_warnings = set(warnings_suppressed_at_commit) - \
                set(warnings_suppressed_at_previous_commit)
            for warning in new_warnings:
                accidentally_suppressed_warnings.append(
                    AccidentallySuppressedWarning(commit, warning))

        warnings_suppressed_at_previous_commit = warnings_suppressed_at_commit

    return accidentally_suppressed_warnings


def main(repo_dir, commits_file, history_file, results_dir):
    # read the list of commit ids
    commits = get_commit_list(commits_file)

    # read the suppression history
    histories = read_histories_from_json(history_file)

    # compute warning-suppression mappings for all commits
    for commit in commits:
        # TODO add support for mypy
        compute_warning_suppression_mapping(
            repo_dir, commit, "pylint", results_dir)

    # analyze each suppression history separately
    all_accidentally_suppressed_warnings = []
    for history in histories:
        accidentally_suppressed_warnings = analyze_suppression_history(
            results_dir, history, commits)
        all_accidentally_suppressed_warnings.extend(
            accidentally_suppressed_warnings)

    # write results to file
    output_file = join(results_dir, "accidentally_suppressed_warnings.json")
    write_accidentally_suppressed_warnings(
        all_accidentally_suppressed_warnings, output_file)


if __name__ == "__main__":
    args = parser.parse_args()
    main(args.repo_dir, args.commits_file, args.history_file, args.results_dir)
