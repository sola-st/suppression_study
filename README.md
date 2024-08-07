# An Empirical Study of Suppressions of Static Analysis Warnings

**Dependencies:**
  GitPython~=3.1.31,
  pylint==2.17.4,
  pydantic==2.3.0,
  matplotlib>=3.5,
  and scipy.

## Experiments

The entry point for all experiments performed for the study is the scripts in the *src/suppression_study/experiments* directory.
You can run experiments with a command like this:
`python -m suppression_study.experiments.<NameOfExperiment>`

Some experiments have dependencies on others. For example, you can run all experiments in this order:
* RunCheckersOnLatestCommit.py &emsp; Get warnings in the newest studied commit.
* CountSuppressionsNumOnMainCommits.py &emsp; Extract and count suppressions for all commits.
* CountSuppressionsOnLatestCommit.py &emsp; Extract and count suppressions for a specific commit.
* ComputeSuppressionHistories.py &emsp; Extract histories of suppressions.
* ComputeWarningSuppressionMapsOnLatestCommit.py &emsp; Compute the mappings between warnings and suppressions (the newest commit).

**Visualization**
* DistributionOfSuppressionsNumOnMainCommits.py
* DistributionOfSuppressionsOnLatestCommit.py
* PlotSuppressionDistributionJavaAndJS.py
* VisualizeWarningSuppressionMapsOnLatestCommit.py
* VisualizeLifetimeForAllSuppressions.py

**Inspections:**  
* InspectSuppressionHistories.py &emsp; Shuffle all extracted suppression histories. Get the add and delete commit git urls for the corresponding change event for manual inspection.
* InspectSuppressionRelatedCommits.py &emsp; Randomly samples commit that either add or remove a suppression and prepare them for manual inspection.

## Structure of the *data* directory

The *data* directory contains the following subdirectories and files, most of which are created by running the experiments:
* Files:
    * *data/specific_numeric_type_map.csv* includes the mappings between Pylint warning types and their numeric code.
    * Other files are about the studied repositories.
* Subdirectories:
    * *data/repos* contains the cloned repositories we study.
    * *data/results* contains the results of running the experiments:
        * *data/results/<repo_name>* contains all results for the repository *repo_name*.
        * *data/results/<repo_name>/commits/<commit_id>* contains all results for a specific commit hash <commit_id>
Files with names starts with *inspection_* contain the inspection of some results.
        * *start_end_commits_1000.csv* records the start and end commits for 10 Python projects.
        * Other files are about the student projects (code review specification + open coding).

## Reproducing the results in the paper
Choose between **SLOW MODE**, which extracts the suppressions and warnings and may take several hours, depending on hardware, and **FAST MODE**, which generates the tables and plots (the ones with no manual analysis required) from pre-computed results and should take less than 30 minutes (include cloning the repositories). 

**Note**: If no explicit path is written, by default all code files are in *src/suppression_study/experiments* and result files are in *data/results*.

### SLOW MODE
#### RQ1: Prevalence of Suppressions. 
* Run RunCheckersOnLatestCommit.py. 
* Analysis to get the unified warning kinds and the number of each kind. -> Table I.

#### RQ2: Evolution of Suppressions.
* Run ComputeSuppressionHistories.py.
* Specify the exp.repo_file with the value 'python_repos.txt' in the entry point of CountSuppressionsOnLatestCommit.py and run it. -> suppressions_per_repo.tex (part of Table II).
* Run DistributionOfSuppressionsNumOnMainCommits.py -> Figure 4.
* Run VisualizeLifetimeForAllSuppressions.py -> Figure 5 and commits_and_histories.tex (remaining Part of Table II).
* suppressions_per_repo.tex + commits_and_histories.tex -> Table II.

#### RQ3: Relation Between Suppressions and Warnings.
* Run ComputeWarningSuppressionMapsOnLatestCommit.py
* Run VisualizeWarningSuppressionMapsOnLatestCommit.py -> Figures 6 and 7.

#### RQ4: Reasons for Using Suppressions.
* Run InspectSuppressionRelatedCommits.py
* Manual analysis. -> Table III
# An Empirical Study of Suppressions of Static Analysis Warnings

**Dependencies:**
  GitPython~=3.1.31,
  pylint==2.17.4,
  pydantic==2.3.0,
  matplotlib>=3.5,
  and scipy.

## Experiments

The entry point for all experiments performed for the study is the scripts in the *src/suppression_study/experiments* directory.
You can run experiments with a command like this:
`python -m suppression_study.experiments.<NameOfExperiment>`

