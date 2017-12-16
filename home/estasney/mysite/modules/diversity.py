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

try:
    from config import local_config as config
except ImportError:
    from config import web_config as config

ALLOWED_EXTENSIONS = ['.csv', '.xlsx']
TRY_ENCODINGS = ['', 'latin1', 'cp1252', 'iso-8859-1']

UPLOAD_FOLDER = config.UPLOAD_FOLDER

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

""" 

UPLOAD SPECIFIC FUNCTIONS

"""

class UploadManager(object):

    allowed_extensions = ALLOWED_EXTENSIONS
    try_encodings = TRY_ENCODINGS

    def __init__(self, request_object):
        self.request_object = request_object
        self.uploaded_filename = self.receive_upload_()
        self.uploaded_file = None
        if self.uploaded_filename:
            self.uploaded_file = self.open_file()


    @staticmethod
    def find_file_ext(filename):
        ext = "." + filename.rsplit('.', 1)[-1]
        return ext

    def allowed_file_(self, filename):
        ext = self.find_file_ext(filename)
        if ext in self.allowed_extensions:
            return True
        else:
            return False

    def receive_upload_(self):
        # TODO return False rather than rendering template for failures
        """

        Checks for common errors and omissions with uploading files
        Checks for secure filename
        Saves to disk and returns the filepath

        :param request_object: pass the request object received
        :return: file_path
        """

        # No file included
        if 'file' not in self.request_object.files:
            return render_template('diversity_score.html')

        file = self.request_object['file']

        # Blank file included
        if file.filename == '':
            return render_template('diversity_score.html', success='False', error_message='No File Selected')

        # File included
        if file and self.allowed_file_(file.filename):
            name_header = request.form['header_name']
            # If user doesn't add a name header
            if name_header == '':
                return render_template('diversity_score.html', success='False',
                                       error_message='You forgot to include the header that contains the first names')

        filename = secure_filename(file.filename)

        if self.allowed_file_(filename) is False:
            return None

        # Save file to open later for analysis
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Save location
        file_path = os.path.join(app.config['UPLOAD_FOLDER'],
                                  filename)

        return file_path

    def open_file(self):

        """
        Function that handles opening the spreadsheet with pandas
        Gets file extension and uses appropriate open method with pandas
        Tries several encodings until opening is successful or ends with fail

        :return: pd.DataFrame() or False if fail to open
        """

        file_ext = self.find_file_ext(self.uploaded_filename)
        try_encodings = self.try_encodings
        if file_ext == 'csv':
            open_method = pd.read_csv
        elif file_ext == '.xls' or file_ext == '.xlsx':
            open_method = pd.read_excel
        else:
            # No file extension found
            return False

        for encoding in try_encodings:
            try:
                df = open_method(self.uploaded_filename, encoding=encoding)
                return df
            except:
                if encoding == try_encodings[-1]:
                    # Tried all encodings, all failed
                    return False
                else:
                    continue

def validate_header(df, name_header):

    """
    Function that tries different casing of user entered name header
    :param df: dataframe
    :param name_header: the user name header
    :return: name_header or cased_name_header
    """

    df_headers = set(df.columns.tolist())
    if name_header in df_headers:
        return name_header

    # Try changing casing
    casing_f = [lambda x: x.upper(), lambda x: x.lower(), lambda x: x.title()]

    for cf in casing_f:
        cased_name_header = cf(name_header)
        if cased_name_header in df_headers:
            return cased_name_header

    return False

def parse_sheet(df, name_header):
    """


    :param df:
    :return:
    """

    valid_name_header = validate_header(df, name_header)
    if valid_name_header:
        try:
            names_col = df[valid_name_header]
        except KeyError:
            return False

    user_form = request.form
    global_name_mode = user_form.get('use_global_names', False)

    diversity_scored = retrieve_names_bulk(names_col, global_name_mode)
    male_count = str(diversity_scored['male'])
    female_count = str(diversity_scored['female'])
    unknown_count = str(diversity_scored['unknown'])
    ai_names = diversity_scored['ai_names']

    return render_template('diversity_score.html', success='True', male_count=male_count,
                           female_count=female_count, unknown_count=unknown_count, ai_names=ai_names)

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


def retrieve_names_bulk(name_list, global_mode=False):

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



def guess_name(name):
    inferred_gender = tree_model.classify(gender_features(name)).title()
    return inferred_gender

user_query_name = request.form['infer_name']
        inferred_gender = tree_model.classify(gender_features(user_query_name)).title()
        gender_lookup = retrieve_name(user_query_name, name_dict)[1]  # Selecting the message
        return render_template('infer.html', user_query=user_query_name, success='True', gender_guess=inferred_gender,
                               lookup_message=gender_lookup)