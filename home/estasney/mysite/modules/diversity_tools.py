from operator import itemgetter
import queue


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

class DataFetcher(object):

    def __init__(self, query, *data_file):
        self.query = self.format_query_(query)
        self.data_file = [d for d in data_file]
        self.query_results = {'male': 0, 'female': 0, 'ambiguous': 0, 'unknown': []}

    def format_query_(self, query):
        if isinstance(query, str):
            query = [query]
        elif isinstance(query, list) is False:
            raise ValueError
        fl = [q.lower() for q in query]
        query_q = queue.Queue()
        for qq in fl:
            query_q.put_nowait(qq)
        return query_q


    def query_name_(self, name, data_file_index=0):
        if name not in self.data_file[data_file_index]:
            return False
        else:
            return self.data_file[data_file_index][name]

    def parse_value_(self, value):
        if isinstance(value, dict): # SSA Database
            sorted_data = sorted(value, key=itemgetter(1), reverse=True)
            top_gender = sorted_data[0][0]
            return top_gender
        if isinstance(value, str): # Global Name Database
            return value

    def run_query(self):
        for q in self.query:
            self.query_name_(q)

def worker():
    while True:
        item = q.get()
        if item is None:
            break
        do_work(item)
        q.task_done()

q = queue.Queue()
threads = []
for i in range(num_worker_threads):
    t = threading.Thread(target=worker)
    t.start()
    threads.append(t)

for item in source():
    q.put(item)

# block until all tasks are done
q.join()

# stop workers
for i in range(num_worker_threads):
    q.put(None)
for t in threads:
    t.join()










def gender_features(name):
    name = name.lower()
    features = {}
    features['first_two'] = name[:2]
    features['last_letter'] = name[-1]
    features['last_letter_vowel'] = vowel_test(name[-1])
    features['last_two'] = name[-2:]
    return features


def vowel_test(letter):
    vowels = ["a", "e", "i", "o", "u", "y"]
    if letter in vowels:
        return "Yes"
    else:
        return "No"

def retrieve_names_bulk(name_list, name_dict, global_dict=None, infer_gender=True):
    male_count = 0
    female_count = 0
    unknown_count = 0
    amb_count = 0 # Ambiguous count
    ai_count = 0
    unknown_holder = []
    ai_dict = {}

    for name in name_list:
        if name not in name_dict:
            unknown_holder.append(name)
            continue
        gender_lookup = retrieve_name(name, name_dict)
        top_gender = parse_ssa_lookup(gender_lookup)
        if top_gender == 'M':
            male_count += 1
        elif top_gender == 'F':
            female_count += 1

    if global_dict and unknown_holder:
        for name in unknown_holder:
            if name not in global_dict:
                continue
            gender_lookup = retrieve_name(name, global_dict)
            top_gender = gender_lookup
            if top_gender == 'M':
                male_count += 1
            elif gender_lookup == 'F':
                female_count += 1
            else:
                amb_count += 1
            unknown_holder.pop(unknown_holder.index(name))

    if infer_gender is False:
        diversity_score_dict = {'male': male_count, 'female': female_count, 'unknown': len(unknown_holder),
                                'amb_count': amb_count, 'ai_names': False, 'ai_count': 0}
        return diversity_score_dict

    for name in unknown_holder:
        inferred_gender = guess_name(name).lower()
        if inferred_gender == 'male':
            male_count += 1
            ai_dict[name.title()] = 'Male'
        elif inferred_gender == 'female':
            female_count = female_count + 1
            ai_dict[name.title()] = 'Female'
        ai_count += 1

    diversity_score_dict = {'male': male_count, 'female': female_count, 'unknown': 0, 'amb_count': 0,
                            'ai_names':ai_dict, 'ai_count': ai_count}
    return diversity_score_dict



def guess_name(name):
    inferred_gender = tree_model.classify(gender_features(name)).title()
    return inferred_gender

user_query_name = request.form['infer_name']
        inferred_gender = tree_model.classify(gender_features(user_query_name)).title()
        gender_lookup = retrieve_name(user_query_name, name_dict)[1]  # Selecting the message
        return render_template('infer.html', user_query=user_query_name, success='True', gender_guess=inferred_gender,
                               lookup_message=gender_lookup)