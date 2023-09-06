from typing import Dict
import tempfile
import shutil
from os.path import join


class SuppressionRemover():
    """
    Removes one suppression at a time from a repository.
    After each call of remove_suppression(), call restore()
    to restore the repository to its original state.
    """

    def __init__(self, repo_dir):
        self.repo_dir = repo_dir

    def remove_suppression(self, suppression):
        self.file = join(self.repo_dir, suppression.path)

        # save unmodified file for later
        self.tmp_dir = tempfile.mkdtemp()
        self.stored_file = join(self.tmp_dir, "orig_file.py")
        shutil.copyfile(self.file, self.stored_file)

        # remove the suppression
        with open(self.file, "r") as f:
            lines = f.readlines()

        assert suppression.text in lines[suppression.line - 1]
        lines[suppression.line - 1] = lines[suppression.line - 1].replace(suppression.text, "")
        
        # make sure to not leave trailing whitespace
        # (which would trigger new warnings, e.g., by Pylint)
        if lines[suppression.line - 1].endswith("\n"):
            lines[suppression.line - 1] = lines[suppression.line - 1].rstrip() + "\n"
        else: 
            lines[suppression.line - 1] = lines[suppression.line - 1].rstrip()
        
        with open(self.file, "w") as f:
            f.writelines(lines)

    def restore(self):
        shutil.copyfile(self.stored_file, self.file)
        shutil.rmtree(self.tmp_dir)