'''
For a given repository, find any warnings that are accidentally suppressed,
i.e., that are suppressed by a suppression that was added before the warning itself appeared.
'''

import argparse
import os
from os.path import join
from typing import List
from suppression_study.evolution.ExtractHistory import read_histories_from_json
from suppression_study.utils.FunctionsCommon import get_commit_list
from suppression_study.warnings.WarningSuppressionMapper import main as compute_warning_suppression_mapping
from suppression_study.warnings.WarningSuppressionUtil import read_mapping_from_csv
from suppression_study.evolution.AccidentallySuppressedWarning import AccidentallySuppressedWarning, write_accidentally_suppressed_warnings
from suppression_study.evolution.ChangeEvent import ChangeEvent
from git.repo import Repo
from suppression_study.utils.GitRepoUtils import get_files_changed_by_commit


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
    begin_idx = commits.index(begin_commit)
    newest_event = suppression_history[-1]
    end_commit = newest_event.commit_id
    end_idx = commits.index(end_commit)
    if newest_event.change_operation == "file delete":
        # the file is not exist in the last commit, no need to run checker and check the warnings and suppressions. 
        end_idx += 1 

    range_of_commits = commits[end_idx: begin_idx+1] 
    range_of_commits.reverse() # we want the oldest commit first

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


def find_files_in_history(history: List[ChangeEvent]):
    files = set()
    for change_event in history:
        files.add(change_event.file_path)
    return files


def find_relevant_commits(repo_dir: str, history: List[ChangeEvent], commits: List[str]):
    # we care only about commits between the first and last event in the suppression history
    candidate_commits = find_relevant_range_of_commits(history, commits)

    # we care only about commits that change any of the files in the suppression history
    relevant_files = find_files_in_history(history)
    repo = Repo(repo_dir)
    result = []
    for commit in candidate_commits:
        files_changed_by_commit = get_files_changed_by_commit(repo, commit)
        if any(f in files_changed_by_commit for f in relevant_files):
            result.append(commit)

    return result # the commits that changes the relevant files.


def get_suppression_warning_pairs(repo_dir, commit, relevant_files, results_dir):
    # TODO mypy support
    compute_warning_suppression_mapping(
        repo_dir, commit, "pylint", results_dir, relevant_files=relevant_files)
    pairs = read_mapping_from_csv(results_dir=results_dir, commit_id=commit)
    return pairs


def check_for_accidental_suppressions(repo_dir, history, relevant_commits, relevant_files, results_dir):
    accidentally_suppressed_warnings = []
    previous_commit = None
    warnings_suppressed_at_previous_commit = None
    for commit in relevant_commits:
        event = find_closest_change_event(commit, history)
        suppression_warning_pairs = get_suppression_warning_pairs(
            repo_dir, commit, relevant_files, results_dir)

        # find warnings that the suppression suppresses at the current point in time
        warnings_suppressed_at_commit = []
        suppression = None
        for s, w in suppression_warning_pairs:
            # middle statuses' line numbers are unknown, here the closet event is just a way to show the suppression
            # TODO change the way to collect warnings_suppressed_at_commit, like keep the middle status for histories.
            if s.path == event.file_path and s.text == event.warning_type and s.line == event.line_number:
                suppression = s
                if w is not None:
                    warnings_suppressed_at_commit.append(w)

        # if a new warning shows up that wasn't suppressed by this suppression
        # at the previous commit, create an AccidentallySuppressedWarning
        if warnings_suppressed_at_previous_commit is not None:
            # TODO if we want to support "moving" suppressions, this check needs to be removed;
            # see the currently disabled test_AccidentalSuppressionFinder6()
            if suppression is not None:
                if len(warnings_suppressed_at_commit) > len(warnings_suppressed_at_previous_commit):
                    # there's a new warning suppressed by this suppression
                    accidentally_suppressed_warnings.append(
                        AccidentallySuppressedWarning(previous_commit,
                                                      commit,
                                                      suppression,
                                                      warnings_suppressed_at_previous_commit,
                                                      warnings_suppressed_at_commit))

        previous_commit = commit
        warnings_suppressed_at_previous_commit = warnings_suppressed_at_commit

    return accidentally_suppressed_warnings


def main(repo_dir, commits_file, history_file, results_dir):
    # read the list of commit ids
    commits = get_commit_list(commits_file)

    # read the suppression history
    histories = read_histories_from_json(history_file)
    print(f"Read {len(histories)} suppression histories.")

    all_accidentally_suppressed_warnings = []
    # go through all suppression histories
    for history_idx, history in enumerate(histories):
        if history[0].line_number != "merge unknown":
            # find the files and commits that are relevant for the suppression
            relevant_files = find_files_in_history(history)
            relevant_commits = find_relevant_commits(repo_dir, history, commits)
            print(f"Found {len(relevant_commits)} relevant commits.")

            accidentally_suppressed_warnings = check_for_accidental_suppressions(
                repo_dir, history, relevant_commits, relevant_files, results_dir)
            all_accidentally_suppressed_warnings.extend(
                accidentally_suppressed_warnings)
            print(f"Done with {history_idx + 1}/{len(histories)} histories. Found {len(accidentally_suppressed_warnings)} accidentally suppressed warnings.\n")
        else:
            print(f"Skip the {history_idx + 1}/{len(histories)}th history.\n")

    # write results to file
    print(f"Write all {len(all_accidentally_suppressed_warnings)} accidental suppressions.")
    output_file = join(os.path.dirname(results_dir), "accidentally_suppressed_warnings.json")
    write_accidentally_suppressed_warnings(
        all_accidentally_suppressed_warnings, output_file)


if __name__ == "__main__":
    args = parser.parse_args()
    main(args.repo_dir, args.commits_file, args.history_file, args.results_dir)
