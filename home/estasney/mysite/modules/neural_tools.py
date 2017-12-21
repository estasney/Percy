from gensim.models import Doc2Vec
from home.estasney.mysite.modules.Utils import prettify_dict

try:
    from home.estasney.mysite.config import local_config as config
except ImportError:
    from home.estasney.mysite.config import web_config as config

model = Doc2Vec.load(config.model)

def word_sims(user_query, prettify=True):
    try:
        result = dict(model.similar_by_word(user_query.lower()))
    except KeyError as error:
        return False, error
    if prettify:
        result = prettify_dict(result)
    return True, result


def word_math(request):
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

        return {'result': prettify_dict(result), 'success': True, 'user_equation':user_equation, 'word_one':word_one.strip(), 'word_two':word_two.strip(),
                'word_three': word_three.strip()}
    except KeyError as error:
        error_message = str(error)
        offending_term = error_message.split("'")[1]
        result = offending_term.title()
        return {'result': result, 'success': False}
