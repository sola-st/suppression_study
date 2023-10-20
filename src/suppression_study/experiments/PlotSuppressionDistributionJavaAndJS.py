from os.path import join
import csv
from collections import Counter
import matplotlib.pyplot as plt
from suppression_study.experiments.Experiment import Experiment


class PlotSuppressionDistributionJavaAndJS(Experiment):
    def _load_data(self, file):
        kind_to_count = Counter()
        with open(file) as fp:
            reader = csv.reader(fp, None)
            rows = [r for r in reader]
            rows = rows[1:]  # skip header
            rows = rows[:-1] # skip last row, which is the total
            for row in rows:
                kind_to_count[row[2]] = int(row[3])
        return kind_to_count

    def _plot(self, data_file, output_file):
        plt.clf() # clear the previous plot
        plt.rcParams.update({'font.size': 13})

        kind_to_count = self._load_data(data_file)
        top_kind_to_count = dict(kind_to_count.most_common(10))
        print(top_kind_to_count)
        sorted_data = dict(sorted(top_kind_to_count.items(), key=lambda item: item[1]))
        plt.barh(list(sorted_data.keys()), list(sorted_data.values()))
        plt.xlabel("Number of suppressions") 
        plt.ylabel("Kind of suppression") 
        plt.tight_layout()
        plt.savefig(output_file)
        print(f"Saved histogram to {output_file}")

    def run(self):
        java_file = join("data", "results", "table_java_remaining_warnings.csv")
        java_output_file = join("data", "results", "suppression_histogram_java.pdf")    
        self._plot(java_file, java_output_file)
        
        javascript_file = join("data", "results", "table_javascript_remaining_warnings.csv")
        javascript_output_file = join("data", "results", "suppression_histogram_javascript.pdf")
        self._plot(javascript_file, javascript_output_file)


if __name__ == "__main__":
    PlotSuppressionDistributionJavaAndJS().run()
