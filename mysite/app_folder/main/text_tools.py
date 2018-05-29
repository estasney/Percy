import re
import string
from operator import itemgetter

import gensim
import nltk
import pandas as pd
from gensim.corpora import Dictionary
from gensim.models import TfidfModel
from gensim.summarization import keywords as KW
from gensim.summarization.textcleaner import tokenize_by_word as _tokenize_by_word
from nltk.stem.porter import PorterStemmer
from nltk.tokenize.moses import MosesTokenizer

from app_folder.site_config import FConfig
from app_folder import tfidf_model, dictionary, bigram_tfidf_model, bigram_dictionary, lems_tfidf_model, \
    lems_dictionary, lg_tfidf_model, lg_dictionary, bigram

# Raw
def load_tfidf_model():
    return tfidf_model

def load_dictionary():
    return dictionary
# Grams Only

def load_bigram_tfidf_model():
    return bigram_tfidf_model

def load_bigram_dictionary():
    return bigram_dictionary

# Lems Only

def load_lems_tfidf_model():
    return lems_tfidf_model

def load_lems_dictionary():
    return lems_dictionary

# Grams and Lems

def load_lg_tfidf_model():
    return lg_tfidf_model

def load_lg_dictionary():
    return lg_dictionary

def load_name_list():
    name_list = pd.read_csv(FConfig.name_file_path)
    name_list = name_list['names'].tolist()
    name_list = set(name_list)
    return name_list

# Phraser
def load_bigram():
    return bigram

def load_bigrammer():
    return bigram

month_list = ["jan", "january" "feb", "february", "mar", "march", "apr", "april", "may", "jun", "june", "jul", "july",
              "aug", "august", "sep", "sept", "september", "oct", "october", "nov", "november", "dec", "december"]
number_list = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]

WORD_LEN = 3

LEMMATIZER = nltk.WordNetLemmatizer()
TOKENIZER = nltk.tokenize.moses.MosesTokenizer()
STEMMER = nltk.stem.snowball.SnowballStemmer("english")
WORDNET = nltk.corpus.wordnet

# Load Stopwords
# TODO Update to my collection
stopw = gensim.parsing.preprocessing.STOPWORDS

# Punctuation
punc = string.punctuation
punc = punc + "●" + "•" + "-" + "ø"

# Stoplist
stoplist = nltk.corpus.stopwords.words('english')

# Whitespace
wht_space = set('\t\r\x0b\x0c')

