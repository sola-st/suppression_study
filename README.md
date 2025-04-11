# An Empirical Study of Suppressions of Static Analysis Warnings

[This paper](https://www.software-lab.org/publications/fse2025_suppressions.pdf) presents the first in-depth empirical study of suppressions of static analysis warnings, addressing questions about the prevalence of suppressions, their evolution over time, the relationship between suppressions and warnings, and the reasons for using suppressions.

## Setup
Choose one of the following options to set up the project.

#### Option 1: Run locally
If you prefer to run the code locally, make sure you have `python>=3.8`, and run the following from the root directory of this project:
1. `pip install -r requirements.txt`  
2. `apt-get install sloccount`
3. `pip install -e .`

#### Option 2: Run with Docker
If you prefer to isolate the packages that you install during the reproduction, use Docker.
1. Install Docker (if it is your first time using Docker, [Docker Desktop](https://docs.docker.com/desktop/) is recommended)
2. Build the image: `docker build -t suppression_study .`  
3. Run the container (run one of the following): 
  * With files editable: `docker run -it -v $(pwd):/suppression_home suppression_study`
  * With files non-editable: `docker run -it suppression_study`

## Experiments

The entry point for all experiments performed for the study is the scripts in the *src/suppression_study/experiments* directory. You can run experiments with a command like this:
`python -m suppression_study.experiments.<NameOfExperiment>`

Some experiments have dependencies on others. For example, you can run all experiments in this order:
* RunCheckersOnLatestCommit.py &emsp; Get warnings in the newest studied commit.
* CountSuppressionsOnLatestCommit.py &emsp; Extract and count suppressions for a specific commit.
* CountSuppressionsNumOnMainCommits.py &emsp; Extract and count suppressions for all commits.
* ComputeSuppressionHistories.py &emsp; Extract histories of suppressions.
* ComputeWarningSuppressionMapsOnLatestCommit.py &emsp; Compute the mappings between warnings and suppressions (the newest commit).
* ComputeIntermediateChains.py &emsp; Extract intermediate line number chains for the histories. 
* ComputeAccidentallySuppressedWarnings.py &emsp; Find potentially unintended suppressions.
* Get1000Commits.py  &emsp; Get an overview of the start and end commits of the repositories.

**Visualization**
* DistributionOfSuppressionsNumOnMainCommits.py
* DistributionOfSuppressionsOnLatestCommit.py
* PlotSuppressionDistributionJavaAndJS.py
* VisualizeWarningSuppressionMapsOnLatestCommit.py
* VisualizeLifetimeForAllSuppressions.py

**Inspections:**  
* InspectSuppressionHistories.py &emsp; Shuffle all extracted suppression histories. Get the add and delete commit git urls for the corresponding change event for manual inspection.
* InspectSuppressionRelatedCommits.py &emsp; Randomly samples commit that either add or remove a suppression and prepare them for manual inspection. 
* InspectAccidentallySuppressedWarnings.py &emsp; Collect all potentially unintended suppressions from the projects and prepare them for manual inspection. 

## Structure of the *data* directory

The *data* directory contains the following subdirectories and files, most of which are created by running the experiments:
* Files:
    * *data/specific_numeric_type_map.csv* includes the mappings between Pylint warning types and their numeric code.
    * *2020_CodeReview_Spec.pdf* and *2022_CodeReview_Spec.pdf* are course requirements for the Java/JavaScript student projects.
    * Other files are about the studied repositories.
* Subdirectories:
    * *data/repos* contains the repositories we study: 
        * Now it is empty, the experiments will check the existence and clone the repositories as needed.  
    * **data/results** [Load pre-computed results](#load-pre-computed-results), contains the results of running the experiments:
        * **[Individual perspective]** *data/results/<repo_name>* contains all results for the repository.
        *repo_name*.   
          * For each project, the following records the detailed results for RQ1 to RQ5:
            * Related to RQ1
              * *data/results/<repo_name>/commits/<commit_id>* contains all results for a specific commit hash <commit_id>        
            * Related to RQ2
              * *grep* records the suppressions in the 1,000 commits.
              * *histories_suppression_level_all.json* is the history file.
            * Related to RQs 3 and 4
              * *suppression2warnings* contains the files where record the maps between suppressions and warnings, and the useless/useful suppressions. 
            * RQ5 is based on all result files above
      * **[Overall perspective] Folders RQ1 to RQ5 contain the overall result of the corresponding research question.**

## Reproducing the results in the paper
Choose between **SLOW MODE**, which extracts the suppressions and warnings and may take several hours, depending on hardware, and **FAST MODE**, which generates the tables and plots from pre-computed results and should take less than 30 minutes (include cloning the repositories). 

**Notes**: 
* If no explicit path is written, by default all code files are in *src/suppression_study/experiments* and result files are in *data/results*.  

* Some file executions use `grep`, which may display the warning message:
`grep: warning: * at start of expression.`
This warning can be safely ignored and does not affect the execution.

* The file names of the generated tables and plots in the *data/results* folder:
  * Table 2 &emsp; suppressions_per_repo.tex + commits_and_histories.tex
  * Table 3 &emsp; suppression_levels/overall_table.tex
  * Table 4 &emsp; useful_and_useless_suppressions.tex
  * Figure 4 &emsp; repo10_suppression_num_on_main.pdf
  * Figure 5 &emsp; lifetime_visualization.pdf
  * Figure 6 &emsp; suppressions_to_warnings.pdf + warnings_to_suppressions.pdf

### SLOW MODE
#### RQ1: Prevalence of Suppressions. 
* Run RunCheckersOnLatestCommit.py. 
* Analysis to get the unified warning kinds and the number of each kind. -> Table 1.

#### RQ2: Evolution of Suppressions.
* Run ComputeWarningSuppressionMapsOnLatestCommit.py   
-> Although this file is part of RQ3, running it here can help reduce the execution time of ComputeSuppressionHistories.py later.
* Run ComputeSuppressionHistories.py.
* Run CountSuppressionsOnLatestCommit.py -> suppressions_per_repo.tex (part of Table 2).
* Run Get1000Commits.py
* Run DistributionOfSuppressionsNumOnMainCommits.py -> Figure 4.
* Run VisualizeLifetimeForAllSuppressions.py -> Figure 5 and commits_and_histories.tex (remaining Part of Table 2).
* suppressions_per_repo.tex + commits_and_histories.tex -> Table 2.

#### RQ3: Relation Between Suppressions and Warnings.
* Run CheckSuppressionLevels.py
* Run TableSuppressionLevels.py--> Table 3.
* Run ComputeWarningSuppressionMapsOnLatestCommit.py   
-> If you have already run it in RQ2, there’s no need to run it again.
* Run VisualizeWarningSuppressionMapsOnLatestCommit.py -> Table 4 and Figure 6.

#### RQ4: Potentially unintended suppressions.
* Run ComputeIntermediateChains.py 
* Run ComputeAccidentallySuppressedWarnings.py 
* Run InspectAccidentallySuppressedWarnings.py
* Manual analysis. -> Table 5

#### RQ5: Reasons for Using Suppressions.
* Run InspectSuppressionRelatedCommits.py
* Manual analysis. -> Table 6

### FAST MODE
#### Load pre-computed results 
Before generate the table and plots, load the pre-computed results. Here are two options:
* [Option 1] Run LoadPreComputedResults.py, it will automatically load and place the results folder in the correct location.
* [Option 2] Manually download results.zip from the latest release and extract it into the _data_ folder.

You can check the structure of _data/results_ [here](#structure-of-the-data-directory).

#### Reproduce tables and plots:  
All tables and figures (exclude the ones require manual analysis) in results: 
* Run CountSuppressionsOnLatestCommit.py -> suppressions_per_repo.tex (part of Table 2).
* Run DistributionOfSuppressionsNumOnMainCommits.py -> Figure 4.
* Run VisualizeLifetimeForAllSuppressions.py -> Figure 5 and commits_and_histories.tex (remaining Part of Table 2).
* suppressions_per_repo.tex + commits_and_histories.tex -> Table 2.
* Run TableSuppressionLevels.py--> Table 3.
* Run VisualizeWarningSuppressionMapsOnLatestCommit.py -> Table 4 and Figure 6.
