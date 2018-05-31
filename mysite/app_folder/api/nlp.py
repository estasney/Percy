import re
import abc
from app_folder.main.neural_tools import word_sims
from nltk import word_tokenize, pos_tag
from app_folder import model

class IntentParser(object):

    def __init__(self, intent_mappers):
        self.intent_mappers = intent_mappers

    def __contains__(self, item):
        if any([lambda x: x, [im.run_search_(item) for im in self.intent_mappers]]):
            return True
        else:
            return False

class SynonymParser(object):

    """
    Checks message and returns true if message indicates checking for synonyms

    Preprocesses string:
        - Returning string found after "synonyms" or variant
        - Tokening above string
        - POS Tagging and Filtering by NN*

    Gather synonyms
        - Calls word_sims() from neural_tools.py

    Generate reply
        - Generates reply to query

    """

    def __init__(self):
        pass

    @property
    def search_method_(self):
        # matches "synonyms" are approximate spelling
        return r"(syn[a-z]+?ms?)"

    @property
    def default_pos_(self):
        return ['NN', 'JJ']

    @property
    def search_method(self):
        return re.compile(self.search_method_, flags=re.IGNORECASE)

    def preprocess_string(self, text):
        # Splitting query to text following search_method
        word_matched = self.search_method.search(text).group()  # "Synonym" or variant
        text_list = self.search_method.split(text) # Before, "Synonym", After
        text_pos = text_list.index(word_matched) + 1  # Position of After in list
        entities = text_list[text_pos] # After
        entities = pos_tag(word_tokenize(entities))  # Tokenize and POS Tag

        def filter_tag(token_tag, pos_filter=self.default_pos_):
            tag = token_tag[1]
            if any([tag.startswith(pf) for pf in pos_filter]):
                    return True
            return False

        entities = list(filter(filter_tag, entities))  # Filter by POS
        entities = [word for word, tag in entities]  # Remove tag
        return entities

    def run_query(self, entities, topn=5):
        if isinstance(entities, str):
            entities = [entities]

        results = []
        for e in entities:
            sims = word_sims(e, topn=topn)













    def run_search_(self, text):
        return super().run_search_(text)





def parse_intent(message_body):



def make_response(message):
    """
    message :
        created: datetime or str(if conversion failed)
        person_email:
        person_id:
        person_fname:
        person_lname:
        person_displayname:
        person_nname: person nick-name

    :return:
    """