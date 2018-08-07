import re

from gensim.parsing.preprocessing import strip_tags, strip_punctuation, strip_multiple_whitespaces, \
    strip_numeric, strip_short, stem_text
from gensim.summarization import keywords as KW
from gensim.utils import lemmatize

# Raw

months = {}

char_search_ = re.compile(r"[^\u0020\u0027\u002c-\u002e\u0030-\u0039\u0041-\u005a\u0061-\u007a]")
strip_multi_ws_ = re.compile(r"( {2,})")

STOPWORDS = frozenset(
    ['a', 'about', 'above', 'across', 'after', 'afterwards', 'again', 'against', 'ain', 'all', 'almost',
     'alone', 'along', 'already', 'also', 'although', 'always', 'am', 'among', 'amongst', 'amoungst', 'amount',
     'an', 'and', 'another', 'any', 'anyhow', 'anyone', 'anything', 'anyway', 'anywhere', 'are', 'aren',
     "aren't", 'around', 'as', 'at', 'back', 'be', 'became', 'because', 'become', 'becomes', 'becoming', 'been',
     'before', 'beforehand', 'behind', 'being', 'below', 'beside', 'besides', 'between', 'beyond', 'bill',
     'both', 'bottom', 'but', 'by', 'call', 'can', 'cannot', 'cant', 'co', 'computer', 'con', 'could', 'couldn',
     "couldn't", 'couldnt', 'cry', 'd', 'de', 'describe', 'detail', 'did', 'didn', "didn't", 'do', 'does',
     'doesn', "doesn't", 'doing', 'don', "don't", 'done', 'down', 'due', 'during', 'each', 'eg', 'eight',
     'either', 'eleven', 'else', 'elsewhere', 'empty', 'enough', 'etc', 'even', 'ever', 'every', 'everyone',
     'everything', 'everywhere', 'except', 'few', 'fifteen', 'fify', 'fill', 'find', 'fire', 'first', 'five',
     'for', 'former', 'formerly', 'forty', 'found', 'four', 'from', 'front', 'full', 'further', 'get', 'give',
     'go', 'had', 'hadn', "hadn't", 'has', 'hasn', "hasn't", 'hasnt', 'have', 'haven', "haven't", 'having',
     'he', 'hence', 'her', 'here', 'hereafter', 'hereby', 'herein', 'hereupon', 'hers', 'herself', 'him',
     'himself', 'his', 'how', 'however', 'hundred', 'i', 'ie', 'if', 'in', 'inc', 'indeed', 'interest', 'into',
     'is', 'isn', "isn't", 'it', "it's", 'its', 'itself', 'just', 'keep', 'kg', 'km', 'last', 'latter',
     'latterly', 'least', 'less', 'll', 'ltd', 'm', 'ma', 'made', 'make', 'many', 'may', 'me', 'meanwhile',
     'might', 'mightn', "mightn't", 'mill', 'mine', 'more', 'moreover', 'most', 'mostly', 'move', 'much',
     'must', 'mustn', "mustn't", 'my', 'myself', 'name', 'namely', 'needn', "needn't", 'neither', 'never',
     'nevertheless', 'next', 'nine', 'no', 'nobody', 'none', 'noone', 'nor', 'not', 'nothing', 'now', 'nowhere',
     'o', 'of', 'off', 'often', 'on', 'once', 'one', 'only', 'onto', 'or', 'other', 'others', 'otherwise',
     'our', 'ours', 'ourselves', 'out', 'over', 'own', 'part', 'per', 'perhaps', 'please', 'put', 'quite',
     'rather', 're', 'really', 'regarding', 's', 'same', 'say', 'see', 'seem', 'seemed', 'seeming', 'seems',
     'serious', 'several', 'shan', "shan't", 'she', "she's", 'should', "should've", 'shouldn', "shouldn't",
     'show', 'side', 'since', 'sincere', 'six', 'sixty', 'so', 'some', 'somehow', 'someone', 'something',
     'sometime', 'sometimes', 'somewhere', 'still', 'such', 'system', 't', 'take', 'ten', 'than', 'that',
     "that'll", 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'thence', 'there', 'thereafter',
     'thereby', 'therefore', 'therein', 'thereupon', 'these', 'they', 'thick', 'thin', 'third', 'this', 'those',
     'though', 'three', 'through', 'throughout', 'thru', 'thus', 'to', 'together', 'too', 'top', 'toward',
     'towards', 'twelve', 'twenty', 'two', 'un', 'under', 'unless', 'until', 'up', 'upon', 'us', 'used',
     'using', 'various', 've', 'very', 'via', 'was', 'wasn', "wasn't", 'we', 'well', 'were', 'weren', "weren't",
     'what', 'whatever', 'when', 'whence', 'whenever', 'where', 'whereafter', 'whereas', 'whereby', 'wherein',
     'whereupon', 'wherever', 'whether', 'which', 'while', 'whither', 'who', 'whoever', 'whole', 'whom',
     'whose', 'why', 'will', 'with', 'within', 'without', 'won', "won't", 'would', 'wouldn', "wouldn't", 'y',
     'yet', 'you', "you'd", "you'll", "you're", "you've", 'your', 'yours', 'yourself', 'yourselves',
     'experience', "jan", "january" "feb", "february", "mar", "march", "apr", "april", "may", "jun", "june",
     "jul", "july", "aug", "august", "sep", "sept", "september", "oct", "october", "nov", "november", "dec",
     "december"])


def char_search(s, search=char_search_):
    x = search.sub(string=s, repl=" ")
    return x


def remove_stopwords(s, sw=STOPWORDS):
    return " ".join(w for w in s.split() if w not in sw)


DEFAULT_FILTERS = frozenset([
    char_search, lambda x: x.lower(), strip_tags, strip_punctuation,
    strip_multiple_whitespaces, strip_numeric,
    remove_stopwords, strip_short, lemmatize
])


def preprocess_text(s, filters=DEFAULT_FILTERS):
    for f in filters:
        s = f(s)
    return s


def wild_stem(text):
    bool_logic = ["OR", "AND", "NOT"]
    re_words = re.compile(r"(\w+)")
    terms = text.split()
    mod_terms = []
    for term in terms:
        if term in bool_logic:
            mod_terms.append(term)
            continue
        word_matches = re_words.findall(term)
        word = ' '.join(word_matches)  # List to string
        other_char = term.replace(word, "")
        stem_word = stem_text(word)
        if stem_word != word:
            stem_word += stem_word + "*"

        if len(other_char) == 0:  # Is a operator present?
            mod_terms.append(stem_word)
            continue
        char_position = term.find(other_char)
        if char_position == 0:
            full_term = other_char + stem_word
        else:
            full_term = stem_word + other_char
        mod_terms.append(full_term)
    stemmed_bool = ' '.join(mod_terms)
    return stemmed_bool


def get_keywords(text):
    raw_text = str(text)
    keywords = KW(raw_text, split=True, scores=True)
    return keywords


def score_tfidf(text):
    # clean text returned is string.
    tokens = preprocess_text(text)
    # TODO


def process_graph_text(text, phrases, min_word_len=3):
    lem_tokens = preprocess_text(text)
    lem_tokens = list(filter(lambda x: len(x) > min_word_len, lem_tokens))
    return lem_tokens
