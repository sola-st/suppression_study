'''
For a given repository, find any warnings that are accidentally suppressed,
i.e., that are suppressed by a suppression that was added before the warning itself appeared.
'''

import argparse
import ast
import os
from os.path import join, exists
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
    range_of_commits = []
    oldest_event = suppression_history[0]
    begin_commit = oldest_event.commit_id
    if begin_commit in commits:
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
    return list(files)


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
    file_specific = "_".join(relevant_files[0].rsplit("/", 3)[1:]).rsplit(".", 1)[0]
    file = join(results_dir, f"{commit}_mapping_{file_specific}.csv")
    if not exists(file):
        compute_warning_suppression_mapping(
            repo_dir, commit, "pylint", results_dir, relevant_files=relevant_files, file_specific=file_specific)
    pairs = read_mapping_from_csv(file=file)
    return pairs


def check_for_accidental_suppressions(repo_dir, history, relevant_commits, relevant_files, results_dir):
    accidentally_suppressed_warnings = []
    previous_commit = None
    warnings_suppressed_at_previous_commit = None

    add_event = history[0]
    event_warning_type = add_event.warning_type
    event_file_path = add_event.file_path
    middle_statuses_chain = ast.literal_eval(add_event.middle_status_chain)
    # commits = [add_event.commit_id]
    # line_nums = [add_event.line_number]
    file_paths = []
    commits = []
    line_nums = []
    for item in middle_statuses_chain:
        if len(item) == 3:
            path, commit, line = item
            file_paths.append(path)
            commits.append(commit)
            line_nums.append(line)

    if add_event.commit_id not in commits:
        # if in, may some impacts from git happens
        file_paths.insert(0, event_file_path)
        commits.insert(0, add_event.commit_id)
        line_nums.insert(0, add_event.line_number)
    
    for commit in relevant_commits:
        # if not "<Parsing failed>" in warnings_suppressed_at_previous_commit 
        if commit in commits:
            suppression_warning_pairs = get_suppression_warning_pairs(
                repo_dir, commit, relevant_files, results_dir)
            if suppression_warning_pairs:
                # find warnings that the suppression suppresses at the current point in time
                warnings_suppressed_at_commit = []
                suppression = None
                idx = commits.index(commit)
                line_in_commit = line_nums[idx]
                file_path_in_commit = file_paths[idx]
                for s, w in suppression_warning_pairs:
                    if (s.path == event_file_path or s.path == file_path_in_commit) and \
                        s.text == event_warning_type and \
                        (s.line == line_in_commit or "merge" in str(line_in_commit)):
                        suppression = s
                        if w is not None:
                            warnings_suppressed_at_commit.append(w)
                    
                # if a new warning shows up that wasn't suppressed by this suppression
                # at the previous commit, create an AccidentallySuppressedWarning
                if warnings_suppressed_at_previous_commit is not None:
                    if suppression is not None:
                        if len(warnings_suppressed_at_commit) > len(warnings_suppressed_at_previous_commit):
                            # there's a new warning suppressed by this suppression
                            # TODO Check if the suppression is useless.
                            accidentally_suppressed_warnings.append(
                                AccidentallySuppressedWarning(previous_commit,
                                                            commit,
                                                            suppression,              
                                                            warnings_suppressed_at_previous_commit,
                                                            warnings_suppressed_at_commit))
                previous_commit = commit
                warnings_suppressed_at_previous_commit = warnings_suppressed_at_commit
            else:
                warnings_suppressed_at_previous_commit = None
                previous_commit = None
        else:
            warnings_suppressed_at_previous_commit = None
            previous_commit = None

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
        # find the files and commits that are relevant for the suppression
        relevant_files = find_files_in_history(history)
        relevant_commits = find_relevant_commits(repo_dir, history, commits)
        print(f"Found {len(relevant_commits)} relevant commits.")

        accidentally_suppressed_warnings = check_for_accidental_suppressions(
            repo_dir, history, relevant_commits, relevant_files, results_dir)
        all_accidentally_suppressed_warnings.extend(accidentally_suppressed_warnings)
        print(f"Done with {history_idx + 1}/{len(histories)} histories. Found {len(accidentally_suppressed_warnings)} accidentally suppressed warnings.\n")

    # write results to file
    print(f"Write all {len(all_accidentally_suppressed_warnings)} accidental suppressions.")
    output_file = join(os.path.dirname(results_dir), "accidentally_suppressed_warnings.json")
    write_accidentally_suppressed_warnings(
        all_accidentally_suppressed_warnings, output_file)


if __name__ == "__main__":
    args = parser.parse_args()
    main(args.repo_dir, args.commits_file, args.history_file, args.results_dir)
