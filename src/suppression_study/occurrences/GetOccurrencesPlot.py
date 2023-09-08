import csv
import matplotlib.pyplot as plt
import numpy as np

from suppression_study.utils.VisualizationLoadData import load_data_from_csv


def visualization_occurrence(occurrences_csv):
    # Visualize data in occurrences_csv to output_pdf
    '''
    Target file header = [
        "warning_type",
        "occurrences",
    ]
    '''
    data = load_data_from_csv(occurrences_csv)
    output_pdf = occurrences_csv.replace(".csv", "_visualization.pdf")

    warning_types = data["warning_type"]
    occurrences_tmp = data["occurrences"]  # str
    occurrences = [int(i) for i in occurrences_tmp] # int

    total = sum(occurrences)

    plt.figure(figsize=(10, 6))

    x = np.array(warning_types)
    y = np.array(occurrences)
    plt.ylim(0, round(max(occurrences) * 1.1))
    plt.bar(x, y)  # , width=0.6

    for a, b in zip(x, y):
        plt.text(a, b, str(str(b) + "\n" + '{:.2f}'.format(b / total * 100)) + '%', ha="center")

    plt.xticks(rotation=60)
    plt.xlabel("Warning types")
    plt.ylabel("# Occurrences")
    plt.subplots_adjust(left=0.2, right=0.9, bottom=0.3)
    plt.title("Occurrences of different warning types")
    plt.savefig(output_pdf)
    print("Visualization done.")