def remove_noise(text, sent=False):

    tokenizer = TOKENIZER
    name_list = load_name_list()

    # CV/Resume Specific Cleaning
    regex_email = re.compile(r"((\w|\d|\.)+)(@)(\w+)(\.)(\w{3})")
    regex_dates = re.compile(r"([A-z]+\.? ?\d{2,4}| +- (P|p)resent)|(\d{2}\/\d{2}\/\d{2,4})")
    regex_phone_numbers = re.compile(r"(\d{3}(-|.)){2}(\d{4})")
    regex_three_or_more = re.compile(r"\w*(.)(\1){2,}\w*")  # If a word contains a series of 3 or more identical letters
    regex_bullets = re.compile(r"(•|✓|#|\*|●  *)|(\d[.|:])|( ?- )")
    regex_hyperlinks = re.compile(r"(http)([a-z]|[A-Z]|[\d]|\.|\/|\?|\=|&|:|-)+")
    regex_numbers_only = re.compile(r"\d+[^A-z]")
    regex_punctuation = re.compile(
        r"(!|\"|#|\$|%|&|\||\)|\(|\*|\+|,|-|\.|\/|:|;|<|=|>|\?|@|\[|\\|\]|\^|_|`|\{|\||\}|~|')")
    if sent:
        for space in wht_space:
            text.replace(space, "\n")
        sent_holder = nltk.tokenize.sent_tokenize(text)
        quiet_sents_clean = []
        for sent in sent_holder:
            sent = regex_phone_numbers.sub(" ", sent)
            sent = regex_email.sub(" ", sent)
            sent = regex_hyperlinks.sub(" ", sent)
            sent = regex_three_or_more.sub(" ", sent)
            sent = regex_numbers_only.sub(" ", sent)
            sent = regex_punctuation.sub(" ", sent)
            sent = sent.lower()
            for space in set(string.whitespace):
                sent.replace(space, " ")
            sent = tokenizer.tokenize(sent)
            sent = ' '.join([word for word in sent if word not in stopw and word not in stoplist
                             and word not in name_list and word not in punc and word not in month_list and
                             word_number_test(word) is True])
            quiet_sents_clean.append(sent)
        return quiet_sents_clean

    else:
        quiet_text = text
        quiet_text = regex_phone_numbers.sub(" ", quiet_text)
        quiet_text = regex_email.sub(" ", quiet_text)
        quiet_text = regex_hyperlinks.sub(" ", quiet_text)
        quiet_text = regex_dates.sub(" ", quiet_text)
        quiet_text = regex_three_or_more.sub(" ", quiet_text)
        quiet_text = regex_bullets.sub(" ", quiet_text)
        quiet_text = regex_numbers_only.sub(" ", quiet_text)
        quiet_text = regex_punctuation.sub(" ", quiet_text)
        clean_text = quiet_text.lower()
        for space in set(string.whitespace):
            clean_text.replace(space, " ")
            clean_text = tokenizer.tokenize(clean_text)
            clean_text = ' '.join([word for word in clean_text if word not in stopw and word not in stoplist
                                   and word not in name_list and word not in punc and word not in month_list and word_number_test(
                word) is True])
    return clean_text


def word_number_test(word):
    if any(num in word for num in number_list):
        word_length = len(word)
        number_count = 0
        for letter in word:
            if letter in number_list:
                number_count += 1
        ratio = number_count / word_length
        if ratio >= 0.1:
            return False
        else:
            return True
    else:
        return True


def document_to_tokens(clean_text, lem_tokens):

    tokenizer=TOKENIZER

    tokens = tokenizer.tokenize(clean_text)
    if lem_tokens:
        pos_tokens = nltk.pos_tag(tokens)
        stemmed_tokens = token_stemmer(pos_tokens)
        return stemmed_tokens
    else:
        tokens = ' '.join(tokens)
        return tokens


def token_stemmer(pos_tagged_tokens):

    lemmatizer = LEMMATIZER

    stemmed_tokens = []
    for tagged_tuple in pos_tagged_tokens:
        token = tagged_tuple[0]
        pos_tag = get_wordnet_pos(tagged_tuple[1])
        if pos_tag is False:
            lemmed_token = lemmatizer.lemmatize(token)
        else:
            lemmed_token = lemmatizer.lemmatize(token, pos_tag)
        stemmed_tokens.append(lemmed_token)
    stem_join_tokens = ' '.join(token for token in stemmed_tokens)
    return stem_join_tokens


# https://stackoverflow.com/questions/15586721/wordnet-lemmatization-and-pos-tagging-in-python
def get_wordnet_pos(treebank_tag):
    wordnet = WORDNET
    if treebank_tag.startswith('J'):
        return wordnet.ADJ
    elif treebank_tag.startswith('V'):
        return wordnet.VERB
    elif treebank_tag.startswith('N'):
        return wordnet.NOUN
    elif treebank_tag.startswith('R'):
        return wordnet.ADV
    else:
        return False


