from app_folder.tools.decorators import memoized
from app_folder.percy_models import Name

from app_folder.site_config import FConfig
from app_folder.tools.diversity_tools_.namesearch import NameSearch

fconfig = FConfig()


def get_name_count(name):
    name = name.lower()
    name_kw = Name.query.get(name)
    if not name_kw:
        return None
    else:
        male, female = name_kw.male_count, name_kw.female_count
        return {'n_male': male, 'n_female': female}


class AppNameSearch(NameSearch):

    def __init__(self, prior=None, flashtext_fp=fconfig.NAMESEARCH_V2, beta_interval=0.95, sample_confidence=0.95,
                 beta_params_path=fconfig.BETA_PARAMS):
        super().__init__(prior, flashtext_fp, beta_interval, sample_confidence, beta_params_path)

        @memoized
        def get_interval(self, n_male, n_female):
            return super().get_interval(n_male, n_female)
