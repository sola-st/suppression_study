import argparse
from os.path import join

parser = argparse.ArgumentParser(description="Gather all Pylint warnings in a specific commit")
parser.add_argument("--repo", help="Directory with the repository to check", required=True)
parser.add_argument("--results", help="Result directory of the given repository", required=True)
parser.add_argument("--commit", help="Commit to check", required=True)


if __name__ == "__main__":
    args = parser.parse_args()
    
    # TODO implement this script
    # for now, it only writes a dummy file to the results directory
    with open(join(args.results, "pylint_warnings.txt"), "w") as f:
        f.write("This is a dummy file\n")