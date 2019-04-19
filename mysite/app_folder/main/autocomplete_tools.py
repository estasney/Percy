from app_folder.site_config import FConfig

fconfig = FConfig()


def get_autocomplete(dataset, words=fconfig.AUTOCOMPLETE_TOKENS, skills=fconfig.AUTOCOMPLETE_SKILLS):

    if dataset == 'words':
        with open(words, 'r') as tfile:
            d1 = tfile.read().splitlines()
            return d1

    else:
        with open(skills, 'r') as tfile:
            d2 = tfile.read().splitlines()
            return d2





