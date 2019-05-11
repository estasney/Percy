from app_folder.site_config import FConfig

fconfig = FConfig()


def get_autocomplete(dataset, words=fconfig.AUTOCOMPLETE_TOKENS, skills=fconfig.AUTOCOMPLETE_SKILLS):

    if dataset == 'words':
        with open(words, 'r', encoding="utf-8") as tfile:
            d1 = tfile.read().splitlines()
            return d1

    else:
        with open(skills, 'r', encoding="utf-8") as tfile:
            d2 = tfile.read().splitlines()
            return d2





