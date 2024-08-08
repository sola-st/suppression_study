import tempfile
import subprocess
from os.path import join

from tests.TestUtils import sort_and_compare_files

def test_GetMypyWarning():
    with tempfile.TemporaryDirectory() as demo_path:
        demo_repo_name = "suppression-test-python-mypy"
        demo_repo_git_link = "https://github.com/Hhyemin/suppression-test-python-mypy.git"
        subprocess.run("git clone " + demo_repo_git_link, cwd=demo_path, shell=True)

        repo_dir = join(demo_path, demo_repo_name)
        subprocess.run(["python", "-m", "suppression_study.checkers.GetMypyWarnings",
            "--repo_dir=" + repo_dir,
            "--commit_id=06d4370",
            "--results_dir=" + demo_path])
        
        actual_results = join(demo_path, "checker_results/mypy/06d4370_warnings.csv")
        expected_results = "tests/checkers/GetMypyWarnings/expected_06d4370_warnings.csv"
        sort_and_compare_files(actual_results, expected_results)