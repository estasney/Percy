from itertools import chain, combinations
from operator import itemgetter
from collections import Counter
import difflib
import string
import pickle
import re
import networkx as nx

f = "id2company.pkl"
f1 = "company2id.pkl"