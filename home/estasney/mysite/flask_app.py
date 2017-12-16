import math
import os
import pickle
import re
import string
import gensim
import nltk
import pandas as pd
from flask import Flask, render_template, request, jsonify
from gensim.models import Doc2Vec, TfidfModel
from gensim.corpora import Dictionary
from gensim.summarization import keywords as KW
from nltk.stem.porter import PorterStemmer
from nltk.tokenize import sent_tokenize
from nltk.tokenize.moses import MosesTokenizer
from werkzeug.utils import secure_filename

""" LOAD CONFIG """

try:
    from config import local_config as config
except ImportError:
    from config import web_config as config

""" GLOBAL VARS HERE"""

# for local dev
#
model = Doc2Vec.load(config.model)

f = open(config.tree, "rb")

fp = open(config.name_dict, "rb")

UPLOAD_FOLDER = config.UPLOAD_FOLDER

# Load Tree Classifier

tree_model = pickle.load(f)
f.close()

# Load Name Dictionary
name_dict = pickle.load(fp)
fp.close()

# Load Stopwords
stopw = gensim.parsing.preprocessing.STOPWORDS

# Punctuation
punc = string.punctuation
punc = punc + "●" + "•" + "-" + "ø"

# Tokenizer
tokenizer = nltk.tokenize.moses.MosesTokenizer()

# Stemmer
stemmer = nltk.stem.snowball.SnowballStemmer("english")

# Stoplist
stoplist = nltk.corpus.stopwords.words('english')

# Whitespace
wht_space = set('\t\r\x0b\x0c')

# Namelist
name_list = pd.read_csv(config.name_file_path)
name_list = name_list['names'].tolist()
name_list = set(name_list)

# Phraser
bigram = gensim.models.Phrases.load(config.gram_path)
bigrammer = gensim.models.phrases.Phraser(bigram)

"""

TFIDF Variables

"""


# Raw
tfidf_model = TfidfModel.load(config.tfidf_model)
dictionary = Dictionary.load(config.raw_dict)
# Grams Only
bigram_tfidf_model = TfidfModel.load(config.bigram_tfidf_model_path)
bigram_dictionary = Dictionary.load(config.bigram_dict_path)
# Lems Only
lems_tfidf_model = TfidfModel.load(config.lem_tfidf_model_path)
lems_dictionary = Dictionary.load(config.lem_dict_path)
# Grams and Lems
lg_tfidf_model = TfidfModel.load(config.lg_tfidf_model_path)
lg_dictionary = Dictionary.load(config.lg_dict_path)

month_list = ["jan", "january" "feb", "february", "mar", "march", "apr", "april", "may", "jun", "june", "jul", "july",
              "aug", "august", "sep", "sept", "september", "oct", "october", "nov", "november", "dec", "december"]
number_list = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]

""" GLOBAL END"""


"""

UPLOAD PARAMETERS HERE

"""




"""

Hack to include an API for other projects

"""

dupcheck_version = config.dupcheck_version


@app.route('/api/dupchecker/version', methods=['GET'])
def get_version():
    return jsonify({'version': dupcheck_version})

@app.route('/')
def hello_world():
    return render_template('home_page.html')


@app.route('/diversity')
def diversity():
    return render_template('diversity_score.html')


@app.route('/stemmed')
def stemmed():
    return render_template('stemmed.html')


@app.route('/keywords')
def keywords():
    return render_template('keywords.html')


@app.route('/related')
def related():
    return render_template('related.html')


@app.route('/thisplusthat')
def thisplusthat():
    return render_template('thisplusthat.html')


@app.route('/infer')
def infer():
    return render_template('infer.html')

@app.route('/tfidf_measures')
def tfidf():
    return render_template('tf_idf.html')

