from typing import List
import argparse
import re
from os.path import exists, join
from suppression_study.checkers.GetPylintWarnings import GetPylintWarnings
from suppression_study.suppression.Suppression import Suppression
from suppression_study.warnings.Warning import Warning
from suppression_study.warnings.WarningSuppressionUtil import write_mapping_to_csv


parser = argparse.ArgumentParser(
    description="Gather all suppressed Pylint warnings in a specific commit")
parser.add_argument(
    "--repo_dir", help="Directory with the repository to check", required=True)
parser.add_argument(
    "--commit_id", help="Specify which commit to check", required=True)
parser.add_argument(
    "--results_dir", help="Directory where to put the results", required=True)


class GetSuppressedPylintWarnings(GetPylintWarnings):
    """
    Runs Pylint while enabling its suppressed-message option,
    which allows us to get the list of suppressed warnings.   
    """

    def __init__(self, repo_dir, commit_id, results_dir, file_specific, relevant_files): 
        # relevant_files is a set. It is valid >=python 3.9 as relevant_files: set[str] and <3.9 relevant_files: Set[str]
        self.repo_dir = repo_dir
        self.commit_id = commit_id
        self.results_dir = results_dir
        self.file_specific, = file_specific, 
        self.relevant_files = relevant_files

    def run_checker(self):
        checker = "pylint"
        report = None
        commit_results_dir = None
        
        # the default output path from checkers/GetWarningsSuper.py
        default_report_path = join(self.results_dir, "checker_results", checker, f"{self.commit_id}_report.txt")
        if not exists(default_report_path):
            if self.relevant_files:
                files_to_analyze = [
                    f for f in self.relevant_files if exists(join(self.repo_dir, f))]
                command_line = f"pylint --recursive=y --disable=I --enable=I0020 {' '.join(files_to_analyze)}"
            else: # for running tests
                command_line = f"pylint --recursive=y --disable=I --enable=I0020 ./"

            report, commit_results_dir = super(
                GetPylintWarnings, self).run_checker(checker, command_line, self.file_specific)

        return report, commit_results_dir

    def read_reports(self, report):
        suppression_warning_pairs = []
        with open(report, "r") as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                if line.endswith("(suppressed-message)"):
                    # [file for file in self.relevant_files if file in line] and 
                    assert line.count(":") == 4
                    file_path, line_number, _, _, rest = line.split(":")
                    m = re.search(
                        " Suppressed '(.+?)' \(from line (.+?)\)", rest)
                    assert m
                    warning_type = m.group(1)
                    suppression_line_number = m.group(2)

                    suppression = Suppression(
                        file_path, f"# pylint: disable={warning_type}", int(suppression_line_number))
                    warning = Warning(
                        file_path, warning_type, int(line_number))
                    suppression_warning_pairs.append([suppression, warning])
                elif "Parsing failed" in line:
                    # print(f"Parsing failed: {report}")
                    suppression_warning_pairs = None
                    break

        return suppression_warning_pairs


def main(repo_dir, commit_id, results_dir, relevant_files: List[str] = None):
    # avoid covering the existing check reports.
    # file_specific: file name and its first layer parent folder name as a symbol to identify different reports
    # e.g., all/repo/a.py --> repo_a
    file_specific = None
    if relevant_files:
        file_specific = "_".join(relevant_files[0].rsplit("/", 3)[1:]).rsplit(".", 1)[0]

    tool = GetSuppressedPylintWarnings(
        repo_dir, commit_id, results_dir, file_specific, relevant_files, )
    report, _ = tool.run_checker()

    suppression_warning_pairs = []
    if report:
        suppression_warning_pairs = tool.read_reports(report)
        if suppression_warning_pairs:
            write_mapping_to_csv(suppression_warning_pairs, results_dir, commit_id, file_specific)
    return suppression_warning_pairs


if __name__ == "__main__":
    args = parser.parse_args()
    main(args.repo_dir, args.commit_id, args.results_dir)
