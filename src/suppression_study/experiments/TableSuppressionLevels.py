import json
from os.path import join


def generate_table(data):
    if data.get("detailed"):
        first_detail = data["detailed"][0]
        first_detail_key = list(first_detail.keys())[0]
        column_names = ["Project"] + list(first_detail[first_detail_key].keys())
        column_names.remove("all")
        column_names.append("all")

    num_columns = len(column_names)
    alignment_string = 'l' + 'r' * (num_columns - 1)

    latex_table = f"""\\begin{{table}}[t]
        \\small
        \\centering
        \\caption{{The number of useless and all suppressions at different levels.}}
        \\label{{tab:suppression_levels}}
        \\begin{{tabular}}{{{alignment_string}}}
        \\toprule
        {' & '.join([name.capitalize().replace('_', ' ') for name in column_names])} \\\\
        \\midrule
        """

    # Loop through the detailed components and add rows to the LaTeX table
    for component in data["detailed"]:
        for name, stats in component.items():
            row_data = [name] + [stats.get(key, '') for key in column_names[1:]]
            row_data_str = ' & '.join(row_data)
            latex_table += f"{row_data_str}\\\\\n\t"

    summary_data = [data.get(key, '') for key in column_names[1:]]
    summary_data_str = 'Overall & ' + ' & '.join(summary_data)
    latex_table += "\\midrule\n\t"
    latex_table += f"{summary_data_str}\\\\"

    latex_table += """
        \\bottomrule
        \\end{tabular}
    \\end{table}
        """
    
    return latex_table

if __name__=="__main__":
    file_folder = join("data", "results", "suppression_levels")
    json_filename = join(file_folder, "overall.json")
    output_file = join(file_folder, "overall_table.tex")

    with open(json_filename, 'r') as file:
        data = json.load(file)
    latex_table = generate_table(data)

    with open(output_file, "w") as f:
        f.writelines(latex_table)
    print("Done.")
