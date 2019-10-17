import re
from collections import Counter
from collections import namedtuple
from datetime import datetime


from gensim.models.phrases import Phraser, Phrases
from pampy import match, _, TAIL

from mysite.nlp_process.process_config import ProcessConfig
from mysite.nlp_process.spacy_process.utils import time_this
from mysite.nlp_process.spacy_process.streaming import get_sub_docs, SpacyTokenFilter, SpacyReader

Pattern = namedtuple('Pattern', 'pattern action default')


def make_pattern(pattern, action=False, default=True):
    return Pattern(pattern, action, default)


f1 = make_pattern(["I", _])  # anything starting with i
f2 = make_pattern(["--", _])  # --_--

# 10_years, 3+_years
f3 = make_pattern([re.compile(r"([0-9+]{1,2}\+?)"),
                   re.compile(r"(years?|months?|days?)")])

# 15_percent 15+_percent, 55_%
f4 = make_pattern([re.compile(r"([0-9]{1,}\+?)"),
                   re.compile(r"(%)|(percent)|(\+)"),
                   TAIL])

phrase_patterns = [f1, f2, f3, f4]

config = ProcessConfig()


def filter_phrases(phrase_line, patterns=phrase_patterns):
    temp_phrase = phrase_line[0].split("_")
    for pattern in patterns:
        keep_it = match(temp_phrase, pattern.pattern, pattern.action, default=pattern.default)
        if not keep_it:
            return False
    return True


@time_this
def detect_phrases(input_dir, phrase_model_fp, phrase_dump_fp, common_words, min_count, threshold, token_key,
                   max_layers=2):
    """
    max_layers
        1 - bigrams
        2 - trigrams, etc
    """

    streamer = SpacyReader(folder=input_dir, data_key=get_sub_docs, token_key=token_key)

    phrases = Phrases(streamer, common_terms=common_words, min_count=min_count, threshold=threshold)

    starting_layer, next_layer = 1, 2

    while next_layer <= max_layers:
        start_time = datetime.now()
        phrases, found_new = train_layer(text=streamer, model=phrases, starting_layer=starting_layer,
                                         ending_layer=next_layer)
        end_time = datetime.now()
        elapsed = end_time - start_time
        print("Finished layer {} in {}".format(starting_layer, elapsed))
        if not found_new:
            print("No new phrases found at layer {}".format(next_layer))
            break
        else:
            print("New phrases detected at layer {}".format(next_layer))
            starting_layer += 1
            next_layer += 1

    print("Finished training layers")

    phrases.save(phrase_model_fp)

    print("Exporting Phrase Counts")
    start_time = datetime.now()
    phrase_counts = Counter()
    current_layer = 0
    while current_layer <= max_layers:
        layer_start_time = datetime.now()
        ngrams_stream = stream_ngrams(folder=input_dir, data_key=get_sub_docs, model=phrases,
                                      layers=current_layer, token_key=token_key)
        ngrams_export = phrases.export_phrases(ngrams_stream)
        phrase_counts.update(ngrams_export)
        print("Finished export of layer {} in {}".format(current_layer, (datetime.now() - layer_start_time)))
        current_layer += 1

    print("Finished Exporting Phrase Counts after {}".format(datetime.now() - start_time))

    phrase_counts = list(phrase_counts.items())
    decoded_phrase_counts = []
    for word_pmi, count in phrase_counts:
        word, pmi = word_pmi
        word = word.decode()
        decoded_phrase_counts.append((word, pmi, count))
    decoded_phrase_counts.sort(key=lambda x: x[2], reverse=True)
    del phrase_counts
    with open(phrase_dump_fp, 'w+', encoding='utf-8') as tfile:
        for phrase, pmi, count in decoded_phrase_counts:
            tfile.write("{}, {}, {}".format(phrase.replace(" ", "_"), pmi, count))
            tfile.write("\n")


def stream_ngrams(folder, data_key, model, token_key, layers=1):
    reader = SpacyReader(folder=folder, data_key=data_key, token_key=token_key)

    def phrase_once(doc, model):
        return model[doc]

    def phrase_many(doc, model, ntimes):
        for i in range(ntimes):
            doc = phrase_once(doc, model)
        return doc

    for sentence in reader:
        if sentence:
            doc = phrase_many(sentence, model, layers)
            yield doc


