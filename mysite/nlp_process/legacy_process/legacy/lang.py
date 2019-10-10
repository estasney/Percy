import multiprocessing
import numpy as np
import pandas as pd
import os
from langdetect import detect


def _apply_df(args):
    df, func, num, kwargs = args
    return num, df.apply(func, **kwargs)


def apply_by_multiprocessing(df, func, **kwargs):
    workers = kwargs.pop('workers')
    pool = multiprocessing.Pool(processes=workers)
    result = pool.map(_apply_df, [(d, func, i, kwargs) for i, d in enumerate(np.array_split(df, workers))])
    pool.close()
    result = sorted(result, key=lambda x: x[0])
    return pd.concat([i[1] for i in result])


def lang_detect(x):
    if x['lang'] == -1:
        try:
            return detect(x['summary'])
        except:
            return ""
    else:
        return x['lang']


def lookup_language_detection(df, lang_file):

    if not os.path.isfile(lang_file):
        print("No lang file")
        df['lang'] = -1
        return df

    df_lang = pd.read_json(lang_file)

    # If detected previously, will have:
        # en
        # ""

    # If not, will have:
        # NaN

    df1 = df.merge(df_lang, on='member_id', how='left')
    df1['lang'].fillna(-1, inplace=True)
    print(df1['lang'].value_counts())
    return df1


def store_language_detection(df, lang_file):

    with open(lang_file, 'w+') as json_file:
        df[['member_id', 'lang']].to_json(json_file, orient='records')

