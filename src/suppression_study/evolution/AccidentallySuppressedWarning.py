import json


class AccidentallySuppressedWarning:
    def __init__(self, first_commit, warning):
        self.first_commit = first_commit
        self.warning = warning

    def __lt__(self, other):
        """Sort by first_commit, then by warning. Useful for getting a deterministic order when writing to a file."""
        if self.first_commit != other.first_commit:
            return self.first_commit < other.first_commit
        else:
            return self.warning < other.warning

    def to_dict(self):
        return {
            "first_commit": self.first_commit,
            "warning": {
                "path": self.warning.path,
                "kind": self.warning.kind,
                "line": self.warning.line
            }
        }


def write_accidentally_suppressed_warnings(accidentally_suppressed_warnings, output_file):
    with open(output_file, "w") as f:
        list_of_dicts = [w.to_dict() for w in accidentally_suppressed_warnings]
        json.dump(list_of_dicts, f, indent=4)
