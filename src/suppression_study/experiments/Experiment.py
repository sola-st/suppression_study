from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict
from os.path import join, exists, isdir
from os import makedirs
from git.repo import Repo
from suppression_study.utils.GitRepoUtils import get_name_of_main_branch


class Experiment(ABC):
    """
    Base class for implementing an experiment.
    An experiment invokes one or more of our tools on all
    the repositories considered in this study.
    This class provides helper methods useful for multiple experiments.

    Experiments may depend on each other, in which case the dependencies
    should be mentioned in the class-level documentation of the experiment.
    It's the user's responsibility to run any dependencies before
    dependent experiments.
    """

    def __init__(self):
        self.latest_commit_date = "2023-09-01T00:00:00-00:00"

    def _is_repo(self, repo_dir):
        try:
            Repo(repo_dir)
            return True  # repo exists and is valid
        except:
            return False

    def get_repo_dirs(self) -> List[str]:
        """
        Returns a list with the directories of all repositories.
        If the repositories are not yet cloned, this method clones them first.
        """
        # read repo file
        repo_file = join("data", "python_repos.txt")
        with open(repo_file) as f:
            git_urls = f.read().splitlines()

        # ensure we have data/repos directory
        makedirs(join("data", "repos"), exist_ok=True)

        # ensure that repos are cloned
        repo_dirs = []
        for git_url in git_urls:
            short_name = git_url.split("/")[-1].replace(".git", "")
            repo_dir = join("data", "repos", short_name)
            if not (exists(repo_dir) and isdir(repo_dir) and self._is_repo(repo_dir)):
                print(f"Cloning {git_url} to {repo_dir}")
                makedirs(repo_dir)
                Repo.clone_from(git_url, repo_dir)
            repo_dirs.append(repo_dir)

        # return list of repo dirs
        return repo_dirs

    def checkout_latest_commits(self) -> Dict[str, str]:
        """
        Checks out the latest commit of all repositories (where "latest" is 
        fixed to a specific data for reproducibility).

        Returns a dictionary from repo directory to commit ID.
        """
        repo_dir_to_commit = {}
        for repo_dir in self.get_repo_dirs():
            repo = Repo(repo_dir)
            branch = get_name_of_main_branch(repo)
            latest_commit = next(repo.iter_commits(branch, max_count=1,
                                                   until=self.latest_commit_date))
            repo.git.checkout(latest_commit, force=True)
            commit_id = latest_commit.hexsha[:8]
            repo_dir_to_commit[repo_dir] = commit_id
            print(f"Checked out commit {commit_id} of {repo_dir}")
        return repo_dir_to_commit

    @abstractmethod
    def run(self):
        """
        To be implemented by subclasses with code for running the experiment.
        """
        ...
