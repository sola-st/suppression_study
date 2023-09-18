# A Empirical Study of Suppressions of Static Analysis Warnings

## Experiments

The entry point for all experiments performed for the study are the scripts in the *experiments* directory.
You can run experiments with a command like this:
`python -m suppression_study.experiments.<NameOfExperiment>`

Some experiments have dependencies on others.
For example, you can run all experiments in this order:
 * RunCheckersOnLatestCommits
 * (TODO: to be continued)


## Structure of the *data* Directory

The *data* directory contains the following subdirectories, most of which are created by running the experiments:
 * *data/repos* contains the cloned repositories we study
 * *data/results* contains the results of running the experiments
 * *data/results/<repo_name>* contains all results for the repository *repo_name*
 * *data/results/<repo_name>/commits/<commit_id>* contains all results for a specific commit hash <commit_id>


