from app_folder.site_config import FConfig


def get_autocomplete(dataset, words=FConfig.dictionary_autocomplete, skills=FConfig.dictionary_skills_autocomplete,
                     names=FConfig.names_autocomplete):

    if dataset == 'words':
        with open(words, 'r') as tfile:
            d1 = tfile.read().splitlines()
            return d1

    else:
        with open(skills, 'r') as tfile:
            d2 = tfile.read().splitlines()
            return d2





