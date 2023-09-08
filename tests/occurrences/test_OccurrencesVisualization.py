import csv
import os
import tempfile
import subprocess
from os.path import join

from suppression_study.utils.FunctionsCommon import FunctionsCommon
from tests.TestUtils import sort_and_compare_files


def test_OccurrencesVisualization_toy_repos():
    with tempfile.TemporaryDirectory() as demo_path:
        all_repositories_csv = "tests/occurrences/all_repositories.csv"
        csv_reader = csv.reader(open(all_repositories_csv))
        for repo in csv_reader:
            repo_name = repo[1]
            git_link = repo[2]
            subprocess.run("git clone " + git_link, cwd=demo_path, shell=True)

            repo_dir = join(demo_path, repo_name) 
            commit_csv_file = join(repo_dir, "check_commits.csv")
            FunctionsCommon.write_commit_info_to_csv(repo_dir, commit_csv_file)
            
            suppression_results_dir = join(demo_path, repo_name)
            subprocess.run(["python", "-m", "suppression_study.suppression.GrepSuppressionPython",
            f"--repo_dir={repo_dir}",
            f"--commit_id={commit_csv_file}",
            f"--results_dir={suppression_results_dir}"]) 

        subprocess.run(["python", "-m", "suppression_study.occurrences.OccurrencesVisualization",
            f"--all_repositories_csv={all_repositories_csv}",
            f"--grep_parent_folder={demo_path}",
            f"--results_dir={demo_path}"])

        expected_results_data = "tests/occurrences/warning_types_occurrences.csv"
        actual_results_data = join(demo_path, "occurrences/warning_types_occurrences.csv")
        sort_and_compare_files(expected_results_data, actual_results_data)

        # Check if the generated plot file has bytes
        expected_results_plot_pdf = join(demo_path, "occurrences/warning_types_occurrences_visualization.pdf")
        assert os.path.getsize(expected_results_plot_pdf) > 0