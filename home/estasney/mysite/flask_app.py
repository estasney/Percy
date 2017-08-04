from flask import Flask, render_template, request
from gensim.models import Doc2Vec
from gensim.summarization import keywords as KW
model = Doc2Vec.load(r"C:\Users\erics_qp7a9\PycharmProjects\percy1\Percy\home\estasney\mysite\mymodel.model")



app = Flask(__name__)

@app.route('/')
def hello_world():
    return render_template('home_page.html')

@app.route('/keywords')
def keywords():
    return render_template('keywords.html')

@app.route('/related')
def related():
    return render_template('related.html')

@app.route('/thisplusthat')
def thisplusthat():
    return render_template('thisplusthat.html')

@app.route('/', methods=['POST'])
def my_sims():
    if request.form['button'] == 'query':  # similar words search
        user_query = request.form['query'].lower()
        try:
            result = dict(model.similar_by_word(user_query))
            return render_template('related.html', result=result, success='True', title_h2='Word Similarity Score', title_th='Similarity Score')
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
            return render_template('thisplusthat.html', result=result, success='True', user_equation=user_equation)
        except KeyError as error:
            error_message = str(error)
            offending_term = error_message.split("'")[1]
            result = offending_term.title()
            return render_template('thisplusthat.html', result=result, success='False')
    elif request.form['button'] == 'keywords':
        try:
            raw_text = request.form['raw_text']
            raw_text = ' '.join([word for word in raw_text.split()])
            user_keywords = KW(raw_text).splitlines()
            return render_template('keywords.html', keywords=user_keywords, success='True')
        except:
            return render_template('keywords.html', success='False')







if __name__ == '__main__':
    app.run()
