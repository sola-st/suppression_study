import tempfile
import subprocess
from os.path import join

from tests.TestUtils import sort_and_compare_files

def test_GetPylintWarning():
    with tempfile.TemporaryDirectory() as demo_path:
        demo_repo_name = "suppression-test-python-pylint"
        demo_repo_git_link = "https://github.com/michaelpradel/suppression-test-python-pylint.git"
        subprocess.run("git clone " + demo_repo_git_link, cwd=demo_path, shell=True)

        repo_dir = join(demo_path, demo_repo_name)
        subprocess.run(["python", "-m", "suppression_study.checkers.GetPylintWarnings",
            "--repo_dir=" + repo_dir,
            "--commit_id=a09fcfe",
            "--results_dir=" + demo_path])

        expected_results = "tests/checkers/GetPylintWarnings/a09fcfe_warnings.csv"
        actual_results = join(demo_path, "checker_results/a09fcfe/a09fcfe_warnings.csv")
        sort_and_compare_files(expected_results, actual_results)