import subprocess
from os.path import join, isdir
from git import Repo


def clone_repo(git_url, working_dir):
    assert git_url.endswith(".git")
    subprocess.run("git clone " + git_url, shell=True, cwd=working_dir)
    project_name = git_url.split("/")[-1].split(".")[0]
    repo_dir = join(working_dir, project_name)
    assert isdir(repo_dir)
    print(f"Cloned repo to {repo_dir}")
    return repo_dir


def all_commits(repo_dir):
    repo = Repo(repo_dir)
    # TODO make this more robust, e.g., by supporting a main branch called "master" 
    return list(repo.iter_commits("main"))
    