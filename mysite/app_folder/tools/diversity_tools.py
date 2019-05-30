import pickle

import numpy as np
from cytoolz import groupby
from scipy import stats
import math
from app_folder.tools.decorators import memoized

from app_folder.site_config import FConfig

fconfig = FConfig()


def get_name_count(name, fp=fconfig.NAMESEARCH_V2):
    with open(fp, "rb") as p:
        kw = pickle.load(p)

    if name not in kw:
        return None
    else:
        male, female = kw.get_keyword(name)
        return {'n_male': male, 'n_female': female}


class NameSearch(object):

    def __init__(self, ratio_female, n_male=100000, flashtext_fp=fconfig.NAMESEARCH_V2, sample_min_size=30,
                 sample_min_size_uniform=100):

        """

        :param ratio_female: expected ratio of females in a population.
        :param n_male: number of males from which to calculate number of females
        :param flashtext_fp: flashtext file path
        :param sample_min_size: The minimum size required in order to treat a sample as its own population.
        I.e. whether to use the sample's standard deviation or the population's
        :param sample_min_size_uniform: The minimum size required in order to treat a sample as its own population if
        it's samples are one-sided. E.g. Male : 50, Female: 0
        """

        self.kw = self.load_fp(flashtext_fp)
        self.population_std = self.get_population_std_from_ratio(ratio_female)
        self.sample_min_size = sample_min_size
        self.sample_min_size_uniform = sample_min_size_uniform

    def get_population_std_from_ratio(self, ratio_female):
        pop_size = 100
        n_female = int(math.ceil(pop_size* ratio_female))
        n_male = pop_size - n_female
        population_array = self.make_array(n_male, n_female)
        return population_array.std()

    @memoized
    def make_array(self, n_male, n_female):
        m = np.zeros(n_male)
        f = np.ones(n_female)
        return np.concatenate([m, f])

    def make_sigma_scale(self, arr):
        if arr.size < self.sample_min_size:
            return self.population_std / np.sqrt(arr.size)

        arr_mean = arr.mean()

        if arr_mean == 0 or arr_mean == 1 and arr.size < self.sample_min_size_uniform:
            return self.population_std / np.sqrt(arr.size)
        else:
            return arr.std(ddof=1) / np.sqrt(arr.size)

    @memoized
    def get_interval(self, n_male, n_female, confidence):

        sample = self.make_array(n_male, n_female)
        mu = sample.mean()
        scale = self.make_sigma_scale(sample)

        if scale == 0:  # Prevents nan
            return 0, 0

        # Min and max of interval
        m1, m3 = stats.norm.interval(alpha=confidence, loc=mu, scale=scale)

        # Truncate negative values and values > 1
        m1, m3 = max([m1, 0]), min([1, m3])
        return m1, m3

    @memoized
    def get_name_probality_interval(self, name, name_confidence):
        counts = self.kw.extract_keywords(name)
        n_male, n_female = max(counts, key=lambda x: sum(x))
        name_mean_min, name_mean_max = self.get_interval(n_male, n_female, name_confidence)
        return name_mean_min, name_mean_max

    def make_name_sample(self, name_probability_interval, n_name_samples):
        # Possible that multiple names detected. Take the one with the most samples

        name_mean_min, name_mean_max = name_probability_interval
        min_array = np.random.binomial(1, name_mean_min, n_name_samples // 2)
        max_array = np.random.binomial(1, name_mean_max, n_name_samples // 2)
        prob_array = np.concatenate([min_array, max_array])
        del min_array, max_array
        np.random.shuffle(prob_array)
        return prob_array

    def trial_names(self, names, n_name_samples, name_confidence):
        name_probability_intervals = [self.get_name_probality_interval(name, name_confidence) for name in names]
        name_samples = np.vstack(
            [self.make_name_sample(interval, n_name_samples) for interval in name_probability_intervals])
        return name_samples.mean(axis=0)

    def summarize_gender(self, names, random_seed, n_name_samples=100, name_confidence=0.95, sample_confidence=0.95):
        np.random.seed(random_seed)
        # Groupby if we have counts for a name
        grouped_names = groupby(lambda x: len(self.kw.extract_keywords(x)) > 0, names)
        known_names, unknown_names = grouped_names.get(True, []), grouped_names.get(False, [])
        del grouped_names

        n_names = len(names)
        n_known = len(known_names)
        n_unknown = len(unknown_names)

        if not known_names:
            return None


        trial_means = self.trial_names(known_names, n_name_samples, name_confidence)
        trial_mu = trial_means.mean()
        trial_scale = self.make_sigma_scale(trial_means)
        m1, m3 = stats.norm.interval(alpha=sample_confidence, loc=trial_mu, scale=trial_scale)
        m1, m3 = max([0, m1]), min([1, m3])

        trial_means_list = list(trial_means)

        return {'n_names': n_names, 'n_known': n_known, 'n_unknown': n_unknown, 'trial_mean': trial_mu,
                'trial_scale': trial_scale, 'trial_min': m1, 'trial_max': m3, 'n_name_samples': n_name_samples,
                'name_confidence': name_confidence, 'sample_confidence': sample_confidence,
                'trial_means': trial_means_list,
                'n_trials': n_name_samples, 'trial_means_min': min(trial_means_list),
                'trial_means_max': max(trial_means_list)}

    def load_fp(self, fp):
        with open(fp, "rb") as p:
            return pickle.load(p)
