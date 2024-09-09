import matplotlib.pyplot as plt
import numpy as np

from suppression_study.utils.VisualizationLoadData import load_data_from_csv


def visualize_lifetime(lifetime_group_output_csv):
    # Visualize data in lifetime_group_output_csv to output_pdf
    '''
    Target file header = [
        "day_range",
        "day_group_num_removed",
        "day_group_num_lasting",
        "commit_based_rates_range",
        "rate_group_num_removed",
        "rate_group_num_lasting",
    ]
    '''
    data = load_data_from_csv(lifetime_group_output_csv)
    output_pdf = lifetime_group_output_csv.replace("_groups.csv", "_visualization.pdf")
    
    plt.rcParams["figure.figsize"] = (12, 4)
    plt.rcParams.update({'font.size': 14})
    fig, (ax_day, ax_rate) = plt.subplots(nrows=1, ncols=2)

    for ax in (ax_day, ax_rate):
        for tick in ax.get_xticklabels():
            tick.set_rotation(30)

    ax_day.set_xlabel("Days")
    ax_day.set_ylabel("Number of suppressions")
    bottom_day = np.zeros(len(data['day_range']))
    legend_labels = []  # Create an empty list to store legend labels

    for keyword in ['day_group_num_removed', 'day_group_num_lasting']:
        d_num = np.array(data[keyword], dtype=np.float64)
        # label legend
        legend_label = keyword.split('_')[-1]
        if legend_label == "lasting":
            legend_label = "never removed"
        ax_day.bar(data['day_range'], d_num, label=legend_label, bottom=bottom_day)
        legend_labels.append(legend_label)  # Add the legend label to the list
        bottom_day += d_num

    ax_rate.set_xlabel("Percentage of all studied commits")
    bottom_rate = np.zeros(len(data['commit_based_rates_range']))

    for keyword in ['rate_group_num_removed', 'rate_group_num_lasting']:
        rate = np.array(data[keyword], dtype=np.float64)
        ax_rate.bar(data['commit_based_rates_range'], rate, label=keyword.split('_')[-1], bottom=bottom_rate)
        bottom_rate += rate

    ax_rate.legend(legend_labels, loc="upper right")

    plt.tight_layout()
    plt.savefig(output_pdf)
    print("Visualization done.")
