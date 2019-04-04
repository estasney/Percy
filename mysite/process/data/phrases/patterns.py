from pampy import match, _, HEAD, TAIL
from collections import namedtuple
from cytoolz import groupby
import re

# anything starting with i

Pattern = namedtuple('Pattern', 'pattern action default')

def make_pattern(pattern, action=False, default=True):
    return Pattern(pattern, action, default)

f1 = make_pattern(["I", _])
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

with open(r"C:\Users\estasney\PycharmProjects\webwork\mysite\app_folder\scripts\tmp\phrases\phrase_dump.txt", "r", encoding='utf-8') as text_file:
    phrase_lines = text_file.read().splitlines()
    phrase_lines = [x.split(", ") for x in phrase_lines]

with open(r"C:\Users\estasney\PycharmProjects\webwork\mysite\app_folder\scripts\tmp\phrases\included.txt", "r", encoding="utf-8") as text_file:
    included = set(text_file.read().splitlines())

with open(r"C:\Users\estasney\PycharmProjects\webwork\mysite\app_folder\scripts\tmp\phrases\excluded.txt", "r", encoding="utf-8") as text_file:
    excluded = set(text_file.read().splitlines())

phrase_lines = [line for line in phrase_lines if line[0] not in included and line[0] not in excluded]

filtered_phrases = groupby(filter_phrases, phrase_lines)
new_excluded = filtered_phrases[False]
new_excluded = set([x[0] for x in new_excluded])
excluded.update(new_excluded)

new_included = filtered_phrases[True]  # put these back into queue
new_included.sort(key=lambda x: x[2], reverse=True)

with open(r"C:\Users\estasney\PycharmProjects\webwork\mysite\app_folder\scripts\tmp\phrases\excluded.txt", "w+", encoding="utf-8") as text_file:
    for phrase in excluded:
        text_file.write(phrase)
        text_file.write("\n")

with open(r"C:\Users\estasney\PycharmProjects\webwork\mysite\app_folder\scripts\tmp\phrases\phrase_dump.txt", "w+", encoding="utf-8") as text_file:
    for phrase in new_included:
        phrase = ", ".join(phrase)
        text_file.write(phrase)
        text_file.write("\n")
