import math
import os
import pickle
import re
import string


import gensim
import nltk
import pandas as pd
from flask import Flask, render_template, request
from gensim.models import Doc2Vec, TfidfModel
from gensim.corpora import Dictionary
from gensim.summarization import keywords as KW
from nltk.stem.porter import PorterStemmer
from nltk.tokenize import sent_tokenize
from nltk.tokenize.moses import MosesTokenizer
from werkzeug.utils import secure_filename

""" GLOBAL VARS HERE"""

# for local dev
#
# # model = Doc2Vec.load(r"C:\Users\estasney\PycharmProjects\webwork\home\estasney\mysite\mymodel.model")
# # model = Doc2Vec.load(r"C:\Users\erics_qp7a9\PycharmProjects\percy1\Percy\home\estasney\mysite\mymodel.model")
#
# # f = open(r"C:\Users\estasney\Google Drive\IPython Books\Diversity Notebooks\names\Models\tree_classifier.pickle", "rb")
# f = open(r"C:\Users\erics_qp7a9\Google Drive\IPython Books\Diversity Notebooks\names\Models\tree_classifier.pickle", "rb")
#
# # fp = open(r"C:\Users\estasney\Google Drive\IPython Books\Diversity Notebooks\names\Models\name_dict.pickle", "rb")
# fp = open(r"C:\Users\erics_qp7a9\Google Drive\IPython Books\Diversity Notebooks\names\Models\name_dict.pickle", "rb")
#
# dict_path = os.path.join("C:\\Users\\", os.getlogin(), r"Google Drive\IPython Books\Perseus Notebooks\Models\tfidf_dict.dict")
# bigram_dict_path = os.path.join("C:\\Users\\", os.getlogin(), r"Google Drive\IPython Books\Perseus Notebooks\Models\bigram_tfidf_dict.dict")
# tfidf_model_path = os.path.join("C:\\Users\\", os.getlogin(), r"Google Drive\IPython Books\Perseus Notebooks\Models\tfidf.model")
# bigram_tfidf_model_path = os.path.join("C:\\Users\\", os.getlogin(), r"Google Drive\IPython Books\Perseus Notebooks\Models\bigram_tfidf.model")
#
# UPLOAD_FOLDER = r"C:\Users\erics_qp7a9\PycharmProjects\percy1\Percy\home\estasney\mysite\uploads"
# # UPLOAD_FOLDER = r"C:\Users\estasney\PycharmProjects\webwork\home\estasney\mysite\uploads"
#
# gram_path = os.path.join("C:\\Users\\", os.getlogin(), r"Google Drive\IPython Books\trigram_model.p")
#
# name_file_path = os.path.join("C:\\Users\\", os.getlogin(),
#                               r"Google Drive\IPython Books\Perseus Notebooks\Data\name_list.csv")

# for web
#
model = Doc2Vec.load('/home/estasney/mysite/mymodel.model')
f = open("/home/estasney/mysite/tree_classifier.pickle", "rb")
fp = open('/home/estasney/mysite/name_dict.pickle', "rb")
dict_path = '/home/estasney/mysite/tfidf_dict.dict'
bigram_dict_path = '/home/estasney/mysite/bigram_tfidf_dict.dict'
tfidf_model_path = '/home/estasney/mysite/tfidf.model'
bigram_tfidf_model_path = '/home/estasney/mysite/bigram_tfidf.model'
gram_path = '/home/estasney/mysite/trigram_model.p'
name_file_path '/home/estasney/mysite/name_list.csv'

UPLOAD_FOLDER = ('/home/estasney/mysite/uploads')

# common

tree_model = pickle.load(f)
f.close()
name_dict = pickle.load(fp)
fp.close()
stopw = gensim.parsing.preprocessing.STOPWORDS
punc = string.punctuation
punc = punc + "●" + "•" + "-" + "ø"
tokenizer = nltk.tokenize.moses.MosesTokenizer()
stemmer = nltk.stem.snowball.SnowballStemmer("english")
stoplist = nltk.corpus.stopwords.words('english')
wht_space = set('\t\r\x0b\x0c')
name_list = pd.read_csv(name_file_path)
name_list = name_list['names'].tolist()
name_list = set(name_list)
bigram = gensim.models.Phrases.load(gram_path)
bigrammer = gensim.models.phrases.Phraser(bigram)
tfidf_model = TfidfModel.load(tfidf_model_path)
bigram_tfidf_model = TfidfModel.load(bigram_tfidf_model_path)
dictionary = Dictionary.load(dict_path)
bigram_dictionary = Dictionary.load(bigram_dict_path)
month_list = ["jan", "january" "feb", "february", "mar", "march", "apr", "april", "may", "jun", "june", "jul", "july",
              "aug", "august", "sep", "sept", "september", "oct", "october", "nov", "november", "dec", "december"]
number_list = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]

""" GLOBAL END"""


"""

UPLOAD PARAMETERS HERE

"""


ALLOWED_EXTENSIONS = ['.csv', '.xlsx']

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

""" 

UPLOAD SPECIFIC FUNCTIONS

"""


