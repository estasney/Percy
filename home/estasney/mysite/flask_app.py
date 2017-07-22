
# A very simple Flask Hello World app for you to get started with...

from flask import Flask, render_template, request
from gensim.models import Doc2Vec

model = Doc2Vec.load('/home/estasney/mysite/mymodel.model')
#model = Doc2Vec.load('mymodel.model')

app = Flask(__name__)

@app.route('/')
def hello_world():
    return render_template('main_page.html')

@app.route('/', methods=['POST'])
# https://stackoverflow.com/questions/19794695/flask-python-buttons
def my_form_post():
    if request.form['button'] == 'query':  # similar words search
        user_query = request.form['query'].lower()
        try:
            result = dict(model.similar_by_word(user_query))
            return render_template('results.html', result=result, success='True', title_h2='Word Similarity Score', title_th='Similarity Score')
        except KeyError as error:
            error_message = str(error)
            offending_term = error_message.split("'")[1]
            result = offending_term.title()
            return render_template('results.html', result=result, success='False')
    elif request.form['button'] == 'math':
        pos_words = [request.form['word1'].lower(), request.form['word2'].lower()]
        neg_words = list(request.form['word3'].lower())
        if neg_words != '':
            try:
                result = dict(model.most_similar(positive=pos_words))
                print(result)
                return render_template('results.html', result=result, success='True', title_h2='Word Equation Results', title_th='Score')
            except KeyError as error:
                error_message = str(error)
                print(error_message)
                offending_term = error_message.split("'")[1]
                result = offending_term.title()
                return render_template('results.html', result=result, success='False')
        else:
            try:
                result = dict(model.most_similar(positive=pos_words, negative=neg_words))
                print(result)
                return render_template('results.html', result=result, success='True', title_h2='Word Equation Results', title_th='Score')
            except KeyError as error:
                error_message = str(error)
                print(error_message)
                offending_term = error_message.split("'")[1]
                result = offending_term.title()
                return render_template('results.html', result=result, success='False')



# Launch server locally

"""
if __name__ == '__main__':
    app.run()
"""