import csv
import os
import tempfile
import subprocess
from os.path import join

from suppression_study.utils.FunctionsCommon import write_commit_info_to_csv
from tests.TestUtils import sort_and_compare_files


def test_OccurrencesVisualization_in_suppressions():
    with tempfile.TemporaryDirectory() as demo_path:
        all_repositories_csv = "tests/suppression/occurrences/all_repositories.csv"
        csv_reader = csv.reader(open(all_repositories_csv))
        for repo in csv_reader:
            repo_name = repo[1]
            git_link = repo[2]
            subprocess.run("git clone " + git_link, cwd=demo_path, shell=True)

            repo_dir = join(demo_path, repo_name) 
            commit_csv_file = join(repo_dir, "check_commits.csv")
            write_commit_info_to_csv(repo_dir, commit_csv_file)
            
            suppression_results_dir = join(demo_path, repo_name)
            subprocess.run(["python", "-m", "suppression_study.suppression.GrepSuppressionPython",
            f"--repo_dir={repo_dir}",
            f"--commit_id={commit_csv_file}",
            f"--results_dir={suppression_results_dir}"]) 

        subprocess.run(["python", "-m", "suppression_study.suppression.occurrences.OccurrencesVisualization",
            f"--all_repositories_csv={all_repositories_csv}",
            f"--results_repos_parent_folder={demo_path}",
            f"--results_dir={demo_path}",
            f"--type_source='suppressions'"])

        # TODO newly edited suppression format steps are not well fit for mypy
        # warning_types_occurrences does not includes mypy warning types now
        actual_results_data = join(demo_path, "occurrences/warning_types_occurrences.csv")
        expected_results_data = "tests/suppression/occurrences/expected_warning_types_occurrences.csv"
        sort_and_compare_files(actual_results_data, expected_results_data)

        # Check if the generated plot file has bytes
        expected_results_plot_pdf = join(demo_path, "occurrences/warning_types_occurrences_visualization.pdf")
        assert os.path.getsize(expected_results_plot_pdf) > 0