import tempfile
import subprocess
from os.path import join
from suppression_study.evolution.Select1000Commits import select_1000_commits
from tests.TestUtils import exactly_compare_files


def run_test_on_repo(repo_name, repo_url, expected_result_file):
    with tempfile.TemporaryDirectory() as working_dir:
        subprocess.run("git clone " + repo_url,
                       cwd=working_dir, shell=True)

        # extract suppression histories, which are needed for the accidental suppression finder
        repo_dir = join(working_dir, repo_name)
        selected_1000_commits_csv = join(repo_dir, "check_commits_1000.csv")
        select_1000_commits(repo_dir, selected_1000_commits_csv)
        subprocess.run(["python", "-m", "suppression_study.evolution.ExtractHistory",
                        "--repo_dir=" + repo_dir,
                        "--selected_1000_commits_csv=" + selected_1000_commits_csv,
                        "--results_dir=" + working_dir])

        history_file = join(
            working_dir, "histories_suppression_level_all.json")

        repo_dir = join(working_dir, repo_name)
        subprocess.run(["python", "-m", "suppression_study.evolution.AccidentalSuppressionFinder",
                        "--repo_dir=" + repo_dir,
                        "--commits_file=" + selected_1000_commits_csv,
                        "--history_file=" + history_file,
                        "--results_dir=" + repo_dir]) # the results json file will be written to working_dir

        actual_result_file = join(
            working_dir, "accidentally_suppressed_warnings.json")
        exactly_compare_files(actual_result_file, expected_result_file)


def test_AccidentalSuppressionFinder3():
    run_test_on_repo("suppression-test-accidental3",
                     "https://github.com/michaelpradel/suppression-test-accidental3.git",
                     "tests/evolution/expected_accidentally_suppressed_warnings3.json")


def test_AccidentalSuppressionFinder4():
    run_test_on_repo("suppression-test-accidental4",
                     "https://github.com/michaelpradel/suppression-test-accidental4.git",
                     "tests/evolution/expected_accidentally_suppressed_warnings4.json")

def test_AccidentalSuppressionFinder5():
    run_test_on_repo("suppression-test-accidental5",
                     "https://github.com/michaelpradel/suppression-test-accidental5.git",
                     "tests/evolution/expected_accidentally_suppressed_warnings5.json")
    
def test_AccidentalSuppressionFinder6():
    run_test_on_repo("suppression-test-accidental6",
                     "https://github.com/michaelpradel/suppression-test-accidental6.git",
                     "tests/evolution/expected_accidentally_suppressed_warnings6.json")