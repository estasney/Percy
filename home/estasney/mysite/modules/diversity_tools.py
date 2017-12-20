from operator import itemgetter
from collections import namedtuple
import pickle

try:
    from home.estasney.mysite.config import local_config as config
except ImportError:
    from home.estasney.mysite.config import web_config as config

# Load Tree Classifier

f = open(config.tree, "rb")

tree_model = pickle.load(f)
f.close()

# Load Name Dictionary
f = open(config.name_dict, "rb")
name_dict = pickle.load(f)
f.close()

# Load Global Name Dictionary
f = open(config.global_name_dict, "rb")
global_name_dict = pickle.load(f)
f.close()





def infer_one(request):
    user_form = request.form
    use_global = user_form.get('global_names', False)
    if use_global == 'on':
        use_global = True

    # resources available to genderize
    if use_global:
        resources = {'data-SSA': name_dict, 'data-Global': global_name_dict, 'model': tree_model}
    else:
        resources = {'data-SSA': name_dict, 'model': tree_model}

    genderizer = Genderize(**resources)
    results = genderizer.run_query(request.form['infer-name'])
    return results

def infer_stats(results, type=None):
    if type:
        if type == 'Cumul': # Get overall M, F, U counts
            # Prefer data over model result
            cumul = {'M': 0, 'F': 0, 'U': 0}
            for v in results.values():
                data = [dv for dv in v if 'data' in dv.source]
                if data:
                    if len(data) > 1:
                        data = [dv for dv in v if 'SSA' in dv.source]
                    result = data[0].result
                    old_score = cumul[result]
                    cumul[result] = old_score + 1
                    continue
                model = [dv for dv in v if 'model' in dv.source]
                result = model[0].result
                old_score = cumul[result]
                cumul[result] = old_score + 1
            return cumul
        elif type == 'Data':  # Get overall, M,F,U, Unk counts
            # Excluding models
            # Prefer data over model result
            cumul = {'M': 0, 'F': 0, 'U': 0, 'Unk': 0}
            for v in results.values():
                data = [dv for dv in v if 'data' in dv.source]
                if data:
                    if len(data) > 1:
                        data = [dv for dv in v if 'SSA' in dv.source]
                    result = data[0].result
                    old_score = cumul[result]
                    cumul[result] = old_score + 1
                    continue
                else:
                    old_score = cumul['Unk']
                    cumul['Unk'] = old_score + 1
            return cumul
        elif type == 'DSources':
            dsources = {}
            for v in results.values():
                data = [dv for dv in v if 'data' in dv.source]
                for dv in data:
                    current_score = dsources.get(dv.source, 0)
                    dsources[dv.source] = current_score + 1
            return dsources


# TODO Exclude ML Option
def infer_many(names_list, use_global):
    if use_global:
        resources = {'data-SSA': name_dict, 'data-Global': global_name_dict, 'model': tree_model}
    else:
        resources = {'data-SSA': name_dict, 'model': tree_model}

    genderizer = Genderize(**resources)

    name_results = {}
    for i, first_name in enumerate(names_list):
        results, _ = genderizer.run_query(first_name)
        name_results[i] = results

    cumul_count = infer_stats(name_results, type='Cumul')
    data_only = infer_stats(name_results, type='Data')
    data_sources = infer_stats(name_results, type='DSources')

    return {'Cumulative': cumul_count, 'Data_Only': data_only, 'Data_Sources': data_sources}

class Genderize(object):

    GenderResults = namedtuple('GenderResults', 'query source result')
    default_resources = {'data-SSA': name_dict, 'data-Global': global_name_dict, 'model': tree_model}

    def __init__(self, **resources):
        """
        :param resources: Provide resources that class may access to determine gender.
            :keyword - in form (data) - (int) : for database, (model) - (int) : for model
            :value - object
        """
        self.datas = {}
        self.models = {}
        if resources:
            for k, v in resources.items():
                if "data" in k:
                    self.datas[k] = v
                elif "model" in k:
                    self.models[k] = v
        else:
            for k, v in self.default_resources.items():
                if "data" in k:
                    self.datas[k] = v
                elif "model" in k:
                    self.models[k] = v

    def gender_features_(self, query):
        name = query.lower()
        features = {}
        features['first_two'] = name[:2]
        features['last_letter'] = name[-1]
        features['last_letter_vowel'] = self.vowel_test_(name[-1])
        features['last_two'] = name[-2:]
        return features

    def vowel_test_(self, letter):
        vowels = ["a", "e", "i", "o", "u", "y"]
        if letter in vowels:
            return "Yes"
        else:
            return "No"

    def parse_result_(self, result):
        if isinstance(result, dict): # SSA Format {'M': int, 'F': int}
            # ensure not equal
            if list(result.values())[0] == list(result.values())[1]:
                return 'U' # U for ambiguous
            #  return the top scoring gender
            return sorted(result.items(), key=itemgetter(1), reverse=True)[0][0]
        if isinstance(result, str): # Global Names Format or Classifier
            if len(result) == 1:
                return result.upper()
            else:
                return result[0].upper()

    def format_result_(self, query, source, result):
        res = self.GenderResults(query=query, source=source, result=result)
        return res

    def data_lookup_(self, query):
        query_l = query.lower()

        if self.datas:
            for data_name, data_file in self.datas.items():
                if query_l in data_file:
                    parsed_finding = self.parse_result_(data_file[query_l])
                    format_finding = self.format_result_(query, data_name, parsed_finding)
                    return format_finding
        else:
            return False

    def ask_model_(self, query):
        query_l = query.lower()
        if self.models:
            query_features = self.gender_features_(query_l)
            for model_name, model_obj in self.models.items():
                guess = model_obj.classify(query_features)
                parsed_guess = self.parse_result_(guess)
                format_finding = self.format_result_(query, model_name, parsed_guess)
                return format_finding
        else:
            return False

    def list_datas_(self, prettify=True):
        data_list = []
        for k, v in self.datas.items():
            if prettify:
                if k == 'data-SSA':
                    new_k = "Social Security Database"
                elif k == 'data-Global':
                    new_k = "Global Names Database"
                else:
                    new_k = k
                data_list.append(new_k)
            else:
                data_list.append(k)
        if prettify:
            if len(data_list) == 1:
                return data_list[0]
            else:
                return ' and '.join(data_list)
        return data_list

    def run_query(self, query):
        results = []
        data_results = self.data_lookup_(query)
        if data_results:
            results.append(data_results)
        model_results = self.ask_model_(query)
        results.append(model_results)
        data_sources = self.list_datas_()
        return results, data_sources



















