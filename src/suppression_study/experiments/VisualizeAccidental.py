from collections import Counter
import json
from os.path import join
import subprocess
from git.repo import Repo

from matplotlib import pyplot as plt
from suppression_study.evolution.AnalyzeGitlogReport import AnalyzeGitlogReport
from suppression_study.evolution.lifetime_visualization.LifetimeCalculator import time_delta
from suppression_study.experiments.Experiment import Experiment
from suppression_study.suppression.Suppression import get_raw_warning_type_from_formatted_suppression_text
from suppression_study.utils.FunctionsCommon import get_commit_date_lists
from suppression_study.utils.GitRepoUtils import repo_dir_to_name
from suppression_study.suppression.NumericSpecificTypeMap import get_specific_numeric_type_map_list


def get_time_between_add_and_accidental_data(repo_dirs, commit_suppressions, 
        raw_warning_types, specific_numeric_maps, accidental_dates):
    days = []
    pre_repo = ""
    pre_commit = ""
    repo_base = Repo()
    for repo_dir, cs, raw_type, accidental_date in zip(repo_dirs, commit_suppressions, raw_warning_types, accidental_dates):
        commit = cs.commit
        if pre_repo != repo_dir:
            repo_base = Repo(repo_dir)
            repo_base.git.checkout(commit, force=True)
        else:
            if pre_commit != commit:
                repo_base.git.checkout(commit, force=True)
        suppression = cs.suppression
        current_file = suppression["path"]
        line_range_start_end = suppression["line"]
        line_range_str = str(line_range_start_end)
        command_line = "git log -C -M -L" + line_range_str + "," + line_range_str + ":'" + current_file + "' --first-parent"
        result = subprocess.run(command_line, cwd=repo_dir, shell=True, stdout=subprocess.PIPE, universal_newlines=True)
        log_result = result.stdout
            
        expected_add_event = AnalyzeGitlogReport(log_result, "# pylint:", raw_type, current_file,
                specific_numeric_maps).from_gitlog_results_to_change_events()

        delta_day = time_delta(expected_add_event["date"], accidental_date)
        days.append(delta_day)

        pre_repo = repo_dir
        pre_commit = commit

    return days

def plot_time_between_add_and_accidental(days, time_plot_output):
    element_counts = Counter(days)

    unique_elements = list(element_counts.keys())
    frequencies = list(element_counts.values())
    # TODO a better way to show all the time for all the relevant suppressions
    top_days = sorted(zip(unique_elements, frequencies), key=lambda x: x[0], reverse=True)[:20]

    day = [item[0] for item in top_days]
    num_suppression = [item[1] for item in top_days]
    day = [str(item) for item in day]
    plt.figure(figsize=(10, 6))
    plt.bar(day, num_suppression, color='purple')
    plt.xlabel('Days')
    plt.ylabel('Number of suppressions')

    plt.tight_layout()
    plt.savefig(time_plot_output)

def plot_previous_current_warnings_num(difference, previous_nums, nums, compare_plot_output):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))  # 1 row, 2 columns
    indices = list(range(1, len(previous_nums) + 1))

    # subplot 1
    maker_size = 4
    ax1.scatter(indices, previous_nums, label='Before', color='blue', marker='o', s=maker_size)
    ax1.scatter(indices, nums, label='After', color='orange', marker='^', s=maker_size)
    ax1.set_xlabel('Indices of suppressions')
    ax1.set_ylabel('Numbers of warnings')
    ax1.legend()

    # subplot 2, line plot 
    ax2.plot(indices, difference, label='After - Before', color='green', linestyle='-', marker='o', markersize=maker_size-2)
    ax2.set_xlabel('Index of suppressions')
    ax2.set_ylabel('Number of potential accidentally suppressed warnings')
    ax2.legend()

    plt.tight_layout()
    plt.savefig(compare_plot_output)

