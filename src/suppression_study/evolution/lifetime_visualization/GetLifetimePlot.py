import matplotlib.pyplot as plt
import numpy as np
import csv


def load_data_from_csv(csv_filename):
    '''
    Target file header = [
        "day_range",
        "day_group_num_removed",
        "day_group_num_lasting",
        "commit_range",
        "commit_group_num_removed",
        "commit_group_num_lasting",
        "commit_based_rates_range",
        "rate_group_num_removed",
        "rate_group_num_lasting",
    ]
    '''

    with open(csv_filename, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        header = next(csv_reader)
        data = {col: [] for col in header}
        
        for row in csv_reader:
            for col, value in zip(header, row):
                data[col].append(value)
                
    return data

def visualize_lifetime(lifetime_group_output_csv):
    # Visualize data in lifetime_group_output_csv to output_png
    data = load_data_from_csv(lifetime_group_output_csv)
    output_png = lifetime_group_output_csv.replace("_groups.csv", "_visualization.png")
    
    plt.rcParams["figure.figsize"] = (12, 5)
    
    fig, (ax1, ax2, ax3) = plt.subplots(nrows=1, ncols=3)
    fig.suptitle("Lifetime of all repositories with three different standards.", fontsize=11, horizontalalignment="center")
  
    for ax in (ax1, ax2, ax3):
        for tick in ax.get_xticklabels():
            tick.set_rotation(30)

    ax1.set_xlabel("# days")
    ax1.set_ylabel("# suppression")
    bottom1 = np.zeros(len(data['day_range']))
    for keyword in ['day_group_num_removed', 'day_group_num_lasting']:
        d_num = np.array(data[keyword], dtype=np.float64)
        # label legend
        ax1.bar(data['day_range'], d_num, label=keyword.split('_')[-1], bottom=bottom1)
        bottom1 += d_num
    ax1.legend(loc="upper right")

    ax2.set_xlabel("# commits")
    bottom2 = np.zeros(len(data['commit_range']))
    for keyword in ['commit_group_num_removed', 'commit_group_num_lasting']:
        c_num = np.array(data[keyword], dtype=np.float64)
        ax2.bar(data['commit_range'], c_num, label=keyword.split('_')[-1], bottom=bottom2)
        bottom2 += c_num

    ax3.set_xlabel("# commit-based rates")
    bottom3 = np.zeros(len(data['commit_based_rates_range']))
    for keyword in ['rate_group_num_removed', 'rate_group_num_lasting']:
        rate = np.array(data[keyword], dtype=np.float64)
        ax3.bar(data['commit_based_rates_range'], rate, label=keyword.split('_')[-1], bottom=bottom3)
        bottom3 += rate

    plt.tight_layout()
    plt.subplots_adjust(top=0.9)
    plt.savefig(output_png)
    print("Visualization done.")
