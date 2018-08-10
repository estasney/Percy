import re
from app_folder.main.neural_tools import word_sims
from app_folder.main.text_tools import parse_form_text
import nltk


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
    def intent(self):
        """
        Words to search for in query that indicate intent
        """
        return {'synonyms', 'synonym', 'similar', 'similarities'}

    @property
    def preamble_(self):
        return "Synonyms for {}"

    @property
    def grammar(self):
        return "GRAMMAR: {<IN><NN>*<VB>*<JJ>*}"


    @property
    def default_pos_(self):
        return ['NN', 'JJ', 'VB']

    def tag_match(self, word_tag):
        word, tag = word_tag
        filters = [tag.startswith(x) for x in self.default_pos_]
        if any(filters):
            return True
        else:
            return False

    def parse_intent(self, text):
        """
        Extracting structured data from a natural language query

        :param text:
        :return:
        """

        chunker = nltk.RegexpParser(self.grammar)
        tokens = parse_form_text(text)
        pos_tokens = nltk.pos_tag(tokens)

        tree = chunker.parse(pos_tokens)
        words = []

        for subtree in tree.subtrees():
            if subtree.label() == "GRAMMAR":
                matched_words = list(filter(self.tag_match, subtree.leaves()))
                words.append(matched_words)

        def filter_tag(token_tag, pos_filter=self.default_pos_):
            tag = token_tag[1]
            if any([tag.startswith(pf) for pf in pos_filter]):
                    return True
            return False

        entities = list(filter(filter_tag, words))  # Filter by POS
        entities = [word for word, tag in entities]  # Remove tag
        return entities

    def run_query(self, entities, topn=20):
        results = []
        for e in entities:
            sims_success, sim_scores = word_sims(e)
            if sims_success:
                sim_scores = sim_scores[:topn]
            else:
                sim_scores = []
            td = {'success': sims_success,
                  'entity': e,
                  'scores': sim_scores}
            results.append(td)

        return results

    def transform_to_data(self, text):
        entities = self.parse_intent(text)
        query_result = self.run_query(entities)
        return query_result

    def make_preamble_(self, entity, success=True):
        if success:
            return self.preamble_.format(entity)
        else:
            return "I dont know the word: {}.".format(entity)

    def convey_results_(self, result):
        words = [word for word, score in result]
        return ", ".join(words)

    def make_conveyable_(self, results):

        message = []

        for result in results:
            if result['success'] is True:
                preamble = self.make_preamble_(result['entity'])
                sims = self.convey_results_(result['scores'])
                message.append(preamble.format(sims))
            else:
                preamble = self.make_preamble_(result['entity'], success=False)
                message.append(preamble)

        return "\n".join(message)

    def answer_question_(self, text):
        query_result = self.transform_to_data(text)
        text_result = self.make_conveyable_(query_result)
        return text_result
