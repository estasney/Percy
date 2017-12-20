import os
import pandas as pd
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename

try:
    from config import local_config as config
except ImportError:
    from config import web_config as config

""" 

GLOBAL PARAMETERS

"""
ALLOWED_EXTENSIONS = ['.csv', '.xls', '.xlsx']

@app.context_processor
def inject_allowed_ext():
    return dict(allowed_ext=ALLOWED_EXTENSIONS)





TRY_ENCODINGS = ['', 'latin1', 'cp1252', 'iso-8859-1']

UPLOAD_FOLDER = config.UPLOAD_FOLDER

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


class UploadManager(object):
    """
    class object to handle heavy lifting of receiving files via upload
    """

    # TODO Make more generic by removing some of the header and pandas specific functions
    allowed_extensions = ALLOWED_EXTENSIONS
    try_encodings = TRY_ENCODINGS

    def __init__(self, request_object):
        self.request_object = request_object
        self.uploaded_filename = self.receive_upload_()
        self.uploaded_file = None
        self.status = None
        if self.uploaded_filename:
            self.uploaded_file = self.open_file_()
        self.valid_header = None
        if self.uploaded_file:
            self.valid_header = self.validate_header_()
        self.data = None
        if self.valid_header:
            self.data = self.parse_sheet_()

    @staticmethod
    def find_file_ext(filename):
        ext = "." + filename.rsplit('.', 1)[-1]
        return ext

    def allowed_file_(self, filename):
        ext = self.find_file_ext(filename)
        if ext in self.allowed_extensions:
            return True
        else:
            self.status = "Extension {} not permitted".format(ext)
            return False

    def receive_upload_(self):
        # TODO return False rather than rendering template for failures
        """
        Checks for common errors and omissions with uploading files
        Checks for secure filename
        Saves to disk and returns the filepath
        :return: file_path
        """

        # No file included
        if 'file' not in self.request_object.files:
            return render_template('diversity_score.html')

        file = self.request_object['file']

        # Blank file included
        if file.filename == '':
            self.status = "Your file name is blank"
            return False

        # File included
        if file and self.allowed_file_(file.filename):
            name_header = request.form['header_name']
            # If user doesn't add a name header
            if name_header == '':
                self.status = 'You forgot to include the header that contains the first names'
                return False

        filename = secure_filename(file.filename)

        if self.allowed_file_(filename) is False:
            return None

        # Save file to open later for analysis
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Save location
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        return file_path

    def open_file_(self):

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
            self.status = 'No file extension was found'
            return False

        for encoding in try_encodings:
            try:
                df = open_method(self.uploaded_filename, encoding=encoding)
                return df
            except:
                if encoding == try_encodings[-1]:
                    # Tried all encodings, all failed
                    self.status = "Unable to determine file encoding"
                    return False
                else:
                    continue

    def validate_header_(self):

        """
        Function that tries different casing of user entered name header
        :return: name_header or cased_name_header
        """
        user_header = self.request_object['header_name']
        df_headers = set(self.uploaded_file.columns.tolist())
        if user_header in df_headers:
            return user_header

        # Try changing casing if user_header not found
        casing_f = [lambda x: x.upper(), lambda x: x.lower(), lambda x: x.title()]

        for cf in casing_f:
            cased_name_header = cf(user_header)
            if cased_name_header in df_headers:
                return cased_name_header

        self.status = "Unable to find header named: {} , in file".format(user_header)
        return False

    def parse_sheet_(self):
        """
        :return: column data from sheet
        """
        if self.valid_header:
            try:
                names_col = self.uploaded_file[self.valid_header].values.tolist()
                self.status = True
                return names_col
            except KeyError:
                self.status = 'Unable to find header named: {}, in file'.format(self.valid_header)
                return False

    def file_data(self):
        if self.data:
            return self.data
        else:
            return False


