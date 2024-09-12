import json


class AccidentallySuppressedWarning:
    def __init__(self, previous_commit, commit, suppression, previous_warnings, warnings):
        self.previous_commit = previous_commit
        self.commit = commit
        self.suppression = suppression
        self.previous_warnings = previous_warnings
        self.warnings = warnings

    def __lt__(self, other):
        """Sort based on attributes. Useful for getting a deterministic order when writing to a file."""
        if self.previous_commit != other.previous_commit:
            return self.previous_commit < other.previous_commit
        elif self.commit != other.commit:
            return self.commit < other.commit
        elif self.suppression != other.suppression:
            return self.suppression < other.suppression
        elif self.previous_warnings != other.previous_warnings:
            return self.previous_warnings < other.previous_warnings
        else:
            return self.warnings < other.warnings

    def to_dict(self):
        d = {
            "previous_commit": self.previous_commit,
            "commit": self.commit,
            "suppression": {
                "path": self.suppression.path,
                "text": self.suppression.text,
                "line": self.suppression.line
            },
            "previous_warnings": [{"path": w.path, "kind": w.kind, "line": w.line} for w in sorted(self.previous_warnings)],
            "warnings": [{"path": w.path, "kind": w.kind, "line": w.line} for w in sorted(self.warnings)]
        }
        return d


def write_accidentally_suppressed_warnings(accidentally_suppressed_warnings, output_file):
    with open(output_file, "w") as f:
        list_of_dicts = [w.to_dict() for w in accidentally_suppressed_warnings]
        json.dump(list_of_dicts, f, indent=4)