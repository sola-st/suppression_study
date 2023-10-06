# class ExtractHistories():
import argparse
import datetime
import json
import os
from os.path import join
import subprocess

from suppression_study.code_evolution.GetSuppressionDeleteHistories import GetSuppressionDeleteHistories
from suppression_study.code_evolution.GitLogFromFinalStatus import GitLogFromFinalStatus
from suppression_study.evolution.Select1000Commits import select_1000_commits
from suppression_study.suppression.Suppression import read_suppressions_from_file
from suppression_study.utils.FunctionsCommon import get_commit_date_lists

parser = argparse.ArgumentParser(description="Extract change histories of all suppressions at the repository level")
parser.add_argument("--repo_dir", help="Directory with the repository to check", required=True)
parser.add_argument(
    "--selected_1000_commits_csv", help="Expected .csv file, which stores selected commit IDs", required=True
)
parser.add_argument("--results_dir", help="Directory where to put the results", required=True)


def sort_by_date(all_histories):
    # sort the histories events by datetime
    all_histories.sort(key=lambda x: x[list(x.keys())[0]][0]["date"])
    for idx, x in enumerate(all_histories):
        assert len(x) == 1
        old_suppression_id = list(x.keys())[0]
        new_suppression_id = "# S" + str(idx)
        val = x[old_suppression_id]
        x.clear()
        x[new_suppression_id] = val

def write_all_histories_to_json(history_json_file, all_histories):  
    with open(history_json_file, "w", newline="\n") as ds:
        json.dump(all_histories, ds, indent=4, ensure_ascii=False)

def main(repo_dir, selected_1000_commits_csv, results_dir):
    # Get commit list and suppression for selected commits.
    if not os.path.exists(selected_1000_commits_csv):
        select_1000_commits(repo_dir, selected_1000_commits_csv)
    selected_1000_commits_list, selected_1000_dates_list = get_commit_date_lists(selected_1000_commits_csv)
    # Grep for suppressions in all relevant commits
    suppression_result = join(results_dir, "grep")
    if not os.path.exists(suppression_result):
        subprocess.run(
            ["python", "-m", "suppression_study.suppression.GrepSuppressionPython",
            "--repo_dir=" + repo_dir,
            "--commit_id=" + selected_1000_commits_csv,
            "--results_dir=" + results_dir,
            ]
        )

    if not os.listdir(suppression_result):
        os.rmdir(suppression_result)
        print("No suppression found in this repository by running GrepSuppressionPython.")
        return

    # get delete events, return delete events and the corresponding suppressions
    delete_event_and_suppression_list, suppression_final_commits_list = GetSuppressionDeleteHistories(
        repo_dir, selected_1000_commits_list, selected_1000_dates_list, suppression_result
    ).track_commits_forward()

    # get never removed suppressions
    # in theory, last_commit_with_suppression should be the newest commit
    never_removed_suppressions = ""
    last_commit_with_suppression = ""
    for commit in selected_1000_commits_list:
        commit_suppression_csv = join(suppression_result, f"{commit}_suppression.csv")
        if os.path.exists(commit_suppression_csv):
            never_removed_suppressions = read_suppressions_from_file(commit_suppression_csv)
            last_commit_with_suppression = commit
            break

    assert never_removed_suppressions != ""
    assert last_commit_with_suppression != ""

    # get add events (for both delete and never removed suppressions)
    # finally get the histories: 1) add event 2) add delete events
    evolution_init = GitLogFromFinalStatus(repo_dir, never_removed_suppressions, delete_event_and_suppression_list)
    only_add_event_histories = evolution_init.git_log_never_removed_suppression(last_commit_with_suppression)
    add_delete_histories = evolution_init.git_log_deleted_suppression(suppression_final_commits_list)

    all_histories = []
    all_histories.extend(only_add_event_histories)
    all_histories.extend(add_delete_histories)

    # Write all extracted suppression level histories to a JSON file.
    history_json_file = join(results_dir, "histories_suppression_level_all.json")
    write_all_histories_to_json(history_json_file, all_histories)


if __name__ == "__main__":
    args = parser.parse_args()
    print("Running...")
    start_time = datetime.datetime.now()
    main(args.repo_dir, args.selected_1000_commits_csv, args.results_dir)
    end_time = datetime.datetime.now()
    executing_time = (end_time - start_time).seconds
    print(f"Executing time: {executing_time} seconds")
    print("Done with ExtractHistory.")
