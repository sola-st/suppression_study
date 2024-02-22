import csv
from os.path import join
from git.repo import Repo
from shutil import rmtree
import subprocess

from suppression_study.experiments.Experiment import Experiment
from suppression_study.utils.GitRepoUtils import get_name_of_main_branch


class FindProjectsUsingPylint(Experiment):
    """
    Experiment to search for projects that may use Pylint.
    The projects found here still need to be manually checked to see if they
    actually use Pylint.
    """
    def run(self):
        # load candidate repos from file
        candidate_file = join("data", "project_selection.csv")
        min_commits = 1000
        projects = []
        with open(candidate_file, "r") as f:
            csv_reader = csv.reader(f)
            next(csv_reader)  # skip header
            for row in csv_reader:
                # filter by nb of commits
                if int(row[4]) >= min_commits:
                    projects.append(row)

        # sort by nb of stars
        projects.sort(key=lambda x: int(x[3]), reverse=True)

        tmpdir = join("data", "tmp_do_not_commit")
        rmtree(tmpdir)
        for project in projects:
            print("================================================")
            # clone and go to "date of the study" (= latest commit before 2023-09-01)
            git_url = project[2]
            name = project[1]
            repo_dir = join(tmpdir, name)
            print(f"Cloning {git_url}")
            repo = Repo.clone_from(git_url, repo_dir)

            branch = get_name_of_main_branch(repo)
            latest_commit = next(repo.iter_commits(branch, max_count=1,
                                                   until=self.latest_commit_date))
            commit_id = latest_commit.hexsha[:8]
            repo.git.checkout(latest_commit, force=True)
            print(f"Checked out commit {commit_id} of {repo_dir}")

            # grep for "pylint" and look for file names that contain "pylint"
            print("Grep for 'pylint' in the repo")
            grep_cmd = f"grep -ri 'pylint' {repo_dir}"
            result = subprocess.run(grep_cmd, shell=True)
            print(result)

            print("Search for files that contain 'pylint'")
            find_cmd = f"find {repo_dir} -iname '*pylint*'"
            result = subprocess.run(find_cmd, shell=True)
            print(result)



if __name__ == "__main__":
    FindProjectsUsingPylint().run()