def allowed_file(filename):
    ext = "." + filename.rsplit('.', 1)[1]
    if ext in ALLOWED_EXTENSIONS:
        return ext
    else:
        print("ext : " + ext + "not approved")


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
        user_query_name = request.form['infer_name']
        inferred_gender = tree_model.classify(gender_features(user_query_name)).title()
        gender_lookup = retrieve_name(user_query_name, name_dict)[1]  # Selecting the message
        return render_template('infer.html', user_query=user_query_name, success='True', gender_guess=inferred_gender,
                               lookup_message=gender_lookup)
    elif request.form['button'] == 'Upload':
        if 'file' not in request.files:
            return render_template('diversity_score.html')
        file = request.files['file']
        if file.filename == '':
            return render_template('diversity_score.html', success='False')
        if file and allowed_file(file.filename):
            name_header = request.form['header_name']
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            upped_file = os.path.join(app.config['UPLOAD_FOLDER'],
                                      filename)
            file_ext = find_file_ext(upped_file)
            if file_ext == 'csv':
                try:
                    df = pd.read_csv(upped_file)
                except:
                    try:
                        df = pd.read_csv(upped_file, encoding='latin1')
                    except:
                        try:
                            df = pd.read_csv(upped_file, encoding='cp1252')
                        except:
                            try:
                                df = pd.read_csv(upped_file, encoding='iso-8859-1')
                            except:
                                return render_template('diversity_score.html', success='False',error_message="Your file's encoding was not recognized")

            elif file_ext == 'xlsx':
                try:
                    df = pd.read_excel(upped_file)
                except:
                    try:
                        df = pd.read_excel(upped_file, encoding='latin1')
                    except:
                        try:
                            df = pd.read_excel(upped_file, encoding='cp1252')
                        except:
                            try:
                                df = pd.read_excel(upped_file, encoding='iso-8859-1')
                            except:
                                return render_template('diversity_score.html', success='False',
                                                       error_message="Your file's encoding was not recognized")

            names_col = df[name_header]
            diversity_scored = retrieve_names_bulk(names_col)
            male_count = str(diversity_scored['male'])
            female_count = str(diversity_scored['female'])
            unknown_count = str(diversity_scored['unknown'])
            ai_names = diversity_scored['ai_names']

            return render_template('diversity_score.html', success='True', male_count=male_count,
                                   female_count=female_count, unknown_count=unknown_count, ai_names=ai_names)

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
        if gram_mode is True:
            d = bigram_dictionary
            m = bigram_tfidf_model
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



def gender_features(name):
    name = name.lower()
    features = {}
    features['first_two'] = name[:2]
    features['last_letter'] = name[-1]
    features['last_letter_vowel'] = vowel_test(name[-1])
    features['last_two'] = name[-2:]
    return features


def vowel_test(letter):
    vowels = ["a", "e", "i", "o", "u", "y"]
    if letter in vowels:
        return "Yes"
    else:
        return "No"


def retrieve_name(name, name_dict):
    name = name.lower()
    try:
        male_count = name_dict[name]['M']
        female_count = name_dict[name]['F']
        if male_count > female_count:
            try:
                likely = round(male_count / female_count, 1)
                if math.isinf(likely):
                    message = "The name {} is only known to be male".format(name.title())
                    winner = ('M', 999)
                else:
                    message = "The name {} is {}x more likely to be male".format(name.title(), likely)
                    winner = ('M', likely)
            except ZeroDivisionError:
                message = "The name {} is only known to be male"
                winner = ('M', 999)
        elif male_count < female_count:
            try:
                likely = round(female_count / male_count, 1)
                if math.isinf(likely):
                    message = "The name {} is only known to be female".format(name.title())
                    winner = ('F', 999)
                else:
                    message = "The name {} is {}x more likely to be female".format(name.title(), likely)
                    winner = ('F', likely)
            except ZeroDivisionError:
                message = "The name {} is only known to be female"
                winner = ('F', 999)
        else:
            message = "The name {} is ambiguous".format(name.title())
            return False, message
        return winner, message
    except KeyError:
        message = "I have not see the name {} before".format(name.title())
        return False, message


def retrieve_names_bulk(name_list):

    male_count = 0
    female_count = 0
    unknown_count = 0
    unknown_dict = {}
    for name in name_list:
        try:
            gender_lookup = retrieve_name(name, name_dict)[0][0]
            if gender_lookup == 'M':
                male_count += 1
            elif gender_lookup == 'F':
                female_count += 1
        except TypeError:
            # Use decision tree model

            inferred_gender = guess_name(name).lower()
            if inferred_gender == 'male':
                male_count = male_count + 1
                unknown_count = unknown_count + 1
                unknown_dict[name.title()] = 'Male'
            elif inferred_gender == 'female':
                female_count = female_count + 1
                unknown_count = unknown_count + 1
                unknown_dict[name.title()] = 'Female'
    diversity_score_dict = {'male': male_count, 'female': female_count, 'unknown': unknown_count, 'ai_names':unknown_dict}
    return diversity_score_dict

def find_file_ext(filename):
    ext = filename.split(".")[-1]  # return the last split
    return ext

def guess_name(name):
    inferred_gender = tree_model.classify(gender_features(name)).title()
    return inferred_gender

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
