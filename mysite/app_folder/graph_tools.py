import colorsys
import math
import random
from itertools import combinations
from operator import itemgetter

import numpy as np
import pandas as pd
from colour import Color
from gensim.summarization.graph import Graph
from gensim.utils import chunkize_serial

WINDOW_SIZE = 3
WORD_LEN = 3

INCLUDING_FILTER = ['NN', 'JJ']
EXCLUDING_FILTER = []


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
    return math.floor(x/std_dev)


def compute_colors_dict(steps, low="blue", high="red"):
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


def remaining_windows(lem_text):
    return lem_text[WINDOW_SIZE:]


def get_first_window(lem_text):
    return lem_text[:WINDOW_SIZE]


def generate_chunks(remaining_window):
    return chunkize_serial(remaining_window, WINDOW_SIZE, as_numpy=False)


def generate_combos(remaining_window):
    chunks = generate_chunks(remaining_window)
    for chunk in chunks:
        for word_a, word_b in combinations(chunk, 2):
            yield word_a, word_b


def process_remaining_windows(graph, lem_text):
    remaining_window = remaining_windows(lem_text)
    combos = generate_combos(remaining_window)
    for word_a, word_b in combos:
        set_graph_edge(graph, lem_text, word_a, word_b)


def add_nodes(lem_text, graph):
    for token in lem_text:
        if not graph.has_node(token):
            graph.add_node(token)


def process_first_window(graph, lem_text):
    first_window = get_first_window(lem_text)
    for word_a, word_b in combinations(first_window, 2):
        set_graph_edge(graph, lem_text, word_a, word_b)


def set_graph_edge(graph, lem_text, word_a, word_b):
    if word_a in lem_text and word_b in lem_text:
        edge = (word_a, word_b)
    if graph.has_node(word_a) and graph.has_node(word_b) and not graph.has_edge(edge):
        graph.add_edge(edge)


def build_graph(lem_text):
    graph = Graph()
    add_nodes(lem_text, graph)
    process_first_window(graph, lem_text)
    process_remaining_windows(graph, lem_text)
    return graph

