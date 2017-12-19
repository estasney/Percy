from operator import itemgetter
from collections import namedtuple



# user_form = self.request_object
# # TODO Ad
# global_name_mode = user_form.get('use_global_names', False)
#
# diversity_scored = retrieve_names_bulk(names_col, global_name_mode)
# male_count = str(diversity_scored['male'])
# female_count = str(diversity_scored['female'])
# unknown_count = str(diversity_scored['unknown'])
# ai_names = diversity_scored['ai_names']
#
# return render_template('diversity_score.html', success='True', male_count=male_count,
#                        female_count=female_count, unknown_count=unknown_count, ai_names=ai_names)
#
# # Will be passed query data

# Start with list of names
# User chooses
    # A. Include Global Dict?
    # B. Exclude Machine Learning
# Returns
    # Database Lookups
        # SSA Lookup
            # M to F
        # Global Dict
            # M, F, Ambiguous
    # If exclude ML
        # Do stats

class Genderize(object):

    GenderResults = namedtuple('GenderResults', 'query source result')

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

    def run_query(self, query):
        results = []
        data_results = self.data_lookup_(query)
        if data_results:
            results.append(data_results)
        model_results = self.ask_model_(query)
        results.append(model_results)
        return results




















# def retrieve_names_bulk(name_list, name_dict, global_dict=None, infer_gender=True):
#     male_count = 0
#     female_count = 0
#     unknown_count = 0
#     amb_count = 0 # Ambiguous count
#     ai_count = 0
#     unknown_holder = []
#     ai_dict = {}
#
#     for name in name_list:
#         if name not in name_dict:
#             unknown_holder.append(name)
#             continue
#         gender_lookup = retrieve_name(name, name_dict)
#         top_gender = parse_ssa_lookup(gender_lookup)
#         if top_gender == 'M':
#             male_count += 1
#         elif top_gender == 'F':
#             female_count += 1
#
#     if global_dict and unknown_holder:
#         for name in unknown_holder:
#             if name not in global_dict:
#                 continue
#             gender_lookup = retrieve_name(name, global_dict)
#             top_gender = gender_lookup
#             if top_gender == 'M':
#                 male_count += 1
#             elif gender_lookup == 'F':
#                 female_count += 1
#             else:
#                 amb_count += 1
#             unknown_holder.pop(unknown_holder.index(name))
#
#     if infer_gender is False:
#         diversity_score_dict = {'male': male_count, 'female': female_count, 'unknown': len(unknown_holder),
#                                 'amb_count': amb_count, 'ai_names': False, 'ai_count': 0}
#         return diversity_score_dict
#
#     for name in unknown_holder:
#         inferred_gender = guess_name(name).lower()
#         if inferred_gender == 'male':
#             male_count += 1
#             ai_dict[name.title()] = 'Male'
#         elif inferred_gender == 'female':
#             female_count = female_count + 1
#             ai_dict[name.title()] = 'Female'
#         ai_count += 1
#
#     diversity_score_dict = {'male': male_count, 'female': female_count, 'unknown': 0, 'amb_count': 0,
#                             'ai_names':ai_dict, 'ai_count': ai_count}
#     return diversity_score_dict
#
#
#
# def guess_name(name):
#     inferred_gender = tree_model.classify(gender_features(name)).title()
#     return inferred_gender
#
# user_query_name = request.form['infer_name']
#         inferred_gender = tree_model.classify(gender_features(user_query_name)).title()
#         gender_lookup = retrieve_name(user_query_name, name_dict)[1]  # Selecting the message
#         return render_template('infer.html', user_query=user_query_name, success='True', gender_guess=inferred_gender,
#                                lookup_message=gender_lookup)