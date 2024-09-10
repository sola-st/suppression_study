import subprocess
from suppression_study.warnings.Warning import Warning


class MapWarningLines():
    def __init__(self, repo_dir, pre_c, c, pre_warnings, warnings):
        self.repo_dir = repo_dir
        self.pre_c = pre_c
        self.c = c
        self.pre_warnings = pre_warnings
        self.warnings = warnings

        self.refined_warnings = []
        self.mapped_warning_lines = []
        
    def check_warning_mapping(self):
        pre_file = self.pre_warnings[0].path
        file = self.warnings[0].path

        for w in self.pre_warnings:
            self.mapped_warning_lines.append(w.line)

        commit_diff_command = f"git diff --word-diff --unified=0 {self.pre_c}:{pre_file} {self.c}:{file}"
        diff_result = subprocess.run(commit_diff_command, cwd=self.repo_dir, shell=True,
            stdout=subprocess.PIPE, universal_newlines=True)
        diff_contents = diff_result.stdout
        diffs = diff_contents.split("\n")
        
        for diff_line in diffs:
            diff_line = diff_line.strip()
            if diff_line.startswith("@@"):
                tmp = diff_line.split(" ")
                base_hunk_range, base_step = get_diff_reported_range(tmp[1])
                for i, w, warning_line in zip(range(len(self.pre_warnings)), self.pre_warnings, self.mapped_warning_lines):
                    if warning_line < base_hunk_range.start:
                        self.map_helper(w, warning_line)
                    else:
                        target_hunk_range, target_step = get_diff_reported_range(tmp[2], False)
                        if warning_line in list(base_hunk_range):
                            ref_delta = warning_line - base_hunk_range.start
                            may_mapped_line = target_hunk_range.start + ref_delta
                            self.map_helper(w, may_mapped_line)
                        else:
                            move_steps = target_step - base_step
                            self.mapped_warning_lines[i] += move_steps
                
                if not self.mapped_warning_lines:
                    break

        if self.mapped_warning_lines:
            # map the warning after the last changed hunk
            for w, warning_line in zip(self.pre_warnings, self.mapped_warning_lines):
                self.map_helper(w, warning_line)
            if self.mapped_warning_lines:
                print(f"Inaccurate mapping happens. Current commit: {self.c}, file path: {file}")
                return None, False

        self.refined_warnings.append(None) # A symbol to start adding new warnings 
        is_new_warning = []
        for w in self.warnings:
            if w not in self.refined_warnings:
                self.refined_warnings.append(w)   
                is_new_warning.append(True)
        # print(f"{len(is_new_warning)}: is_new_warning")
        return self.refined_warnings, len(is_new_warning) # the number of new warnings

    def map_helper(self, warning, warning_line):
        updated_w = Warning(warning.path, warning.kind, warning_line)
        for w in self.warnings:
            if updated_w == w: # old warning
                self.refined_warnings.append(updated_w)
                self.warnings.remove(updated_w)
                break
            self.refined_warnings.append(None) # mean the self.warnings fixed/disappeared
        # do not check the mapped line for it anymore
        try:
            self.mapped_warning_lines.remove(warning_line)
        except:
            print(f"{warning_line} and {w.line}")
        self.pre_warnings.remove(warning)


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

    return reported_range, step