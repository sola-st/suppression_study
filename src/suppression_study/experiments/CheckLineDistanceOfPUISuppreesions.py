import json
from os.path import join
from matplotlib import pyplot as plt
import numpy as np
from sklearn.cluster import KMeans
    

def plot_distance_from_warning_to_suppression(distance_list, output_file, n_clusters):
    data = np.array(distance_list).reshape(-1, 1)
    
    # Perform k-means clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=0).fit(data)
    labels = kmeans.labels_
    cluster_centers = kmeans.cluster_centers_.flatten()
    grouped_data = [[] for _ in range(n_clusters)]
    
    for i, label in enumerate(labels):
        grouped_data[label].append(distance_list[i])
    
    # Count the number of elements in each cluster
    counts = [len(group) for group in grouped_data]
    
    # Round cluster centers to the nearest multiple of 100
    def round_to_nearest_100(x):
        return np.round(x / 100) * 100
    
    rounded_centers = np.array([round_to_nearest_100(center) for center in cluster_centers])
    
    # Sort centers and counts
    sorted_indices = np.argsort(rounded_centers)
    sorted_centers = rounded_centers[sorted_indices]
    
    # Define consistent group ranges
    group_ranges = []
    lower_bound = np.floor(min(distance_list) / 100) * 100  # Start at the nearest lower multiple of 100
    
    for i in range(n_clusters):
        upper_bound = sorted_centers[i]
        if i == n_clusters - 1:
            upper_bound = max(distance_list) + 1 # np.floor(max(distance_list) / 100 + 1) * 100 
        
        group_ranges.append((lower_bound, upper_bound))
        lower_bound = upper_bound
    
    # Count the number of elements in each range
    counts = [sum(lower_bound <= x < upper_bound for x in distance_list) for lower_bound, upper_bound in group_ranges]
    formatted_ranges = [f'[{int(lower_bound)},\n  {int(upper_bound)})' if i < len(group_ranges) - 1 
                        else f'[{int(lower_bound)},\n  {int(upper_bound) - 1}]' 
                        for i, (lower_bound, upper_bound) in enumerate(group_ranges)]
    plt.figure(figsize=(12, 5))
    plt.rcParams.update({'font.size': 14})
    bars = plt.bar(formatted_ranges, counts)
    for bar in bars:
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2,
                f'{int(bar.get_height())}', ha='center', va='bottom', color='black')
    
    plt.xlabel('Distance from warnings to suppression (number of lines)')
    plt.ylabel('Number of Warnings')

    # Determine the y-axis limits and ticks dynamically
    max_count = max(counts)
    y_tick_interval = 10 ** np.floor(np.log10(max_count))  # Get an appropriate interval for ticks
    plt.ylim(0, np.ceil(max_count / y_tick_interval) * y_tick_interval)
    plt.yticks(np.arange(0, plt.ylim()[1] + y_tick_interval, y_tick_interval))
    # plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig(output_file)

def main(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)

    # specify groups
    group_1= range(0, 11)
    group_2= range(11, 100)
    group_3= range(101, 1000)
    # group_4= range(1001, inf)
    count_1 = 0
    count_2 = 0
    count_3 = 0
    count_4 = 0

    distance_list = []
    for check_item in data:
        check_dict = check_item["Check"][1]
        current_suppression_line = check_dict["suppression"]["line"]
        current_warnings = check_dict["warnings"]
        for w in current_warnings:
            distance = abs(w["line"] - current_suppression_line)
            distance_list.append(distance)

            if distance in group_1:
                count_1 += 1
            elif distance in group_2:
                count_2 += 1
            elif distance in group_3:
                count_3 += 1
            else:
                count_4 += 1

    print(f"minimum distance: {min(distance_list)}, maximum: {max(distance_list)}")
    print(f"Distance {group_1}: {count_1}")
    print(f"Distance {group_2}: {count_2}")
    print(f"Distance {group_3}: {count_3}")
    print(f"Distance > 1000 lines: {count_4}")

def main_cluster(file_path, output_file, n_clusters):
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

    # option #1, use cluster as a guide to get the groups, may in different size.
    # output_file_path = join("data", "results", "distance_from_warnings_to_suppression.pdf")
    # n_clusters = 8 # with n_clusters=8, it gives meaningful clusters 
    # main_cluster(file_path, output_file_path, n_clusters)

    # option #2
    main(file_path)
