import re

from gensim.parsing.preprocessing import strip_tags, strip_punctuation, strip_multiple_whitespaces, \
    strip_numeric, strip_short, stem_text
from gensim.summarization import keywords as KW
from gensim.utils import lemmatize
import nltk


# Raw

char_search_ = re.compile(r"[^\u0020\u0027\u002c-\u002e\u0030-\u0039\u0041-\u005a\u0061-\u007a]")
strip_multi_ws_ = re.compile(r"( {2,})")
quoted_terms = re.compile(r"(?:'|\")([A-z ]+)(?:'|\")")
word_re = re.compile(r"([\w|-]+)")

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
     "december", "team", "level", "work"])


def char_search(s, search=char_search_):
    x = search.sub(string=s, repl=" ")
    return x


def remove_stopwords(s, sw=STOPWORDS):
    return " ".join(w for w in s.split() if w not in sw)


def get_wordnet_pos_graph(treebank_tag, wordnet=nltk.corpus.wordnet):
    if treebank_tag.startswith('J'):
        return wordnet.ADJ
    elif treebank_tag.startswith('V'):
        return wordnet.VERB
    elif treebank_tag.startswith('N'):
        return wordnet.NOUN
    elif treebank_tag.startswith('R'):
        return wordnet.ADV
    else:
        return wordnet.NOUN


def lemmatize_text(s, lemmatizer_=nltk.wordnet.WordNetLemmatizer):
    lemmatizer = lemmatizer_()
    accept_tags = re.compile(r"([A-Z]{2,})")  # We want all tags
    lemmas = lemmatize(s, accept_tags)
    lemmas = [x.decode() for x in lemmas]

    def lem_token(grp):
        try:
            token, pos = grp.split("/")
        except IndexError:
            return grp
        pos = get_wordnet_pos_graph(pos)
        lem_token = lemmatizer.lemmatize(token, pos)
        return lem_token

    lem_tokens = list(map(lem_token, lemmas))
    return " ".join(lem_tokens)


DEFAULT_FILTERS = frozenset([
    char_search, lambda x: x.lower(), strip_tags, strip_punctuation,
    strip_multiple_whitespaces, strip_numeric,
    remove_stopwords, strip_short, lemmatize_text
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


def process_graph_text(text, stopwords=STOPWORDS):

    from pattern.en import parsetree

    def filter_chunks(chunk, f=frozenset(['NP'])):
        if chunk.pos in f:
            return True
        else:
            return False

    def normalize_chunk(chunk, stopwords=stopwords):
        normed = [word for word in chunk.lemmata if word not in stopwords and len(word) > 4]
        if not normed:
            return None
        else:
            normed = " ".join(normed)
            if len(normed) > 4:
                return normed
            else:
                return None

    tree = parsetree(text, tokenize=True, tags=True, chunks=True, relations=False, lemmata=True)

    text_chunks = [chunk for chunks in [sent.chunks for sent in tree] for chunk in chunks]
    filtered_chunks = list(filter(lambda x: filter_chunks(x), text_chunks))

    del text_chunks

    normed_chunks = list(map(normalize_chunk, filtered_chunks))
    normed_chunks = list(filter(lambda x: x is not None, normed_chunks))
    return normed_chunks


def parse_form_text(text):
    """
    Given a string such as :
        Cloud, Software, "Quality Assurance", pre-sale
    return text as:
        ['cloud', 'software', 'quality_assurance', pre-sale]
    """
    quoted_form_terms = quoted_terms.findall(text)
    text = quoted_terms.sub("", text)
    terms = word_re.findall(text)
    terms.extend(quoted_form_terms)

    def prep_tokens(x):
        return x.strip().lower().replace(" ", "_")

    parsed_terms = list(map(prep_tokens, terms))
    return parsed_terms

