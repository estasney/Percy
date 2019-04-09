from pampy import match, _
from collections import namedtuple
from gensim.models.phrases import Phraser, Phrases
from process.process_config import ProcessConfig
from process.process.utils import SpacyReader
import re


Pattern = namedtuple('Pattern', 'pattern action default')


def make_pattern(pattern, action=False, default=True):
    return Pattern(pattern, action, default)


f1 = make_pattern(["I", _])  # anything starting with i
f2 = make_pattern(["--", _])  # --_--

# 10_years, 3+_years
f3 = make_pattern([re.compile(r"([0-9]{1,2}\+?)"),
                   re.compile(r"(years?)")])

# 15_percent 15+_percent, 55_%
f4 = make_pattern([re.compile(r"([0-9]{1,}\+?)"),
                   re.compile(r"(%)|(percent)")])


phrase_patterns = [f1, f2, f3, f4]


def filter_phrases(phrase_line, patterns=phrase_patterns):
    temp_phrase = phrase_line[0].split("_")
    for pattern in patterns:
        keep_it = match(temp_phrase, pattern.pattern, pattern.action, default=pattern.default)
        if not keep_it:
            return False
    return True


def detect_phrases(input_dir, phrase_dir, common_words, min_count, threshold, max_layers=2):

    """
    max_layers
        1 - bigrams
        2 - trigrams, etc
    """

    streamer = DocStreamer(input_dir)
    phrases = Phrases(streamer, common_terms=common_words, min_count=min_count, threshold=threshold)

    starting_layer, next_layer = 1, 2

    while next_layer <= max_layers:
        start_time = datetime.now()
        phrases, found_new = train_layer(streamer, phrases, starting_layer, next_layer)
        end_time = datetime.now()
        elasped = end_time - start_time
        print("Finished layer {}".format(elasped.seconds))
        if not found_new:
            print("No new phrases found at layer {}".format(next_layer))
            break
        else:
            print("New phrases detected at layer {}".format(next_layer))
            starting_layer += 1
            next_layer += 1

    phrases.save(os.path.join(phrase_dir, "phrases.model"))
    phrase_counts = Counter()

    print("Exporting Phrase Counts")

    current_layer = 0
    while current_layer <= max_layers:
        ngrams_stream = stream_ngrams(input_dir, phrases, current_layer)
        ngrams_export = phrases.export_phrases(ngrams_stream)
        phrase_counts.update(ngrams_export)
        current_layer += 1

    print("Finished Exporting Phrase Counts")

    phrase_counts = list(phrase_counts.items())
    decoded_phrase_counts = []
    for word_pmi, count in phrase_counts:
        word, pmi = word_pmi
        word = word.decode()
        decoded_phrase_counts.append((word, pmi, count))
    decoded_phrase_counts.sort(key=lambda x: x[2], reverse=True)
    del phrase_counts
    with open(PHRASE_DUMP, 'w+', encoding='utf-8') as tfile:
        for phrase, pmi, count in decoded_phrase_counts:
            tfile.write("{}, {}, {}".format(phrase.replace(" ", "_"), pmi, count))
            tfile.write("\n")


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

    with open(EXCLUDED, "r", encoding="utf-8") as tfile:
        excluded = set(tfile.read().splitlines())

    with open(INCLUDED, "r", encoding="utf-8") as tfile:
        included = set(tfile.read().splitlines())

    with open(PHRASE_DUMP, "r", encoding="utf-8") as tfile:
        pending = tfile.read().splitlines()
        pending = [x.split(", ") for x in pending]

    pending = [phrase_line for phrase_line in pending if phrase_line[0] not in excluded and phrase_line[0] not in included][:batch_size]
    pending_choices = [phrase_line[0] for phrase_line in pending]
    marked_excluded = easygui.multchoicebox(msg="Mark Excluded", choices=pending_choices)
    if not marked_excluded:
        marked_excluded = []
    for marked in marked_excluded:
        excluded.add(marked)

    with open(EXCLUDED, "w+", encoding="utf-8") as tfile:
        for phrase in excluded:
            tfile.write(phrase)
            tfile.write("\n")

    not_marked = [phrase for phrase in pending_choices if phrase not in excluded]
    for phrase in not_marked:
        included.add(phrase)

    with open(INCLUDED, "w+", encoding="utf-8") as tfile:
        for phrase in included:
            tfile.write(phrase)
            tfile.write("\n")



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
        phrase_model = Phrases.load(phrase_path)
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
