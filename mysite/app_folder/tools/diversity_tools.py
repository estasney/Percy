import pickle

import math
import numpy as np
from cytoolz import groupby
from app_folder.tools.decorators import memoized
from scipy import stats

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

    def __init__(self, ratio_female, flashtext_fp=fconfig.NAMESEARCH_V2, sample_min_size=30,
                 name_confidence=0.95, sample_confidence=0.95,
                 maximum_name_certainty=.995):

        """

        """

        self.kw = self.load_fp(flashtext_fp)
        self.maximum_name_certainty = maximum_name_certainty
        self.population_female = ratio_female
        self.mod_female = ratio_female / 0.5
        self.mod_male = (1 - ratio_female) / 0.5
        self.population_std = self.get_population_std_from_ratio(ratio_female)
        self.sample_min_size = sample_min_size
        self.name_confidence = name_confidence
        self.sample_confidence = sample_confidence

    def get_population_std_from_ratio(self, ratio_female):
        pop_size = 100
        n_female = int(math.ceil(pop_size * ratio_female))
        n_male = pop_size - n_female
        population_array = self.make_array(n_male, n_female, calibrate=False)
        return population_array.std()

    def limit_certainty(self, n_male, n_female):

        if n_male == n_female:
            return n_male, n_female

        count_max = max([n_male, n_female])
        count_min = min([n_male, n_female])

        skew = count_max / (count_max + count_min)
        if skew <= self.maximum_name_certainty:
            return n_male, n_female

        if count_min == 0:
            count_min = math.ceil(count_max * (1 - self.maximum_name_certainty))
            if count_max == n_male:
                return n_male, count_min
            else:
                return count_min, n_female

        scale = (count_max - (self.maximum_name_certainty * count_max)) / (self.maximum_name_certainty * count_min)
        count_min_scaled = math.ceil(count_min * scale)

        if count_max == n_male:
            return n_male, count_min_scaled
        else:
            return count_min_scaled, n_female

    def calibrate(self, n_male, n_female):

        n_male, n_female = self.limit_certainty(n_male, n_female)

        n_male_mod = int(math.ceil(n_male * self.mod_male))
        n_female_mod = int(math.ceil(n_female * self.mod_female))

        return n_male_mod, n_female_mod

    def make_array(self, n_male, n_female, calibrate=True):
        if calibrate:
            n_male, n_female = self.calibrate(n_male, n_female)
        m = np.zeros(n_male)
        f = np.ones(n_female)
        return np.concatenate([m, f])

    def make_sigma_scale(self, arr):
        if arr.size < self.sample_min_size:
            return self.population_std / np.sqrt(arr.size)

        arr_mean = arr.mean()

        if arr_mean == 0 or arr_mean == 1:
            return self.population_std / np.sqrt(arr.size)
        else:
            return arr.std(ddof=1) / np.sqrt(arr.size)

    @memoized
    def get_interval(self, n_male, n_female):

        sample = self.make_array(n_male, n_female)
        mu = sample.mean()
        scale = self.make_sigma_scale(sample)

        if scale == 0:  # Prevents nan
            return 0, 0

        # Min and max of interval
        m1, m3 = stats.norm.interval(alpha=self.name_confidence, loc=mu, scale=scale)

        # # Truncate negative values and values > 1
        m1, m3 = max([m1, 0]), min([1, m3])
        return m1, m3

    def make_name_sample(self, name_probability_interval, n_name_samples):
        # Possible that multiple names detected. Take the one with the most samples

        name_mean_min, name_mean_max = name_probability_interval
        min_array = np.random.binomial(1, name_mean_min, n_name_samples // 2)
        max_array = np.random.binomial(1, name_mean_max, n_name_samples // 2)
        prob_array = np.concatenate([min_array, max_array])
        del min_array, max_array
        np.random.shuffle(prob_array)
        return prob_array

    def get_name_probality_interval(self, count):
        name_mean_min, name_mean_max = self.get_interval(*count)
        return name_mean_min, name_mean_max

    def trial_names(self, name_data, n_name_samples):
        name_probability_intervals = [self.get_name_probality_interval(count) for count in name_data]
        name_samples = np.vstack(
            [self.make_name_sample(interval, n_name_samples) for interval in name_probability_intervals])
        return name_samples.mean(axis=0)

    def extract_names(self, names):
        data = []
        for n in names:
            result = self.kw.extract_keywords(n)
            if not result:
                data.append(None)
                continue
            n_male = sum([x[0] for x in result])
            n_female = sum([x[1] for x in result])

            data.append((n_male, n_female))

        return data

    def summarize_gender(self, names, random_seed, n_name_samples=100):
        np.random.seed(random_seed)
        # Groupby if we have counts for a name

        name_data = self.extract_names(names)
        grouped_names = groupby(lambda x: x is not None, name_data)
        known_names, unknown_names = grouped_names.get(True, []), grouped_names.get(False, [])
        del grouped_names

        n_names = len(names)
        n_known = len(known_names)
        n_unknown = len(unknown_names)

        if not known_names:
            return None

        trial_means = self.trial_names(known_names, n_name_samples)
        trial_mu = trial_means.mean()
        trial_scale = self.make_sigma_scale(trial_means)
        m1, m3 = stats.norm.interval(alpha=self.sample_confidence, loc=trial_mu, scale=trial_scale)
        m1, m3 = max([0, m1]), min([1, m3])

        trial_means_list = list(trial_means)

        return {'n_names': n_names, 'n_known': n_known, 'n_unknown': n_unknown, 'trial_mean': trial_mu,
                'trial_scale': trial_scale, 'trial_min': m1, 'trial_max': m3, 'n_name_samples': n_name_samples,
                'name_confidence': self.name_confidence, 'sample_confidence': self.sample_confidence,
                'trial_means': trial_means_list,
                'n_trials': n_name_samples, 'trial_means_min': min(trial_means_list),
                'trial_means_max': max(trial_means_list)}

    def load_fp(self, fp):
        with open(fp, "rb") as p:
            return pickle.load(p)
