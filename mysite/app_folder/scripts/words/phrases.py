from collections import Counter
import os
from gensim.models.phrases import Phrases, Phraser
from mysite.app_folder.scripts.utils.streaming import DocStreamer
import easygui
#
# EXCLUDED = r"/home/eric/PycharmProjects/Percy/mysite/app_folder/scripts/tmp/phrases/excluded.txt"
# INCLUDED = r"/home/eric/PycharmProjects/Percy/mysite/app_folder/scripts/tmp/phrases/included.txt"
# PHRASE_DUMP = r"/home/eric/PycharmProjects/Percy/mysite/app_folder/scripts/tmp/phrases/phrase_dump.txt"

EXCLUDED = r"C:\Users\estasney\PycharmProjects\webwork\mysite\app_folder\scripts\tmp\phrases\excluded.txt"
INCLUDED = r"C:\Users\estasney\PycharmProjects\webwork\mysite\app_folder\scripts\tmp\phrases\included.txt"
PHRASE_DUMP = r"C:\Users\estasney\PycharmProjects\webwork\mysite\app_folder\scripts\tmp\phrases\phrase_dump.txt"


def detect_phrases(tmp_dir_sent, tmp_dir_phrases, common_words, min_count, threshold, max_layers=3):
    streamer = DocStreamer(tmp_dir_sent)
    phrases = Phrases(streamer, common_terms=common_words, min_count=min_count, threshold=threshold)

    starting_layer, next_layer = 1, 2

    while next_layer <= max_layers:
        phrases, found_new = train_layer(streamer, phrases, starting_layer, next_layer)
        if not found_new:
            break
        else:
            starting_layer += 1
            next_layer += 1

    phrases.save(os.path.join(tmp_dir_phrases, "phrases.model"))
    phrase_counts = Counter(phrases.export_phrases(streamer))
    phrase_counts = list(phrase_counts.items())
    decoded_phrase_counts = []
    for word_pmi, count in phrase_counts:
        word, pmi = word_pmi
        word = word.decode()
        decoded_phrase_counts.append((word, pmi, count))
    decoded_phrase_counts.sort(key=lambda x: x[2], reverse=True)
    del phrase_counts
    with open(os.path.join(tmp_dir_phrases, 'phrase_dump.txt'), 'w+', encoding='utf-8') as tfile:
        for phrase, pmi, count in decoded_phrase_counts:
            tfile.write("{}, {}, {}".format(phrase.replace(" ", "_"), pmi, count))
            tfile.write("\n")


def train_layer(text, model, starting_layer=1, ending_layer=2):
    # layer indicates number of times to transform text
    """
    layer = 2
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


class MyPhraser(Phraser):

    def __init__(self, phrase_path, excluded_phrases):
        phrase_model = Phrases.load(phrase_path)
        self.excluded_phrases = excluded_phrases
        super().__init__(phrase_model)

    def __getitem__(self, item):

        transformed = super().__getitem__(item)
        filtered_transformed = []
        for token in transformed:
            if "_" not in token:
                filtered_transformed.append(token)
                continue
            if token in self.excluded_phrases:
                tokens = token.split("_")
                filtered_transformed.extend(tokens)

        return filtered_transformed