def clean_it(text, lem_tokens=True, gram_tokens=True, sent_mode=False):

    bigrammer = load_bigrammer()

    quiet_text = remove_noise(text, sent=sent_mode)  # sent_mode will return a list of sentences
    if sent_mode:
        sent_holder = []
        for sent in quiet_text:  # String form
            if lem_tokens:
                sent = document_to_tokens(sent, lem_tokens=True)  # returns String form
            if gram_tokens:  # Must be list form
                sent = sent.split()  # List form
                clean_tokens = bigrammer[sent]
                continue_gram = True
                while continue_gram is True:
                    new_tokens = bigrammer[clean_tokens]  # Detect new phrases, must be tokens
                    if clean_tokens != new_tokens:
                        clean_tokens = new_tokens
                    else:
                        sent = new_tokens  # List form
                        sent = ' '.join(new_tokens)  # String rom
                        continue_gram = False
            sent_holder.append(sent)  # sent clean complete, append
            # Sent Holder Ready
        return sent_holder
    elif sent_mode is False:
        if lem_tokens:
            text_tokens = document_to_tokens(quiet_text, lem_tokens=True)
        else:
            text_tokens = document_to_tokens(quiet_text, lem_tokens=False)
        text_tokens = text_tokens.split()
        clean_tokens = ' '.join(
            [token for token in text_tokens if len(token) > 2 and token not in stopw and token not in punc])
        clean_tokens = clean_tokens.split()
        if gram_tokens:
            clean_tokens = bigrammer[clean_tokens]
            continue_gram = True
            while continue_gram is True:
                new_tokens = bigrammer[clean_tokens]  # Detect new phrases, must be tokens
                if clean_tokens != new_tokens:
                    clean_tokens = new_tokens
                else:
                    continue_gram = False
        clean_tokens = ' '.join(clean_tokens)
        return clean_tokens

def wild_stem(text):
    stemmer = PorterStemmer()
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
        stem_word = stemmer.stem(word)
        if stem_word == word:
            pass
        else:
            stem_word = stem_word + "*"

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
    scored_words = [(word, float(score)) for word, score in keywords]
    words_ = [word for word, score in scored_words]
    ranked_words = []
    for i, word in enumerate(words_):
        ranked_words.append((word, i+1))
    ranked_words = sorted(ranked_words, key=itemgetter(1))

    return ranked_words

def score_tfidf(user_input, gram_mode, lem_mode):
    # clean text returned is string.
    clean_text = clean_it(user_input, lem_tokens=lem_mode, gram_tokens=gram_mode)
    # choose model from gram tokens parameter
    if gram_mode is False and lem_mode is False:
        d = load_dictionary()
        m = load_tfidf_model()
    elif gram_mode is True and lem_mode is False:
        d = load_bigram_dictionary()
        m = load_bigram_tfidf_model()
    elif gram_mode is True and lem_mode is True:
        d = load_lg_dictionary()
        m = load_lg_tfidf_model()
    elif gram_mode is False and lem_mode is True:
        d = load_lems_dictionary()
        m = load_lems_tfidf_model()
    else:
        d = load_dictionary()
        m = load_tfidf_model()

    tfidf_values = dict(m[d.doc2bow(clean_text.split())])
    tfidf_tokens = {}
    for id_token, tfidf_value in tfidf_values.items():
        token = d[id_token]
        tfidf_tokens[token] = tfidf_value
    # prettify
    # Sort the values
    tfidf_scored = sorted(tfidf_tokens.items(), key=lambda x: x[1], reverse=True)
    # Limit to 25
    tfidf_scored = tfidf_scored[:25]
    tfidf_scored = [(token, "{:.2%}".format(score)) for token, score in tfidf_scored]
    return tfidf_scored

def process_graph_text(text, phrases, word_len=WORD_LEN):
    wnl = LEMMATIZER
    split_text = list(_tokenize_by_word(text))
    if phrases:
        phraser = load_bigram()
        split_text = phraser[split_text]
    lem_text = [wnl.lemmatize(word, get_wordnet_pos_graph(pos)) for word, pos in nltk.pos_tag(split_text)]
    lem_text = [word for word in lem_text if len(word) >= word_len and word not in stopw]

    return lem_text

def get_wordnet_pos_graph(treebank_tag):
    wordnet = WORDNET
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