"""
Helper code to produce outputs in LaTeX, e.g., tables or macros.
"""

from typing import List


class LaTeXTable:
    def __init__(self, column_names: List[str]):
        self.column_names = column_names
        self.rows = []

    def add_row(self, row: List):
        self.rows.append([str(x) for x in row])

    def add_separator(self):
        self.rows.append("SEPARATOR")

    def to_latex(self):
        latex = "\\begin{tabular}{}\n"
        latex += "\\toprule\n"
        latex += " & ".join(self.column_names) + "\\\\\n"
        latex += "\\midrule\n"
        for row in self.rows:
            if row == "SEPARATOR":
                latex += "\\midrule\n"
            else:
                latex += " & ".join(row) + "\\\\\n"
        latex += "\\bottomrule\n"
        latex += "\\end{tabular}"
        return latex
