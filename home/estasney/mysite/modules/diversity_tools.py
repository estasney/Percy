from operator import itemgetter


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

def single_name(name, name_dict, global_dict=None):
    # Database lookup

    ssa_lookup = retrieve_name(name, name_dict=name_dict)
    if global_dict:
        if ssa_lookup is False:
            global_lookup = retrieve_name(name, name_dict=global_dict)

    # ML Method
    gender_guess = guess_name(name)



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


def retrieve_name(name, name_dict):
    name = name.lower()
    if name not in name_dict:
        return False
    name_lookup = name_dict[name]
    return name_lookup

def parse_ssa_lookup(data):
    sorted_data = sorted(data, key=itemgetter(1), reverse=True)
    top_gender = sorted_data[0][0]
    return top_gender


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