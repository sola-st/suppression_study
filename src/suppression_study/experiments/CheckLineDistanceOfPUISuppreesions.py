import json
from os.path import join
from matplotlib import pyplot as plt
import numpy as np
from sklearn.cluster import KMeans
    

def plot_distance_from_warning_to_suppression(float_list, output_file, n_clusters):
    data = np.array(float_list).reshape(-1, 1)
    
    # Perform k-means clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=0).fit(data)
    labels = kmeans.labels_
    cluster_centers = kmeans.cluster_centers_.flatten()

    # Create a list of lists to hold grouped data
    grouped_data = [[] for _ in range(n_clusters)]
    
    for i, label in enumerate(labels):
        grouped_data[label].append(float_list[i])
    # Count the number of elements in each cluster
    counts = [len(group) for group in grouped_data]
    
    # Sort groups by the cluster center
    sorted_indices = np.argsort(cluster_centers)
    sorted_counts = np.array(counts)[sorted_indices]
    sorted_centers = np.array(cluster_centers)[sorted_indices]

    # Define group ranges for x-axis labels, ensuring that the ranges are contiguous
    sorted_centers = np.sort(sorted_centers)
    group_ranges = []
    for i in range(n_clusters):
        if i == 0:
            lower_bound = 0
        else:
            lower_bound = sorted_centers[i - 1] + 1
        
        if i == n_clusters - 1:
            upper_bound = max(float_list)
        else:
            upper_bound = sorted_centers[i] + 1

        # print(f"L: {lower_bound}\tU: {upper_bound}")
        # group_ranges.append(f'{lower_bound:.1f} - {upper_bound:.1f}')
        if i == n_clusters - 1:
            group_ranges.append(f'[{lower_bound:.1f},\n  {upper_bound:.1f}]')
        else:
            group_ranges.append(f'[{lower_bound:.1f},\n  {upper_bound:.1f})')

    plt.figure(figsize=(12, 5))
    plt.rcParams.update({'font.size': 16})
    bars = plt.bar(group_ranges, sorted_counts) #, color='blue')
    for bar in bars:
        plt.text(bar.get_x() + bar.get_width() / 2, 0.96 * bar.get_height(),
                f'{int(bar.get_height())}', ha='center', va='bottom', color='black')
    # plt.xticks(group_ranges, rotation=30)
    plt.xlabel('Distance from warnings to suppression (number of lines)')
    plt.ylabel('Number of Warnings')
    # Remove decimal places from x-axis ticks
    plt.gca().xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    plt.tight_layout()
    plt.savefig(output_file)

def main(file_path, output_file, n_clusters):
    with open(file_path, 'r') as file:
        data = json.load(file)

    distance_list = []
    for check_item in data:
        check_dict = check_item["Check"][1]
        current_suppression_line = check_dict["suppression"]["line"]
        current_warnings = check_dict["warnings"]
        for w in current_warnings:
            distance = abs(w["line"] - current_suppression_line)
            distance_list.append(distance)
    print(f"Number of warnings: {len(distance_list)}")
    plot_distance_from_warning_to_suppression(distance_list, output_file, n_clusters)


if __name__ == "__main__":
    file_path = join("data", "results", "inspection_accidental_commits.json")
    output_file_path = join("data", "results", "distance_from_warnings_to_suppression.pdf")
    n_clusters = 8 # with n_clusters=8, it gives meaningful clusters 
    main(file_path, output_file_path, n_clusters)
    

