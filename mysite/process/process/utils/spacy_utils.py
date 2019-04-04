from datetime import datetime
import numpy as np
import multiprocessing
from functools import partial
from collections import namedtuple
import json

Pattern = namedtuple('Pattern', 'pattern action default')


EXCLUDED_TAGS = ['is_punct', 'is_left_punct', 'is_right_punct', 'is_space', 'is_bracket',
                 'is_quote', 'is_currency', 'like_url', 'like_email', 'is_stop']

REQUIRED_TAGS = ['is_alpha', 'is_digit']


def filter_tags(doc, excluded=EXCLUDED_TAGS, included=REQUIRED_TAGS):
    keeps = []
    for token in doc:
        if not any([token.get(e, False) for e in excluded]):
            if any([token.get(r, True) for r in included]):
                keeps.append(token)
    return keeps


def stream_docs(files, data_key):
    for f in files:
        with open(f, 'r') as json_file:
            doc = json.load(json_file)
        if data_key:
            doc_text = doc[data_key]
        else:
            doc_text = doc
        yield f, doc_text


def process_phrase_tokens(target_files, phraser, n_jobs=2):

    file_subsets = np.array_split(target_files, n_jobs)
    target_function = partial(process_phrase_tokens_worker, phraser=phraser)
    start_time = datetime.now()
    with multiprocessing.Pool(processes=n_jobs) as pool:
        pool.map(target_function, file_subsets)
    elapsed = (datetime.now() - start_time)
    print("Completed phrasing in {} ".format(elapsed))


def process_phrase_tokens_worker(file_subset, phraser):
    doc_stream = stream_docs(file_subset, data_key=None)
    for fp, doc in doc_stream:
        try:
            doc['phrases'] = phrase_tokens(doc['tokens'], phraser)
            with open(fp, 'w+') as json_file:
                    json.dump(doc, json_file, indent=4)
        except Exception as e:
            print("Bad file : {}".format(fp))
            print(e)


def phrase_tokens(tokens, phraser):

    """
    Accept a list of token data
    Acts as facade to phraser by presenting only strings
    Compares result with original
    Merges phrased tokens

    :param tokens:
    :param phraser:
    :return:
    """
    token_output = []
    index = 0

    # filter the tokens first
    original_tokens = filter_tags(tokens)

    if not original_tokens:
        return []

    # pass just the strings to phraser and get the result
    phrased_tokens = phraser[[x['lemma'] for x in original_tokens]]

    if phrased_tokens == [[x['lemma'] for x in original_tokens]]:
        return original_tokens

    # iterate through phrased tokens, looking for phrased values
    for i, token in enumerate(phrased_tokens):
        if "_" not in token:  # keep the data, unchanged
            try:
                output = original_tokens[index]
            except IndexError:
                continue
            token_output.append(output)
            index += 1
            continue
        else:
            # we now need to grab multiple tokens
            phrased_len = len(token.split("_"))
            output = original_tokens[index:(index+phrased_len)]
            # update the index so the respective lists are aligned
            index += phrased_len
            # make a minimal shim for the phrase
            output_tags_ = [getattr(t, 'tag', "") for t in output]  # keep this if needed
            # make a 'custom' tag to show a phrase
            output_tag = "PHRASE"
            output_data = {'lemma': token, 'tag_': output_tags_, 'tag': output_tag}
            token_output.append(output_data)

    return token_output


def get_filtered_text(doc, excluded=EXCLUDED_TAGS):
    keeps = filter_tags(doc, excluded)
    return [t['lemma'] for t in keeps]