import pickle

import math
import numpy as np
from cytoolz import groupby
from app_folder.tools.decorators import memoized
from app_folder.models import Name
from scipy import stats

from app_folder.site_config import FConfig

fconfig = FConfig()


def get_name_count(name):
    name = name.lower()
    name_kw = Name.query.get(name)
    if not name_kw:
        return None
    else:
        male, female = name_kw.male_count, name_kw.female_count
        return {'n_male': male, 'n_female': female}


class NameSearch(object):

    def __init__(self, prior=None, flashtext_fp=fconfig.NAMESEARCH_V2, beta_interval=0.95, sample_confidence=0.95):

        """

        :param prior: Tuple, or None (default). When passed, indicates prior knowledge of probability. Passing None, will set self.alpha and self.beta to 1, 1.
        Otherwise, the closest estimation will be found from existing calculations
        :param flashtext_fp: the filepath to the flashtext pickle file
        :param beta_interval:
        :param sample_confidence:
        """

        self.kw = self.load_fp(flashtext_fp)
        self.prior = prior
        self.alpha = None
        self.beta = None
        self.beta_interval = beta_interval
        self.sample_confidence = sample_confidence
        self.get_beta_params()

    def get_beta_params(self):
        if not self.prior:
            self.alpha = 1
            self.beta = 1
            return

        with open(fconfig.BETA_PARAMS, "rb") as fp:
            beta_params = np.load(fconfig.BETA_PARAMS)

        # beta params is of form
        # a, b, ci_95_min, ci_95_max
        # find closest parameters to passed prior

        ci_array = np.asarray(beta_params[:, 2:])
        val_array = np.array([*self.prior]).reshape(1, 2)

        idx_2d = np.abs(ci_array - val_array)

        # sum the differences
        idx = idx_2d.sum(axis=1)
        alpha, beta, ci_95_min, ci_95_max = beta_params[idx.argmin()]
        self.alpha = alpha
        self.beta = beta
        return

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
        trial_std = trial_means.std(ddof=1)
        trial_sigma = trial_std / np.sqrt(trial_means.size)
        m1, m3 = stats.t.interval(alpha=self.sample_confidence, df=trial_means.size, loc=trial_mu, scale=trial_sigma)
        m1, m3 = max([0, m1]), min([1, m3])

        trial_means_list = list(trial_means)

        return {
            'n_names':         n_names, 'n_known': n_known, 'n_unknown': n_unknown, 'trial_mean': trial_mu,
            'trial_scale':     trial_sigma, 'trial_min': m1, 'trial_max': m3, 'n_name_samples': n_name_samples,
            'beta_interval':   self.beta_interval, 'sample_confidence': self.sample_confidence,
            'trial_means':     trial_means_list,
            'n_trials':        n_name_samples, 'trial_means_min': min(trial_means_list),
            'trial_means_max': max(trial_means_list)
            }

    def make_array(self, n_male, n_female):
        m = np.zeros(n_male)
        f = np.ones(n_female)
        return np.concatenate([m, f])

    def make_beta(self, n_male, n_female):
        n_male += self.beta
        n_female += self.alpha
        return stats.beta(a=n_female, b=n_male)

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

    def make_name_simulation(self, name_probability_interval, n_trials):

        """
        :param name_probability_interval: tuple, min and max probability
        :param n_trials:
        :return:

        Given an estimation of the probability of a name returning female, we proceed to run the simulation.

        Our probability estimation is from a Beta model our simulation will be a binomial where:

        0 == 'male'
        1 == 'female'
        """

        name_mean_min, name_mean_max = name_probability_interval

        results = np.random.binomial((1, 1), (name_mean_min, name_mean_max), (n_trials // 2, 1, 2))

        # we want to reshape the output so it is flat
        # the output from the min and max will be interleaved

        flat_results = results.reshape(1, -1)[0]
        np.random.shuffle(flat_results)

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
        outcomes = [self.make_name_simulation(interval, n_name_samples) for interval in name_probability_intervals]
        name_samples = np.vstack(outcomes)
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
