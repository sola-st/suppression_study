import os
import tempfile
import subprocess
from os.path import join
from suppression_study.evolution.Select1000Commits import select_1000_commits
from suppression_study.evolution.lifetime_visualization.GetLifetimeGroupsInfo import GetLifetimeGroupsInfo
from suppression_study.evolution.lifetime_visualization.GetLifetimePlot import visualize_lifetime
from suppression_study.evolution.lifetime_visualization.LifetimeCalculator import LifetimeCalculator
from suppression_study.utils.FunctionsCommon import get_commit_date_lists
from tests.TestUtils import sort_and_compare_files


def test_LifetimeVisualization_toy_repo():
    with tempfile.TemporaryDirectory() as demo_path:
        demo_repo_name = "suppression-test-python-pylint"
        demo_repo_git_link = "https://github.com/michaelpradel/suppression-test-python-pylint.git"
        subprocess.run("git clone " + demo_repo_git_link, cwd=demo_path, shell=True)

        repo_dir = join(demo_path, demo_repo_name)
        selected_1000_commits_csv = join(repo_dir, "check_commits_1000.csv")
        select_1000_commits(repo_dir, selected_1000_commits_csv)
        all_main_commits_csv = join(repo_dir, "check_commits.csv") # only main branch
        all_commits, all_dates = get_commit_date_lists(all_main_commits_csv)

        # results_dir includes:
        # 1) extracted histories
        # 2) visualization data: 2 csv files and 1 pdf 

        visualization_result_folder = join(demo_path, "result")
        # "result" is used to avoid conflicts with the repository source: repo_dir
        results_dir = join(visualization_result_folder, demo_repo_name) 

        # Get suppression histories
        subprocess.run(["python", "-m", "suppression_study.evolution.ExtractHistory",
            "--repo_dir=" + repo_dir,
            "--selected_1000_commits_csv=" + selected_1000_commits_csv,
            "--results_dir=" + results_dir])
        
        # Start visualization
        suppression_history_json_file = join(results_dir, "histories_suppression_level_all.json")
        lifetime_output_csv = join(visualization_result_folder, "lifetime.csv")
        init = LifetimeCalculator(all_commits, all_dates, suppression_history_json_file, lifetime_output_csv)
        entire_lifetime, total_commits_num = init.get_lifetime()
        # Get groups for extracting plot
        lifetime_groups_csv = lifetime_output_csv.replace(".csv", "_groups.csv") # For all repositories
        # Based on lifetime_output_csv, process and write to lifetime_groups_csv
        num_groups = 5
        GetLifetimeGroupsInfo(entire_lifetime, total_commits_num, lifetime_output_csv, lifetime_groups_csv, num_groups).get_groups()
        visualize_lifetime(lifetime_groups_csv)
        
        actual_results = join(visualization_result_folder, "lifetime_groups.csv")
        expected_results_data = "tests/evolution/lifetime_visualization/expected_lifetime_groups.csv"
        sort_and_compare_files(actual_results, expected_results_data)

        # Check if the generated plot file has bytes
        expected_results_plot_pdf = join(visualization_result_folder, "lifetime_visualization.pdf")
        assert os.path.getsize(expected_results_plot_pdf) > 0