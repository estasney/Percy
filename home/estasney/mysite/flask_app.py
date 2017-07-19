
# A very simple Flask Hello World app for you to get started with...

from flask import Flask, render_template, request
from gensim.models import Doc2Vec

model = Doc2Vec.load('/home/estasney/mysite/mymodel.model')
# model = Doc2Vec.load('mymodel.model')

app = Flask(__name__)

@app.route('/')
def hello_world():
    return render_template('main_page.html')

@app.route('/', methods=['POST'])
def my_form_post():
    user_query = request.form['query'].lower()
    try:
        result = dict(model.similar_by_word(user_query))
        return render_template('results.html', result=result, success='True')
    except KeyError as error:
        error_message = str(error)
        offending_term = error_message.split("'")[1]
        result = offending_term.title()
        return render_template('results.html', result=result, success='False')

# Launch server locally
"""
if __name__ == '__main__':
    app.run()
"""