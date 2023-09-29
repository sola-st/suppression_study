import csv
from multiprocessing import Pool, cpu_count
import os
from os.path import join
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from suppression_study.experiments.Experiment import Experiment
from suppression_study.utils.GitRepoUtils import repo_dir_to_name


def _plot_distribution(suppression_num_csv, plot_output, start_commit_index, end_commit_index):
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

    # set the select 1000 commits to a different color
    # given commit_index starts from 0
    start_commit_index = str(int(start_commit_index) + 1)
    end_commit_index = str(int(end_commit_index) + 1)

    for i in indexes: # keep consistency with indexes, start from 1.
        if i == start_commit_index or i == end_commit_index:
            plt.scatter(i, num_suppressions[int(i)-1], s=10, color='orange')

    plt.xlabel("Nr. commit")
    plt.ylabel("Number of suppressions")
    plt.savefig(plot_output)

class DistributionOfSuppressionsNumOnAllCommits(Experiment):
    """
    Experiment that plots a distribution of the number of suppression
    in all the commits of the studied repositories.
    """
    def read_csv_to_dict(self):
        start_end_commits_1000_csv = join("data", "results", "start_end_commits_1000.csv")
        start_end_data_dict = {}
    
        with open(start_end_commits_1000_csv, 'r') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                repo_name = row[0]
                start_commit_index = row[2] 
                end_commit_index = row[4]
                repo_data = {"start_commit_index": start_commit_index, 
                             "end_commit_index": end_commit_index}
                start_end_data_dict[repo_name] = repo_data
        return start_end_data_dict
    
    def run(self):
        # prepare repositories
        repo_dirs = self.get_repo_dirs()

        # prepare data for start and end commits
        start_end_data_dict = self.read_csv_to_dict()

        # start to collect args for generating plot
        args_for_all_repos = []
        for repo_dir in repo_dirs:
            repo_name = repo_dir_to_name(repo_dir)
            common_folder = join("data", "results", repo_name)
            repo_data = start_end_data_dict[repo_name]
            start_commit_index = repo_data["start_commit_index"]
            end_commit_index = repo_data["end_commit_index"]
            suppression_num_csv= join(common_folder ,"all_suppression_nums.csv")
            plot_output = join(common_folder,"distribution_suppression_num_color2.pdf")
            args = [suppression_num_csv, plot_output, start_commit_index, end_commit_index]
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
