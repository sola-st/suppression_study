from os.path import join
import tempfile
import subprocess
from tests.TestUtils import sort_and_compare_files


def test_mapping():
    with tempfile.TemporaryDirectory() as working_dir:
        repo_name = "suppression-test-suppr-warn-map"
        repo_url = "https://github.com/michaelpradel/suppression-test-suppr-warn-map.git"
        subprocess.run(f"git clone {repo_url}", cwd=working_dir, shell=True)

        repo_dir = join(working_dir, repo_name)

        subprocess.run(["python", "-m", "suppression_study.warnings.WarningSuppressionMapper",
                        "--repo_dir=" + repo_dir,
                        "--commit_id=7178e72",
                        "--lang=python",
                        "--checker=pylint",
                        "--results_dir=" + working_dir])

        # check that the mapping between suppressions and warnings is correct
        mapping_actual = join(working_dir, "7178e72_mapping.csv")
        mapping_expected = "tests/warnings/WarningSuppressionMapper/expected_mapping.csv"
        sort_and_compare_files(mapping_actual, mapping_expected)

        # check that the lists of suppressed warnings are correct
        mapping_actual = join(working_dir, "7178e72_suppressed_warnings.csv")
        mapping_expected = "tests/warnings/WarningSuppressionMapper/expected_suppressed_warnings.csv"
        sort_and_compare_files(mapping_actual, mapping_expected)

        # check that the lists of useful and useless suppressions are correct
        mapping_actual = join(working_dir, "7178e72_useful_suppressions.csv")
        mapping_expected = "tests/warnings/WarningSuppressionMapper/expected_useful_suppressions.csv"
        sort_and_compare_files(mapping_actual, mapping_expected)
        mapping_actual = join(working_dir, "7178e72_useless_suppressions.csv")
        mapping_expected = "tests/warnings/WarningSuppressionMapper/expected_useless_suppressions.csv"
        sort_and_compare_files(mapping_actual, mapping_expected)
