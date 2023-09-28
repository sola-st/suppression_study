import csv
from multiprocessing import Pool, cpu_count
from os.path import join
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from suppression_study.experiments.Experiment import Experiment
from suppression_study.utils.GitRepoUtils import repo_dir_to_name


def _plot_distribution(suppression_num_csv, plot_output):
    indexes = []
    num_suppressions = []

    csv_reader = csv.reader(open(suppression_num_csv, 'r'))
    for row in csv_reader:
        index = row[0]
        num_suppression = row[1]
        indexes.append(index)
        num_suppressions.append(num_suppression)

    plt.scatter(indexes, num_suppressions, s=2)  # 's' controls the size of the markers

    # Configure x-axis and y-axis tick locators to use MaxNLocator
    ax = plt.gca()
    ax.xaxis.set_major_locator(MaxNLocator(prune='both'))
    ax.yaxis.set_major_locator(MaxNLocator(prune='both'))

    plt.xlabel("Nr. commit")
    plt.ylabel("Number of suppressions")
    plt.savefig(plot_output)

class DistributionOfSuppressionsNumOnAllCommits(Experiment):
    """
    Experiment that plots a distribution of the number of suppression
    in all the commits of the studied repositories.
    """

    def run(self):
        # prepare repositories
        repo_dirs = self.get_repo_dirs()

        args_for_all_repos = []
        for repo_dir in repo_dirs:
            repo_name = repo_dir_to_name(repo_dir)
            common_folder = join("data", "results", repo_name)
            suppression_num_csv= join(common_folder ,"all_suppression_nums.csv")
            plot_output = join(common_folder,"distribution_suppression_num.pdf")
            args = [suppression_num_csv, plot_output]
            args_for_all_repos.append(args)
            
        cores_to_use = cpu_count() - 1 # leave one core for other processes
        print(f"Using {cores_to_use} cores to get the plots of suppression nums in repositories.")
        with Pool(processes=cores_to_use) as pool:
            pool.map(suppression_wrapper, args_for_all_repos)
        print("Done")


def suppression_wrapper(args):
    _plot_distribution(*args)


if __name__ == "__main__":
    DistributionOfSuppressionsNumOnAllCommits().run()
