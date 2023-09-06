def sort_and_compare_files(actual_file, expected_file):
    with open(expected_file, "r") as f:
        expected_lines = f.readlines()
    expected_lines.sort()

    with open(actual_file, "r") as f:
        actual_lines = f.readlines()
    actual_lines.sort()

    assert len(actual_lines) == len(expected_lines)
    for actual, expected in zip(actual_lines, expected_lines):
        assert actual == expected


def exactly_compare_files(actual_file, expected_file):
    with open(expected_file, "r") as f:
        expected_lines = f.readlines()

    with open(actual_file, "r") as f:
        actual_lines = f.readlines()

    assert len(actual_lines) == len(expected_lines)
    for actual, expected in zip(actual_lines, expected_lines):
        assert actual == expected