def train_layer(text, model, starting_layer=1, ending_layer=2):
    # layer indicates number of times to transform text
    """
    starting_layer = 1
        phrase_model[doc] ==> Bigrams
    ending_layer = 2
        phrase_model[phrase_model[doc]] ==> Trigrams
    """

    # add the vocab

    def phrase_once(doc, model):
        return model[doc]

    def phrase_many(doc, model, ntimes):
        for i in range(ntimes):
            doc = phrase_once(doc, model)
        return doc

    def stream_phrase(text, model, ntimes):
        for doc in text:
            doc = phrase_many(doc, model, ntimes)
            yield doc

    base_stream = stream_phrase(text, model, starting_layer)
    model.add_vocab(base_stream)

    base_stream = stream_phrase(text, model, starting_layer)
    new_stream = stream_phrase(text, model, ending_layer)

    for old, new in zip(base_stream, new_stream):
        if old != new:
            return model, True

    return model, False


def annotate_phrases(batch_size=100):
    """
    open the phrase dump file, pull the top 100
    open excluded and included. Remove any in those files
    """

    with open(config.PHRASE_EXCLUDED, "r", encoding="utf-8") as tfile:
        excluded = set(tfile.read().splitlines())

    with open(config.PHRASE_INCLUDED, "r", encoding="utf-8") as tfile:
        included = set(tfile.read().splitlines())

    with open(config.PHRASE_DUMP, "r", encoding="utf-8") as tfile:
        pending = tfile.read().splitlines()
        pending = [x.split(", ") for x in pending]

    pending = [phrase_line for phrase_line in pending if
               phrase_line[0] not in excluded and phrase_line[0] not in included][:batch_size]
    pending_choices = [phrase_line[0] for phrase_line in pending]
    marked_excluded = easygui.multchoicebox(msg="Mark Excluded", choices=pending_choices)
    if not marked_excluded:
        marked_excluded = []
    for marked in marked_excluded:
        excluded.add(marked)

    with open(config.PHRASE_EXCLUDED, "w+", encoding="utf-8") as tfile:
        for phrase in excluded:
            tfile.write(phrase)
            tfile.write("\n")

    not_marked = [phrase for phrase in pending_choices if phrase not in excluded]
    for phrase in not_marked:
        included.add(phrase)

    with open(config.PHRASE_INCLUDED, "w+", encoding="utf-8") as tfile:
        for phrase in included:
            tfile.write(phrase)
            tfile.write("\n")


def evaluate_filters():
    with open(config.PHRASE_EXCLUDED, "r", encoding="utf-8") as tfile:
        excluded = set(tfile.read().splitlines())

    with open(config.PHRASE_INCLUDED, "r", encoding="utf-8") as tfile:
        included = set(tfile.read().splitlines())

    my_phraser = MyPhraser()
    excluded_tokens = [x.split("_") for x in excluded]
    included_tokens = [x.split("_") for x in included]

    excluded_output = {"Fail": [], "Pass": []}
    for tokens in excluded_tokens:
        output = my_phraser[tokens]
        if any(["_" in x for x in output]):
            excluded_output["Fail"].append(output)
        else:
            excluded_output["Pass"].append(output)

    included_output = {"Fail": [], "Pass": []}
    for tokens in included_tokens:
        output = my_phraser[tokens]
        if not any(["_" in x for x in output]):
            included_output["Fail"].append(output)
        else:
            included_output["Pass"].append(output)

    print("Excluded Results".center(80, "="))
    print("")
    print("Fails".center(60, "*"))
    for f in excluded_output["Fail"]:
        print(f)
    print("")


class PhraseFilter(object):

    def __init__(self, patterns=phrase_patterns, phrase_delim="_"):
        self.patterns = patterns
        self.phrase_delim = phrase_delim

    def __contains__(self, item):
        temp_phrase = item.split(self.phrase_delim)
        for pattern in self.patterns:
            keep_it = match(temp_phrase, pattern.pattern, pattern.action, default=pattern.default)
            if not keep_it:
                return True
        return False


class MyPhraser(Phraser):

    def __init__(self, phrase_filter=PhraseFilter(), phrase_path=ProcessConfig().PHRASE_MODEL, iter=2):
        # phrase_model = Phrases.load(phrase_path)
        phrase_model = Phraser.load(phrase_path)
        self.phrase_filter = phrase_filter
        self.iter = iter
        super().__init__(phrase_model)

    def phrase_once(self, item):
        transformed = super().__getitem__(item)
        filtered_transformed = []
        for token in transformed:
            if "_" not in token:
                filtered_transformed.append(token)
                continue
            else:
                if token in self.phrase_filter:
                    tokens = token.split("_")
                    filtered_transformed.extend(tokens)
                else:
                    filtered_transformed.append(token)

        return filtered_transformed

    def __getitem__(self, item):
        for i in range(self.iter):
            item = self.phrase_once(item)
        return item


if __name__ == "__main__":
    # annotate_phrases()
    evaluate_filters()