def plot_top_rank_accidentally_suppressed_warning_types(difference, raw_warning_types, top_rank_plot_output):
    type_dict = {}
    for t, diff in zip(raw_warning_types, difference):
        if t in type_dict:
            type_dict[t] += diff
        else:
            type_dict[t] = diff

    top = sorted(type_dict.items(), key=lambda item: item[1], reverse=True)[:10]
    print(top)
    top.reverse()

    top_types = [item[0] for item in top]
    top_values = [item[1] for item in top]

    plt.figure(figsize=(10, 6))
    plt.barh(top_types, top_values, color='purple')
    plt.ylabel('Warning types')
    plt.xlabel('Occurrences of accidentally suppressed warnings')

    for i, value in enumerate(top_values):
        plt.text(value, i, str(value), va='center', ha='left')

    plt.tight_layout()
    plt.savefig(top_rank_plot_output)


class CommitSuppressionAccidental():
    def __init__(self, commit, suppression):
        self.commit = commit
        self.suppression = suppression


class InspectSuppressionRelatedCommits(Experiment):
    """
    Visualize the time between the suppressions been added and the corresponding accidental warnings found

    Depends on:
     * ComputeAccidentallySuppressedWarnings
    """
    def __init__(self):
        self.commit_suppressions = []
        self.raw_warning_types = []
        self.previous_nums = []
        self.nums = []
        self.repo_dirs_mapped = []
        self.dates = []

    def _read_accidentally_suppressed_warnings(self):
        repo_dirs = self.get_repo_dirs()
        for repo_dir in repo_dirs:
            repo_name = repo_dir_to_name(repo_dir)
            commit_list_file_1000 = join("data", "results", repo_name, "commit_id_list_1000.csv")
            commits_list, date_list = get_commit_date_lists(commit_list_file_1000)
            acci_warning_file = join("data", "results", repo_name,
                                "accidentally_suppressed_warnings.json")
            with open(acci_warning_file, "r") as f:
                records_data = json.load(f)
                for data in records_data:
                    commit = data["commit"]
                    idx = commits_list.index(commit)
                    date = date_list[idx]
                    self.dates.append(date)
                    suppression_text = data["suppression"]["text"]
                    raw_warning_type = get_raw_warning_type_from_formatted_suppression_text(suppression_text)
                    commit_suppression_accidental = CommitSuppressionAccidental(commit, data["suppression"])
                    self.commit_suppressions.append(commit_suppression_accidental)
                    self.raw_warning_types.append(raw_warning_type)
                    self.previous_nums.append(len(data["previous_warnings"]))
                    self.nums.append(len(data["warnings"]))
                    self.repo_dirs_mapped.append(repo_dir) # with duplicates, just keep map with all th other lists

    def run(self):
        self._read_accidentally_suppressed_warnings()

        # Calculate the difference between self.previous_nums, self.nums
        # the absolute numbers, 
        # even without the manual checking, the after - before is exactly newly suppressed warnings
        # difference = [b - a for a, b in zip(self.previous_nums, self.nums)]

        # # plot 1
        # compare_plot_output = join("data", "results", "accidental_num_changes_before_after.pdf")
        # plot_previous_current_warnings_num(difference, self.previous_nums, self.nums, compare_plot_output)

        # # plot 2
        # top_rank_plot_output = join("data", "results", "top_accidentally_suppressed_warning_types_text.pdf")
        # plot_top_rank_accidentally_suppressed_warning_types(difference, self.raw_warning_types, top_rank_plot_output)

        # plot 3
        specific_numeric_maps = get_specific_numeric_type_map_list()
        days = get_time_between_add_and_accidental_data(self.repo_dirs_mapped, 
                self.commit_suppressions, self.raw_warning_types, specific_numeric_maps, self.dates)

        time_plot_output = join("data", "results", "accidental_time.pdf")
        plot_time_between_add_and_accidental(days, time_plot_output)


if __name__ == '__main__':
    InspectSuppressionRelatedCommits().run()
