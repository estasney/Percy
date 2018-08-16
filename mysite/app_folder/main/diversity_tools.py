from collections import OrderedDict
from operator import itemgetter
from app_folder.site_config import FConfig
import pickle


def load_ns(fp=FConfig.namesearch):
    with open(fp, 'rb') as pfile:
        return pickle.load(pfile)


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

    # lowercase all names
    lnames = map(lambda x: x.lower(), names)
    results = map(ns.priority_search, lnames)
    knowns = list(filter(lambda x: x, results))
    unknown = len(names) - len(knowns)
    male = len([g for g in knowns if g == "M"])
    female = len(knowns) - male
    return {'total': len(names), 'male': male, 'female': female, 'unknown': unknown}