Some experiments have dependencies on others. For example, you can run all experiments in this order:
* RunCheckersOnLatestCommit.py &emsp; Get warnings in the newest studied commit.
* CountSuppressionsNumOnMainCommits.py &emsp; Extract and count suppressions for all commits.
* CountSuppressionsOnLatestCommit.py &emsp; Extract and count suppressions for a specific commit.
* ComputeSuppressionHistories.py &emsp; Extract histories of suppressions.
* ComputeWarningSuppressionMapsOnLatestCommit.py &emsp; Compute the mappings between warnings and suppressions (the newest commit).

**Visualization**
* DistributionOfSuppressionsNumOnMainCommits.py
* DistributionOfSuppressionsOnLatestCommit.py
* PlotSuppressionDistributionJavaAndJS.py
* VisualizeWarningSuppressionMapsOnLatestCommit.py
* VisualizeLifetimeForAllSuppressions.py

**Inspections:**  
* InspectSuppressionHistories.py &emsp; Shuffle all extracted suppression histories. Get the add and delete commit git urls for the corresponding change event for manual inspection.
* InspectSuppressionRelatedCommits.py &emsp; Randomly samples commit that either add or remove a suppression and prepare them for manual inspection.

## Structure of the *data* directory

The *data* directory contains the following subdirectories and files, most of which are created by running the experiments:
* Files:
    * *data/specific_numeric_type_map.csv* includes the mappings between Pylint warning types and their numeric code.
    * Other files are about the studied repositories.
* Subdirectories:
    * *data/repos* contains the cloned repositories we study.
    * *data/results* contains the results of running the experiments:
        * *data/results/<repo_name>* contains all results for the repository *repo_name*.
        * *data/results/<repo_name>/commits/<commit_id>* contains all results for a specific commit hash <commit_id>
Files with names starts with *inspection_* contain the inspection of some results.
        * *start_end_commits_1000.csv* records the start and end commits for 10 Python projects.
        * Other files are about the student projects (code review specification + open coding).

## Reproducing the results in the paper
Choose between **SLOW MODE**, which extracts the suppressions and warnings and may take several hours, depending on hardware, and **FAST MODE**, which generates the tables and plots (the ones with no manual analysis required) from pre-computed results and should take less than 30 minutes (include cloning the repositories). 

**Note**: If no explicit path is written, by default all code files are in *src/suppression_study/experiments* and result files are in *data/results*.

### SLOW MODE
#### RQ1: Prevalence of Suppressions. 
* Run RunCheckersOnLatestCommit.py. 
* Analysis to get the unified warning kinds and the number of each kind. -> Table I.

#### RQ2: Evolution of Suppressions.
* Run ComputeSuppressionHistories.py.
* Specify the exp.repo_file with the value 'python_repos.txt' in the entry point of CountSuppressionsOnLatestCommit.py and run it. -> suppressions_per_repo.tex (part of Table II).
* Run DistributionOfSuppressionsNumOnMainCommits.py -> Figure 4.
* Run VisualizeLifetimeForAllSuppressions.py -> Figure 5 and commits_and_histories.tex (remaining Part of Table II).
* suppressions_per_repo.tex + commits_and_histories.tex -> Table II.

#### RQ3: Relation Between Suppressions and Warnings.
* Run ComputeWarningSuppressionMapsOnLatestCommit.py
* Run VisualizeWarningSuppressionMapsOnLatestCommit.py -> Figures 6 and 7.

#### RQ4: Reasons for Using Suppressions.
* Run InspectSuppressionRelatedCommits.py
* Manual analysis. -> Table III

### FAST MODE
All tables in results: Tables I--III, Tables I and II require manual analysis.  
All figures in results: Figures 4--7.   
* Specify the exp.repo_file with the value 'python_repos.txt' in the entry point of CountSuppressionsOnLatestCommit.py and run it. -> suppressions_per_repo.tex (part of Table II).
* Run DistributionOfSuppressionsNumOnMainCommits.py -> Figure 4.
* Run VisualizeLifetimeForAllSuppressions.py -> Figure 5 and commits_and_histories.tex (remaining Part of Table II).
* suppressions_per_repo.tex + commits_and_histories.tex -> Table II.
* Run VisualizeWarningSuppressionMapsOnLatestCommit.py -> Figures 6 and 7.
# An Empirical Study of Suppressions of Static Analysis Warnings

**Dependencies:**
  GitPython~=3.1.31,
  pylint==2.17.4,
  pydantic==2.3.0,
  matplotlib>=3.5,
  and scipy.

## Experiments

The entry point for all experiments performed for the study is the scripts in the *src/suppression_study/experiments* directory.
You can run experiments with a command like this:
`python -m suppression_study.experiments.<NameOfExperiment>`

