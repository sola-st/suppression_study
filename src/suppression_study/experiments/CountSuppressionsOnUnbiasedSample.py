from os.path import join
from suppression_study.experiments.CountSuppressionsOnLatestCommit import CountSuppressionsOnLatestCommit


class CountSuppressionsOnUnbiasedSample(CountSuppressionsOnLatestCommit):
    def __init__(self):
        super().__init__()
        self.repo_file = join("data", "python_repos_46_using_pylint.txt")


if __name__ == "__main__":
    CountSuppressionsOnUnbiasedSample().run()
