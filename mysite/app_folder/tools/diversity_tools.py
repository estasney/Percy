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

    def __init__(self, ratio_female, flashtext_fp=fconfig.NAMESEARCH_V2, beta_interval=0.95, sample_confidence=0.95,
                 maximum_name_certainty=.99):

        """

        :param ratio_female: float, between 0 and 1. The prior belief of the ratio of females in the group
        :param flashtext_fp: the filepath to the flashtext pickle file
        :param beta_interval:
        :param sample_confidence:
        :param maximum_name_certainty:
        """

        self.kw = self.load_fp(flashtext_fp)
        self.maximum_name_certainty = maximum_name_certainty
        self.population_female = ratio_female
        self.mod_female = ratio_female / 0.5
        self.mod_male = (1 - ratio_female) / 0.5
        self.population_std = self.get_population_std_from_ratio(ratio_female)
        self.beta_interval = beta_interval
        self.sample_confidence = sample_confidence

    def summarize_gender(self, names, random_seed, n_name_samples=100):
        np.random.seed(random_seed)

        # Extract names from the input and separate into known and unknown
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
                'beta_interval': self.beta_interval, 'sample_confidence': self.sample_confidence,
                'trial_means': trial_means_list,
                'n_trials': n_name_samples, 'trial_means_min': min(trial_means_list),
                'trial_means_max': max(trial_means_list)}

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

    def make_beta(self, n_male, n_female, calibrate=True):
        if calibrate:
            n_male, n_female = self.calibrate(n_male, n_female)
        n_male += 1
        n_female += 1
        return stats.beta(a=n_female, b=n_male)

    def make_sigma_scale(self, arr):
        if arr.size < 30:
            return self.population_std / np.sqrt(arr.size)

        arr_mean = arr.mean()

        if arr_mean == 0 or arr_mean == 1:
            return self.population_std / np.sqrt(arr.size)
        else:
            return arr.std(ddof=1) / np.sqrt(arr.size)

    @memoized
    def get_interval(self, n_male, n_female):

        """
        In order to accurately simulate male/female occurrences we must provide a value for the probability of a name
        returning female.

        We assume that this cannot be known, but can be estimated.

        Our confidence in our estimation increases as the number of records increases. We fit a Beta model for this task
        """

        beta = self.make_beta(n_male, n_female)
        m1, m3 = beta.interval(self.beta_interval)
        return m1, m3

    def make_name_sample(self, name_probability_interval, n_name_samples):

        """
        :param name_probability_interval: tuple, min and max probability
        :param n_name_samples:
        :return:

        Given an estimation of the probability of a name returning female, we proceed to run the simulation.

        Our probability estimation is from a Beta model our simulation will be a binomial where:

        0 == 'male'
        1 == 'female'
        """

        name_mean_min, name_mean_max = name_probability_interval

        results = np.random.binomial((1, 1), (name_mean_min, name_mean_max), (n_name_samples//2, 1, 2))

        # we want to reshape the output so it is flat
        # the output from the min and max will be interleaved

        flat_results = results.reshape(1, -1)[0]

        return flat_results

    def trial_names(self, name_data, n_name_samples):

        """

        :param name_data:
        :param n_name_samples:
        :return:

        We collect the results of simulation into an array of shape (n_names, n_name_samples)

        For each trial we can compute the number of females

        """

        name_probability_intervals = [self.get_interval(*count) for count in name_data]
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

    def load_fp(self, fp):
        with open(fp, "rb") as p:
            return pickle.load(p)
