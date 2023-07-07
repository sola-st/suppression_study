import sys
import subprocess
import pytest

def test_output():
    out = subprocess.check_output(["python", "src/checkers/GetPylintWarnings.py",
                             "--repo", "dummy",
                             "--results", "data",
                             "--commit", "dummy"]).decode(sys.stdout.encoding)
    assert out == ""
    with open("data/pylint_warnings.txt", "r") as f:
        assert f.read() == "This is a dummy file\n"