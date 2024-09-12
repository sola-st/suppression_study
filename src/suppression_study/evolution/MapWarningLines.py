import subprocess
# Sept. 12, just keep the file here, but this is not necessary for old experiment setting.

class MapWarningLines():
    def __init__(self, repo_dir, pre_c, c, pre_warnings, warnings):
        self.repo_dir = repo_dir
        self.pre_c = pre_c
        self.c = c
        self.pre_warnings = pre_warnings
        self.warnings = warnings

        self.new_warning_hinder = []
        self.overall_new_warning_counts = 0
        
    def check_warning_mapping(self):
        pre_file = self.pre_warnings[0].path
        file = self.warnings[0].path

        commit_diff_command = f"git diff --unified=0 {self.pre_c}:{pre_file} {self.c}:{file}"
        diff_result = subprocess.run(commit_diff_command, cwd=self.repo_dir, shell=True,
            stdout=subprocess.PIPE, universal_newlines=True)
        diff_contents = diff_result.stdout
        diffs = diff_contents.split("\n")
        
        for diff_line in diffs:
            diff_line = diff_line.strip()
            if diff_line.startswith("@@"):
                tmp = diff_line.split(" ")
                base_hunk_range = get_diff_reported_range(tmp[1])
                target_hunk_range = get_diff_reported_range(tmp[2], False)
                base_hunk_lines = list(base_hunk_range)
                target_hunk_lines = list(target_hunk_range)
                previous_warning_line_in_hunk = [w.line for w in self.pre_warnings if w.line in base_hunk_lines]
                current_warning_line_in_hunk = [w.line for w in self.warnings if w.line in target_hunk_lines]
                previous_len = len(previous_warning_line_in_hunk)
                current_len = len(current_warning_line_in_hunk)

                if previous_len < current_len:
                    # new warning occurs
                    new_warning_count = current_len - previous_len
                    self.overall_new_warning_counts += new_warning_count
                    self.new_warning_hinder.append({
                        "new_warnings": new_warning_count,
                        "base_hunk": f"{base_hunk_range}",
                        "target_hunk": f"{target_hunk_range}", 
                        "mapped_previous_warnings": f"{previous_warning_line_in_hunk}",
                        "potential_new_warnings": f"{current_warning_line_in_hunk}"})

        return self.new_warning_hinder, self.overall_new_warning_counts
    

def get_diff_reported_range(meta_range, base=True):
    '''
    Get range from diff results:
    Input: 23,4  or  23
    Return: 
        * a range [ ) : end is not covered
        * step, 4 and 0 in the input examples, respectively
        * start+step, that is the line number of last line in base hunk.
    '''

    start = None
    step = None
    end = None
    reported_range = None

    sep = "+"
    if base == True:
        sep = "-"

    if "," in meta_range:
        tmp = meta_range.lstrip(sep).split(",")
        start = int(tmp[0])
        step = int(tmp[1]) 
    else:
        start = int(meta_range.lstrip(sep))
        step = 1
    end = start + step

    reported_range = range(start, end) # [x, y)

    return reported_range