from os import makedirs
from os.path import join
from shutil import move
from multiprocessing import Pool, cpu_count
from tempfile import TemporaryDirectory
from suppression_study.experiments.Experiment import Experiment
from suppression_study.checkers.GetPylintWarnings import main as get_pylint_warnings
from suppression_study.checkers.GetMypyWarnings import main as get_mypy_warnings
from suppression_study.utils.GitRepoUtils import repo_dir_to_name


class RunCheckersOnLatestCommit(Experiment):
    """
    Runs both pylint and mypy on the latest commit of the project,
    where "latest" means the commit we've set as the latest
    to consider in the study.
    """

    def run(self):
        # prepare repositories
        self.get_repo_dirs()
        repo_dir_to_commit_id = self.checkout_latest_commits()

        # run pylint and mypy on different repos (in parallel)
        args_for_all_repos = []
        for repo_dir, commit_id in repo_dir_to_commit_id.items():
            args_pylint = ["pylint", repo_dir, commit_id]
            # TODO bring back mypy support
            # args_mypy = ["mypy", repo_dir, commit_id]
            # args_for_all_repos.extend([args_pylint, args_mypy])
            args_for_all_repos.extend([args_pylint])

        cores_to_use = cpu_count() - 1  # leave one core for other processes
        print(f"Using {cores_to_use} cores in parallel.")
        with Pool(processes=cores_to_use) as pool:
            pool.map(run_checker_on_repo, args_for_all_repos)


def run_checker_on_repo(args):
    checker, repo_dir, commit_id = args
    repo_name = repo_dir_to_name(repo_dir)
    target_dir = join("data", "results", repo_name, "commits", commit_id)
    target_file = join(target_dir, f"{checker}_warnings.csv")

    with TemporaryDirectory() as tmp_result_dir:
        print(f"Running {checker} on {repo_name} at {commit_id}")
        if checker == "pylint":
            get_pylint_warnings(repo_dir, commit_id, tmp_result_dir)
        elif checker == "mypy":
            get_mypy_warnings(repo_dir, commit_id, tmp_result_dir)
        tmp_path = join(
            tmp_result_dir, f"checker_results/{checker}/{commit_id}_warnings.csv")
        makedirs(target_dir, exist_ok=True)
        move(tmp_path, target_file)
        print(f"Have copied {checker} warnings into {target_file}")


if __name__ == "__main__":
    RunCheckersOnLatestCommit().run()
