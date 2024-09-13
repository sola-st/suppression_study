import csv
from os.path import join
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from suppression_study.experiments.Experiment import Experiment
from suppression_study.utils.GitRepoUtils import repo_dir_to_name


def _plot_distribution(repo_names, suppression_nums_csvs, output_pdf, start_commit_indices, end_commit_indices):
    fig, axes = plt.subplots(4, 3, figsize=(12, 12)) # figsize=(22, 12)
    fix_font_size = 12
    for i, (suppression_nums_csv, start_commit, end_commit) in enumerate(
        zip(suppression_nums_csvs, start_commit_indices, end_commit_indices)
    ):
        # Skip the 11th and 12th positions
        if i >= 10:
            break

        row, col = divmod(i, 3)
        ax = axes[row, col]

        indexes = []
        num_suppressions = []

        csv_reader = csv.reader(open(suppression_nums_csv, 'r'))
        for row in csv_reader:
            index = int(row[0])
            num_suppression = int(row[1])
            indexes.append(index)
            num_suppressions.append(num_suppression)

        # 's' controls the size of the markers
        blue_scatter = ax.scatter(indexes, num_suppressions, s=2, label='Commits on the main/master branch')

        # Configure x-axis and y-axis tick locators to use MaxNLocator
        ax.xaxis.set_major_locator(MaxNLocator(prune='both'))
        ax.yaxis.set_major_locator(MaxNLocator(prune='both'))
        ax.tick_params(axis='both', which='both', labelsize=fix_font_size) 

        # Set the select 1000 commits to a different color
        for index in indexes:
            if index == start_commit or index == end_commit:
                orange_scatter = ax.scatter(
                    index, num_suppressions[index - 1], s=10, color='orange', label='Start/end commit'
                )

        ax.set_title(repo_names[i], fontsize=fix_font_size)

    # Add agenda text to the last two subplots
    # Merge the last two subplots (positions 10 and 11)
    ax10 = axes[3, 1]
    ax11 = axes[3, 2]
    for ax in [ax10, ax11]:
        ax.remove()
    ax10_11 = fig.add_subplot(4, 3, 11)
    ax10_11.axis('off')  # Remove axis labels
    ax10_11.legend(handles=[blue_scatter, orange_scatter], fontsize=fix_font_size, loc="upper left")
    ax10_11.text(
        0.05, 0.2, "X-axis: Number of commits\nY-axis: Number of suppressions", fontsize=fix_font_size, ha='left', va='bottom'
    )

    for ax in axes.flat:
        ax.tick_params(axis='x', labelrotation=45)

    plt.tight_layout()
    plt.savefig(output_pdf)


def _plot_distribution_overall_plot(repo_names, suppression_nums_csvs, output_pdf, start_commit_indices, end_commit_indices):
    plt.rcParams.update({'font.size': 24})
    fig, ax = plt.subplots(figsize=(10, 6)) 

    # Define colors for each dataset
    colors = ['deeppink', 'brown', 'red', 'purple', 'darkorange', 'cyan', 'magenta', 'green', 'black', 'blue']  

    csv_lens = []
    for i, (suppression_nums_csv, start_commit, end_commit, color) in enumerate(
            zip(suppression_nums_csvs, start_commit_indices, end_commit_indices, colors)
    ):
        # Load data from CSV
        indexes = []
        num_suppressions = []
        with open(suppression_nums_csv, 'r') as csv_file:
            csv_reader = csv.reader(csv_file)
            for row in csv_reader:
                index = int(row[0])
                num_suppression = int(row[1])
                indexes.append(index)
                num_suppressions.append(num_suppression)
        
        csv_lens.append(len(num_suppressions))

        # Plot the data
        ax.scatter(indexes, num_suppressions, s=2, color=color) # label=repo_names[i],

        # Highlight start and end commits
        for index in [start_commit, end_commit]:
            ax.scatter(index, num_suppressions[index - 1], s=400, marker='*', color=color)

        last_commit_num = len(num_suppressions)
        ax.annotate(f'{repo_names[i]}', xy=(last_commit_num, num_suppressions[last_commit_num - 1]),
                    xytext=(last_commit_num + 10, num_suppressions[last_commit_num - 1]), color=color)
        
    # Set legend for star marker
    ax.scatter([], [], s=400, marker='*', color='gray', label='Selected start / end commit')
    ax.legend()

    # set to get extra space on the end of x-axis, 
    # otherwise the repo name labels will out of the plot border
    ticks = ax.get_xticks()
    tick_interval = ticks[1] - ticks[0]
    max_index = max(csv_lens)
    quotient, remainder = divmod(max_index, tick_interval)
    if remainder > 0:
        max_quotient = quotient + 2.5 # 1 for cover the remainder, 1.5 for extra space
    ax.set_xlim(left=ax.get_xlim()[0], right=tick_interval*max_quotient)

    # Configure x-axis and y-axis tick locators to use MaxNLocator
    ax.xaxis.set_major_locator(MaxNLocator(prune='both'))
    ax.yaxis.set_major_locator(MaxNLocator(prune='both'))
    ax.tick_params(axis='both', which='both')

    # Set legend and axis labels
    # ax.legend()
    ax.set_xlabel('Number of commits')
    ax.set_ylabel('Number of suppressions')

    plt.tight_layout(pad=0)
    plt.savefig(output_pdf)


class DistributionOfSuppressionsNumOnMainCommits(Experiment):
    """
    Generate a figure with 10 subplots
    show the relationship between the number of suppressions and main branch commits

    Depends on:
     * CountOfSuppressionsNumOnMainCommits - get the number of suppressions in the repositories
     * Get1000Commits - get the start and end commit of the repositories
    """

    def run(self):
        suppression_nums_csvs = []
        repo_names = []
        start_commit_indices = []
        end_commit_indices = []

        # prepare repositories
        repo_dirs = self.get_repo_dirs()

        # get all csv files that records the suppression nums
        for repo_dir in repo_dirs:
            repo_name = repo_dir_to_name(repo_dir)
            repo_names.append(repo_name)
            suppression_num_csv = join("data", "results", repo_name, "main_suppression_nums_pylint.csv")
            suppression_nums_csvs.append(suppression_num_csv)

        # get all start and end commit indices, index number based on only main branch
        # eg,. main branch has 4,000 commits, and the selected 1,000 commits starts from 1,800th commit
        # in this case, the start index is 1,799
        start_end_commits_csv = join("data", "results", "start_end_commits_1000.csv")
        # repo_name, all_main_commit_num, first_commit, first_commit_index, end_commit, end_commit_index
        #  the repos order is the same as repo_dirs
        csv_reader = csv.reader(open(start_end_commits_csv, 'r'))
        for row in csv_reader:
            start_index = int(row[3]) + 1
            end_index = int(row[5]) + 1
            start_commit_indices.append(start_index)
            end_commit_indices.append(end_index)

        # two options to get a plot
        # 1. subplot
        _plot_distribution(
            repo_names,
            suppression_nums_csvs,
            join("data", "results", "subplots10_suppression_num_on_main.pdf"),
            start_commit_indices,
            end_commit_indices,
        )

        # 2. a big plot to show all repos
        _plot_distribution_overall_plot(
            repo_names,
            suppression_nums_csvs,
            join("data", "results", "repo10_suppression_num_on_main.pdf"),
            start_commit_indices,
            end_commit_indices,
        )


if __name__ == "__main__":
    DistributionOfSuppressionsNumOnMainCommits().run()
