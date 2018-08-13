import colorsys
import math
import random
from itertools import combinations
from collections import defaultdict
import networkx as nx
from cytoolz import itertoolz
from operator import itemgetter

import numpy as np
import pandas as pd
from colour import Color

WINDOW_SIZE = 3


INCLUDING_FILTER = ['NN', 'JJ']
EXCLUDING_FILTER = []


def make_graph(tokens, window_size, edge_weighting='cooc_freq'):

    # Adapted from textacy

    windows = itertoolz.sliding_window(window_size, tokens)

    graph = nx.Graph()

    if edge_weighting == 'cooc_freq':
        cooc_mat = defaultdict(lambda: defaultdict(int))
        for window in windows:
            for w1, w2 in combinations(sorted(window), 2):
                cooc_mat[w1][w2] += 1
        graph.add_edges_from(
            (w1, w2, {'weight': cooc_mat[w1][w2]})
            for w1, w2s in cooc_mat.items() for w2 in w2s)

    elif edge_weighting == 'binary':
        graph.add_edges_from(
            w1_w2 for window in windows
            for w1_w2 in combinations(window, 2))

    return graph


def assign_deviations(scores_dict):
    std_dev = np.std(list(scores_dict.values()))
    scores_list = [(k, v) for k, v in scores_dict.items()]
    scores_list = sorted(scores_list, key=itemgetter(1))

    df = pd.DataFrame(scores_list)
    df['Cat'] = df[1].apply(lambda x: get_cat(x, std_dev))
    df1 = df[[0, 'Cat']]
    cats_created = df1['Cat'].max() + 1
    cat_dict = dict(list(df1.to_records(index=False)))
    return cat_dict, cats_created


def get_cat(x, std_dev):
    if std_dev == 0:
        return 0
    return math.floor(x/std_dev)


def get_colors(graph):
    color_idx = nx.greedy_color(graph, 'connected_sequential_dfs')
    color_dict = compute_colors_dict(color_idx)
    color_merged = {}
    for word, color_index in color_idx.items():
        color_merged[word] = color_dict[color_index]

    return color_merged


def compute_colors_dict(color_idx, low="palegreen", high="red"):
    steps = max(color_idx.values()) + 1
    low = Color(low)
    high = Color(high)
    color_list = list(low.range_to(high, steps))
    color_dict = {}
    for i, color in enumerate(color_list):
        rgb = color.get_rgb()
        rgb_web = []
        for r in rgb:
            rgb_web.append(int(r * 255))
        rgb_web = tuple(rgb_web)
        color_dict[i] = rgb_web
    return color_dict


def bright_color():
    h,s,l = random.random(), 0.5 + random.random()/2.0, 0.4 + random.random()/5.0
    r,g,b = [int(256*i) for i in colorsys.hls_to_rgb(h,l,s)]
    return (r, g, b)
