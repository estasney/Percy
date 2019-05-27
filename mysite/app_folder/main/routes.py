from flask import render_template, request, jsonify, redirect, url_for

from app_folder.main import bp
from app_folder.tools import upload_tools, diversity_tools


@bp.route('/')
def open_page():
    return render_template('home_page.html')


@bp.route('/diversity_lookup', methods=['GET', 'POST'])
def lookup_name():
    if request.method == "GET":
        return render_template("diversity_lookup.html")

    name_lookup = request.form.get('q', '')
    result = diversity_tools.get_name_count(name_lookup)
    if not result:
        return render_template('diversity_lookup.html', success='False', original=name_lookup)
    return render_template('diversity_lookup.html', success='True', original=name_lookup, result=result)


@bp.route('/diversity_analysis', methods=['GET', 'POST'])
def infer_diversity():
    if request.method == "GET":
        return render_template('diversity_analysis.html')

    if request.files.get('file', None):
        file_upload = upload_tools.UploadManager(request)
        if not file_upload.status:
            return render_template('diversity_analysis.html', success='False')
        names_list = file_upload.file_data()
        if not names_list:
            return render_template('diversity_analysis.html', success='False', error_message=file_upload.status)
    else:
        names_list = request.form.get('paste_names', '')
        if not names_list:
            return render_template('diversity_analysis.html', success='False', error_message="Unable to analyze names")
        else:
            names_list_lines = names_list.splitlines()
            names_list_commas = names_list.split(",")
            names_list = max([names_list_lines, names_list_commas], key=lambda x: len(x))
            del names_list_lines, names_list_commas

    try:
        ratio_female = int(request.form['female_range']) / 100
        sample_min_size = int(request.form['sample_min_size'])
        sample_min_size_uniform = int(request.form['sample_min_size_uniform'])
        random_seed = int(request.form['random_seed'])
        n_trials = min([abs(int(request.form['n_trials'])), 1000])
        n_trials = max([2, n_trials])

    except ValueError or IndexError:
        return render_template('diversity_analysis.html', success='False', error_message="Invalid Parameters Passed")

    searcher = diversity_tools.NameSearch(ratio_female=ratio_female, sample_min_size=sample_min_size,
                                          sample_min_size_uniform=sample_min_size_uniform)

    result = searcher.summarize_gender(names_list, n_name_samples=n_trials, random_seed=random_seed)

    if not result:
        return render_template("diversity_analysis.html", success='False', error_message='No names recognized')

    return render_template('diversity_analysis.html', result=result)