Some experiments have dependencies on others. For example, you can run all experiments in this order:
* RunCheckersOnLatestCommit.py &emsp; Get warnings in the newest studied commit.
* CountSuppressionsNumOnMainCommits.py &emsp; Extract and count suppressions for all commits.
* CountSuppressionsOnLatestCommit.py &emsp; Extract and count suppressions for a specific commit.
* ComputeSuppressionHistories.py &emsp; Extract histories of suppressions.
* ComputeWarningSuppressionMapsOnLatestCommit.py &emsp; Compute the mappings between warnings and suppressions (the newest commit).

**Visualization**
* DistributionOfSuppressionsNumOnMainCommits.py
* DistributionOfSuppressionsOnLatestCommit.py
* PlotSuppressionDistributionJavaAndJS.py
* VisualizeWarningSuppressionMapsOnLatestCommit.py
* VisualizeLifetimeForAllSuppressions.py

**Inspections:**  
* InspectSuppressionHistories.py &emsp; Shuffle all extracted suppression histories. Get the add and delete commit git urls for the corresponding change event for manual inspection.
* InspectSuppressionRelatedCommits.py &emsp; Randomly samples commit that either add or remove a suppression and prepare them for manual inspection.

## Structure of the *data* directory

The *data* directory contains the following subdirectories and files, most of which are created by running the experiments:
* Files:
    * *data/specific_numeric_type_map.csv* includes the mappings between Pylint warning types and their numeric code.
    * Other files are about the studied repositories.
* Subdirectories:
    * *data/repos* contains the cloned repositories we study.
    * *data/results* contains the results of running the experiments:
        * *data/results/<repo_name>* contains all results for the repository *repo_name*.
        * *data/results/<repo_name>/commits/<commit_id>* contains all results for a specific commit hash <commit_id>
Files with names starts with *inspection_* contain the inspection of some results.
        * *start_end_commits_1000.csv* records the start and end commits for 10 Python projects.
        * Other files are about the student projects (code review specification + open coding).

## Reproducing the results in the paper
Choose between **SLOW MODE**, which extracts the suppressions and warnings and may take several hours, depending on hardware, and **FAST MODE**, which generates the tables and plots (the ones with no manual analysis required) from pre-computed results and should take less than 30 minutes (include cloning the repositories). 

**Note**: If no explicit path is written, by default all code files are in *src/suppression_study/experiments* and result files are in *data/results*.

### SLOW MODE
#### RQ1: Prevalence of Suppressions. 
* Run RunCheckersOnLatestCommit.py. 
* Analysis to get the unified warning kinds and the number of each kind. -> Table I.

#### RQ2: Evolution of Suppressions.
* Run ComputeSuppressionHistories.py.
* Specify the exp.repo_file with the value 'python_repos.txt' in the entry point of CountSuppressionsOnLatestCommit.py and run it. -> suppressions_per_repo.tex (part of Table II).
* Run DistributionOfSuppressionsNumOnMainCommits.py -> Figure 4.
* Run VisualizeLifetimeForAllSuppressions.py -> Figure 5 and commits_and_histories.tex (remaining Part of Table II).
* suppressions_per_repo.tex + commits_and_histories.tex -> Table II.

#### RQ3: Relation Between Suppressions and Warnings.
* Run ComputeWarningSuppressionMapsOnLatestCommit.py
* Run VisualizeWarningSuppressionMapsOnLatestCommit.py -> Figures 6 and 7.

#### RQ4: Reasons for Using Suppressions.
* Run InspectSuppressionRelatedCommits.py
* Manual analysis. -> Table III

### FAST MODE
All tables in results: Tables I--III, Tables I and II require manual analysis.  
All figures in results: Figures 4--7.   
* Specify the exp.repo_file with the value 'python_repos.txt' in the entry point of CountSuppressionsOnLatestCommit.py and run it. -> suppressions_per_repo.tex (part of Table II).
* Run DistributionOfSuppressionsNumOnMainCommits.py -> Figure 4.
* Run VisualizeLifetimeForAllSuppressions.py -> Figure 5 and commits_and_histories.tex (remaining Part of Table II).
* suppressions_per_repo.tex + commits_and_histories.tex -> Table II.
* Run VisualizeWarningSuppressionMapsOnLatestCommit.py -> Figures 6 and 7.

### FAST MODE
All tables in results: Tables I--III, Tables I and II require manual analysis.  
All figures in results: Figures 4--7.   
* Specify the exp.repo_file with the value 'python_repos.txt' in the entry point of CountSuppressionsOnLatestCommit.py and run it. -> suppressions_per_repo.tex (part of Table II).
* Run DistributionOfSuppressionsNumOnMainCommits.py -> Figure 4.
* Run VisualizeLifetimeForAllSuppressions.py -> Figure 5 and commits_and_histories.tex (remaining Part of Table II).
* suppressions_per_repo.tex + commits_and_histories.tex -> Table II.
* Run VisualizeWarningSuppressionMapsOnLatestCommit.py -> Figures 6 and 7.