@app.route('/', methods=['POST'])
def my_sims():
    if request.form['button'] == 'query':  # similar words search
        user_query = request.form['query'].lower()
        try:
            result = dict(model.similar_by_word(user_query))
            return render_template('related.html', result=result, success='True', title_h2='Word Similarity Score',
                                   title_th='Similarity Score', original=user_query)
        except KeyError as error:
            error_message = str(error)
            offending_term = error_message.split("'")[1]
            result = offending_term.title()
            return render_template('related.html', result=result, success='False')
    elif request.form['button'] == 'math':
        word_one = request.form['word1'].lower()
        word_two = request.form['word2'].lower()
        word_three = request.form['word3'].lower()
        try:
            if word_three == '':
                user_equation = word_one.title() + " + " + word_two.title() + " = "
                result = dict(model.most_similar(positive=[word_one, word_two]))
            else:
                user_equation = word_one.title() + " + " + word_two.title() + " - " + word_three.title() + " = "
                result = dict(model.most_similar(positive=[word_one, word_two], negative=[word_three]))
            return render_template('thisplusthat.html', result=result, success='True', user_equation=user_equation,
                                   word_one=word_one.strip(), word_two=word_two.strip(), word_three=word_three.strip())
        except KeyError as error:
            error_message = str(error)
            offending_term = error_message.split("'")[1]
            result = offending_term.title()
            return render_template('thisplusthat.html', result=result, success='False')
    elif request.form['button'] == 'keywords':
        try:
            raw_text = str(request.form['raw_text'])
            raw_text = ' '.join([word for word in raw_text.split()])
            sentences = sent_tokenize(raw_text)
            sentence_keywords = []
            for sentence in sentences:
                try:
                    sent_keyw = KW(sentence)
                    if len(sent_keyw) > 0:
                        sent_keyw = sent_keyw.splitlines()
                        if len(sent_keyw) > 1:
                            sent_keyw = ', '.join([word for word in sent_keyw if len(sent_keyw) > 1])
                        else:
                            sent_keyw = ' '.join([word for word in sent_keyw])
                        sentence_keywords.append(sent_keyw)
                except:
                    pass
            user_keywords = sentence_keywords
            return render_template('keywords.html', keywords=user_keywords, success='True', original=raw_text)
        except:
            return render_template('keywords.html', success='False')
    elif request.form['button'] == 'raw_stem':
        stemmer = PorterStemmer()
        bool_logic = ["OR", "AND", "NOT"]
        re_words = re.compile(r"(\w+)")
        search = request.form['raw_stem']
        terms = search.split()
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
        return render_template('stemmed.html', stemmed_bool=stemmed_bool, success='True', original=search)
    elif request.form['button'] == 'infer_name':
        # Todo import
    elif request.form['button'] == 'Upload':
        # TODO Add Check for Use Global Dict
        # TODO import
        # Validate Header

    elif request.form['button'] == 'tfidf':
        user_input = request.form['tfidf_text']
        if len(user_input) > 10000:
            return render_template('tf_idf.html', success='False', original="Text Size Limit Exceeded", error_message="Text Size Limit Exceeded")
        user_form = request.form
        gram_mode = user_form.get('gram_tokens', False)
        lem_mode = user_form.get('lem_tokens', False)
        if gram_mode == 'on':
            gram_mode = True
        if lem_mode == 'on':
            lem_mode = True
        # clean text returned is string.
        clean_text = clean_it(user_input, lem_tokens=lem_mode, gram_tokens=gram_mode)
        # choose model from gram tokens parameter
        if gram_mode is False and lem_mode is False:
            d = dictionary
            m = tfidf_model
        elif gram_mode is True and lem_mode is False:
            d = bigram_dictionary
            m = bigram_tfidf_model
        elif gram_mode is True and lem_mode is True:
            d = lg_dictionary
            m = lg_tfidf_model
        elif gram_mode is False and lem_mode is True:
            d = lems_dictionary
            m = lems_tfidf_model
        else:
            d = dictionary
            m = tfidf_model

        tfidf_values = dict(m[d.doc2bow(clean_text.split())])
        tfidf_tokens = {}
        for id_token, tfidf_value in tfidf_values.items():
            token = d[id_token]
            tfidf_tokens[token] = round(tfidf_value, 4)
        # Sort the values
        tfidf_scored = sorted(tfidf_tokens.items(), key=lambda x: x[1], reverse=True)
        # Limit to 25
        tfidf_scored = tfidf_scored[:25]
        return render_template('tf_idf.html', success='True', original=user_input, result=tfidf_scored)

def remove_noise(text, sent=False):
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
    tokens = tokenizer.tokenize(clean_text)
    if lem_tokens:
        pos_tokens = nltk.pos_tag(tokens)
        stemmed_tokens = token_stemmer(pos_tokens)
        return stemmed_tokens
    else:
        tokens = ' '.join(tokens)
        return tokens


def token_stemmer(pos_tagged_tokens):
    lemmatizer = nltk.WordNetLemmatizer()
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
    wordnet = nltk.corpus.wordnet
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


if __name__ == '__main__':
    app.run()
