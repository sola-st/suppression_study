"""
Minimal experiment that serves as a template for new experiments.
"""

from suppression_study.experiments.Experiment import Experiment

class DummyExperiment(Experiment):
    pass


if __name__ == "__main__":
    DummyExperiment(name="dummy", depends_on=[]).run_all()