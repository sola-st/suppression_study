from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List
from os.path import join, exists, is_dir
from os import mkdirs
from datetime import datetime
from git.repo import Repo


class Experiment(ABC):
    """
    Base class for implementing an experiment.
    
    An experiment invokes one or more of our tools on all
    the repositories considered in this study.
    The results of the experiment are stored in /data/experiment_xxx_yyy,
    where xxx is the name of the experiment and yyy is a timestamp.

    Experiment do *not* have to clean up results written to /data/experiment_xxx_yyy,
    because other experiments may depend on them and to ease inspecting the results.
    """

    def __init__(self, name, depends_on: List[Experiment] = []):
        # create a directory for the experiment
        timestamp = datetime.now().strftime("%Y.%m.%d_%H.%M.%S.%f")
        self.data_dir = join("data", f"experiment_{name}_{timestamp}")
        mkdirs(self.data_dir)

    def _is_repo(repo_dir):
        try:
            Repo(repo_dir)
            return True  # repo exists and is valid
        except:
            return False

    def get_repo_dirs(self):
        """
        Returns a list with the directories of all repositories.
        If the repositories are not yet cloned, this method clones them first.
        """
        # read repo file
        repo_file = join("data", "python_repos.txt")
        with open(repo_file) as f:
            git_urls = f.readlines()

        # ensure we have data/repos directory
        mkdirs(join(self.data_dir, "repos"), exist_ok=True)

        # ensure that repos are cloned
        repo_dirs = []
        for git_url in git_urls:
            short_name = git_url.split["/"][-1].replace(".git", "")
            repo_dir = join(self.data_dir, "repos", short_name)
            if not (exists(repo_dir) and is_dir(repo_dir) and self._is_repo(repo_dir)):
                mkdirs(repo_dir)
            repo_dirs.append(repo_dir)

        # return list of repo dirs
        return repo_dirs

    def run_all(self):
        """
        Runs all dependencies of this experiment first, then runs the experiment itself.
        """
        for dependency in self.depends_on:
            dependency.run_all()
        self.run()

    @abstractmethod
    def run(self):
        """
        To be implemented by subclasses with code for running the experiment.
        Any dependencies of this experiment will be run first when calling run_all().
        """
        ...
