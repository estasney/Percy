def prettify_dict(d):
    p_dict = {}
    for k, v in d.items():
        pk = k.replace("_", " ")
        pk = pk.title()
        pv = v*100
        pv = round(pv, 1)
        pv = str(pv) + "%"
        p_dict[pk] = pv
    return p_dict

def readable_gender(gender_code):
    if gender_code.upper() == 'M':
        gender_read = 'Male'
    elif gender_code.upper() == 'F':
        gender_read = 'Female'
    elif gender_code.upper() == 'U':
        gender_read = 'Ambiguous'
    else:
        gender_read = "Unknown"
    return gender_read
