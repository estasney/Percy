from collections import OrderedDict
from operator import itemgetter
from app_folder.site_config import FConfig
import pickle
import numpy as np
from scipy.stats import t

fconfig = FConfig()


def load_ns(fp=fconfig.NAMESEARCH):
    with open(fp, 'rb') as pfile:
        return pickle.load(pfile)


def load_ns2(fp=fconfig.NAMESEARCH_V2):
    with open(fp, 'rb') as pfile:
        return pickle.load(pfile)


class NameStats(object):

    def __init__(self):
        self.namesearch = load_ns2()

    def lookup(self, text):
        match = self.namesearch.extract_keywords(text)
        if not match:
            return False
        match = match[0]
        n_male, n_female = match
        total = n_male + n_female
        if total > 0:
            p_male = n_male / total
            p_female = n_female / total
        else:
            p_male = 0
            p_female = 0
        return {'n_male': n_male, 'n_female': n_female, 'p_male': p_male, 'p_female': p_female, 'total': total}


class NameData(object):

    def __init__(self, data, name, priority, preprocessor=None):
        self.data = self.structure_data(data)
        self.name_set = self.generate_set(data)
        self.name = name
        self.priority = priority
        self.preprocessor = preprocessor

    def structure_data(self, data):
        data_ = sorted(data, key=itemgetter(0))
        return OrderedDict(data_)

    def generate_set(self, data):
        data_ = sorted(data, key=itemgetter(0))
        data_ = [x for x, _ in data_]
        return set(data_)

    @property
    def _signature_(self):
        return self.name, self.priority

    def search(self, item):
        if self.preprocessor:
            item = self.preprocessor(item)
        if item not in self.name_set:
            return False
        return self.data[item], self._signature_

    def __contains__(self, item):
        if self.preprocessor:
            item = self.preprocessor(item)
        if item in self.name_set:
            return True
        else:
            return False

    def __repr__(self):
        return "<NameData {}, Priority: {}>".format(self.name, self.priority)


class NameSearch(object):

    def __init__(self, datasets):
        self.datasets = sorted(datasets, key=lambda x: x.priority)

    def __contains__(self, item):
        # builtin function map (faster)
        if any([item in d for d in self.datasets]):
            return True
        else:
            return False

    def __repr__(self):
        return "<NameSearch>"

    def search(self, item):
        # Map the search
        results = []
        for d in self.datasets:
            results.append(d.search(item))

        results = [r for r in results if r is not False]

        return results

    def priority_search(self, item):
        """
        :param item: first name
        :return: result from highest priority dataset
        """

        results = self.search(item)
        if not results:
            return []
        results.sort(key=lambda x: x[1][1])
        top_result = results[0][0]
        return top_result


def search_data(names):
    ns = load_ns()

    # lowercase, strip all names
    lnames = map(lambda x: x.lower().strip(), names)
    results = map(ns.priority_search, lnames)
    knowns = list(filter(lambda x: x, results))
    unknown = len(names) - len(knowns)
    male = len([g for g in knowns if g == "M"])
    female = len(knowns) - male
    data = {'total': len(names), 'male': male, 'female': female, 'unknown': unknown}
    ci = search_confidence(data)
    data['95'], data['99'], data['ratio_female'] = ci['95'], ci['99'], ci['mean']
    data['known'] = len(knowns)
    return data


def search_confidence(data):
    male, female, total = data['male'], data['female'], data['total']
    # Replace M with 0, F with 1
    vec = np.concatenate([np.zeros(male), np.ones(female)])
    s_std = np.std(vec)
    s_mean = np.mean(vec)
    degrees_freedom = total - vec.shape[0] - 1

    # magic coefficient for 95%, 99% confidence, double tail
    t_value_95 = t.ppf(1 - 0.025, degrees_freedom)
    t_value_99 = t.ppf(1 - 0.005, degrees_freedom)

    # Calculate plus and minus
    # Standard deviation divided by sqrt of sample size
    a = s_std / np.sqrt(vec.shape[0])

    # Sqrt of (Population - Sample Size) / (Population - 1)
    b = np.sqrt((total - vec.shape[0]) / (total - 1))

    ci_95 = t_value_95 * a * b
    ci_99 = t_value_99 * a * b
    return {'95': ci_95, '99': ci_99, 'mean': s_mean}




