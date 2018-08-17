import difflib
import pickle
import re
import os
from collections import Counter
from itertools import chain, combinations

import networkx as nx



f = "company2id.pkl"
f1 = "id2company.pkl"

with open(f, 'rb') as pfile:
    id2company = pickle.load(pfile)

with open(f1, 'rb') as pfile:
    company2id = pickle.load(pfile)

char_search = re.compile(r"[^0-9 A-z]")
tokens = re.compile(r"(\w+)")


def longest_match(cid, l):
    def preprocess(x):
        x = char_search.sub("", x)
        x = x.lower()
        words = tokens.findall(x)
        return " ".join(words)

    ltokens = [preprocess(x) for x in l]
    ltokens = list(filter(lambda x: len(x) > 2, ltokens))
    occ_counts = Counter(ltokens)
    variants = set(ltokens)

    if len(variants) <= 2:
        return {cid: occ_counts}

    results = []

    for x, y in map(sorted, combinations(variants, 2)):

        matches = difflib.SequenceMatcher(None, x, y).get_matching_blocks()
        matches = list(filter(lambda x: x.size > 3, matches))
        if not matches:
            continue
        for m in matches:
            c = x[m.a:m.size].strip()
            if len(c) < 3:
                continue
            results.append(c)

    scores = {}

    for substring in results:
        # Find which of the variants it matches
        # Return variant * occ_counts[variant]
        smatches = list(filter(lambda x: substring in x, variants))
        score = sum([occ_counts[m] for m in smatches])
        scores[substring] = score

    return {cid: scores}


results = [longest_match(k, v) for k, v in chain(id2company.items())]


results_all = {}
for rdict in results:
    for company_id, subs in rdict.items():
        subs = dict(subs)
        for substring, score in subs.items():
            if substring not in results_all:
                results_all[substring] = {company_id: score}
            else:
                currents = results_all[substring]
                if company_id not in currents:
                    currents[company_id] = score
                else:
                    currents[company_id] = currents[company_id] + score




def stream_ebunch():
    for substring, id_values in results_all.items():
        for company_id, score in id_values.items():
            yield (substring, company_id, score)


trips = stream_ebunch()
g = nx.Graph()
g.add_weighted_edges_from(trips)

