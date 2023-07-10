import argparse

'''
Each repository has different number of commits.
In this study, default setting to 1000 commits for all target repositories.
Use 'gap_size' to get 1000 commits.
'''

parser = argparse.ArgumentParser(description="Get 1000 commits of target repository.")
parser.add_argument("--all_commit_csv", help="path to .csv file with all commits of target repository", required=True)

def get_1000_commits(all_commit_csv):
    '''
    Receive the all_commit_csv file, return a file with selected 1000 commits.
    Store it to the same path with all_commit_csv, file name endswith "_1000.csv"

    all commits, from latest to oldest, related to "filter_repositories.py"
    '''
    with open(all_commit_csv, "r") as f: 
        commit_lines = f.readlines()
    f.close()
    all_commit_num = commit_lines.__len__()
    gap_size = round(all_commit_num / 1000, 3)

    selected_commit_num=0 # default target 1000
    current_position=0
    left_delta=0
    right_delta=0
    next_mark=""
    update_position=""
    select_next_mark=""
    selected_1000 = []

    line_index = 0
    for line in commit_lines:
        if line_index == 0: 
            selected_1000.append(line)
            selected_commit_num +=1
            next_mark = "move"
            update_position = "update"
        else: # lines except first line.
            if select_next_mark == "select-next":
                selected_1000.append(line)
                selected_commit_num +=1
                next_mark = "move"
                update_position = "update"
            if next_mark == "move":
                if update_position == "update":
                    current_position=round(current_position + gap_size, 3)
                if (current_position - line_index) < 1:
                    left_delta = round(current_position - line_index, 3)
                    next_line_index = line_index + 1
                    right_delta = round(next_line_index - current_position, 3)
                    if left_delta <= right_delta: # if equal, choose left side.
                        selected_1000.append(line)
                        selected_commit_num +=1
                        next_mark = "move"
                        update_position = "update"
                    else:
                        next_mark = ""
                        select_next_mark = "select-next"
                        update_position = ""
                else: # keep moving to find another line fit to gap_size rule
                    next_mark="move"
                    select_next_mark=""
                    update_position=""
        line_index+=1
        if selected_commit_num == 1000: 
            break


    commit_1000_csv = all_commit_csv.replace(".csv", "_1000.csv")
    with open(commit_1000_csv, "w") as w:
        to_write=""
        start_from_oldest = []
        # make the output csv file with order 'from oldest to latest commit'
        start_from_oldest = reversed(selected_1000) # selected_1000.reverse() 
        for line in start_from_oldest: 
            if not line.endswith("\n"):
                line = line + "\n"
            to_write = to_write + line
        w.write(to_write)
        print("Select 1000 commits, Done.")


if __name__=="__main__":
    args = parser.parse_args()
    all_commit_csv = args.all_commit_csv
    get_1000_commits(all_commit_csv)
