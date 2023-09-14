"""
Helper functions that operate on a Git repositories.
"""

from git.repo import Repo
from os import sep
from os.path import normpath


def get_name_of_main_branch(repo: Repo):
    """
    Returns the name of the main branch of the given repository.
    (Git does not have a concept of a "main branch", so this is a guess
    based on common naming conventions.)
    """
    candidates = [h.name for h in repo.heads]
    if "master" in candidates:
        return "master"
    elif "main" in candidates:
        return "main"
    else:
        return candidates[0]


def repo_dir_to_name(repo_dir):
    return normpath(repo_dir).split(sep)[-1]
