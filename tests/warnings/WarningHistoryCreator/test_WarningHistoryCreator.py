from suppression_study.util.RepoUtil import clone_repo
from suppression_study.checkers import GetPylintWarnings
from tempfile import TemporaryDirectory
from suppression_study.warnings.WarningHistoryCreator import WarningHistoryCreator
from os.path import join, isfile


def test_pylint2():
    with TemporaryDirectory() as tmp_dir:
        repo_dir = clone_repo("https://github.com/michaelpradel/suppression-test-python-pylint2.git", tmp_dir)
        
        creator = WarningHistoryCreator(repo_dir, GetPylintWarnings)
        creator.create_history()
        dest_file = join(tmp_dir, "history.json")
        creator.to_json(dest_file)
        
        assert isfile(dest_file)
        # TODO add more assertions: compare content of file with expected content

