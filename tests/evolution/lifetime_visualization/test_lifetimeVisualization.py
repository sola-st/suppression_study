import os
import tempfile
import subprocess
from os.path import join

from suppression_study.utils.FunctionsCommon import FunctionsCommon
from tests.TestUtils import sort_and_compare_files


def test_LifetimeVisualization_toy_repo():
    with tempfile.TemporaryDirectory() as demo_path:
        demo_repo_name = "suppression-test-python-pylint"
        demo_repo_git_link = "https://github.com/michaelpradel/suppression-test-python-pylint.git"
        subprocess.run("git clone " + demo_repo_git_link, cwd=demo_path, shell=True)

        repo_dir = join(demo_path, demo_repo_name)
        commit_csv_file = join(repo_dir, "check_commits.csv")
        FunctionsCommon.write_commit_info_to_csv(repo_dir, commit_csv_file)

        # results_dir includes:
        # 1) extracted histories, {results_dir}/gitlog_history
        # 2) visualization data (2 csv files) and pdf 

        # "result" is used to avoid conflicts with the repository source: repo_dir
        results_dir = join(demo_path, "result", demo_repo_name) 

        # Get suppression histories
        subprocess.run(["python", "-m", "suppression_study.evolution.ExtractHistory",
            "--repo_dir=" + repo_dir,
            "--commit_id=" + commit_csv_file,
            "--results_dir=" + results_dir])
        
        # Start visualization
        visualization_result_folder = join(demo_path, "result")
        output = join(visualization_result_folder, "lifetime_all.csv")
        subprocess.run(["python", "-m", "suppression_study.evolution.lifetime_visualization.LifetimeVisualization",
            "--all_repositories_csv=tests/evolution/lifetime_visualization/all_repositories.csv", 
            f"--repo_parent_folder={demo_path}", 
            f"--lifetime_output_csv={output}"])
        
        actual_results = join(visualization_result_folder, "lifetime_all_groups.csv")
        expected_results_data = "tests/evolution/lifetime_visualization/expected_lifetime_all_groups.csv"
        sort_and_compare_files(actual_results, expected_results_data)

        # Check if the generated plot file has bytes
        expected_results_plot_pdf = join(visualization_result_folder, "lifetime_all_visualization.pdf")
        assert os.path.getsize(expected_results_plot_pdf) > 0