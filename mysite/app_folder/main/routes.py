from flask import render_template, request, jsonify

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

    file_upload = upload_tools.UploadManager(request)

    if not file_upload.status:
        return render_template('diversity_analysis.html', success='False')

    names_list = file_upload.file_data()
    print("Finished Loading")

    if not names_list or names_list is False:
        return render_template('diversity_analysis.html', success='False', error_message=file_upload.status)

    form = request.form
    try:
        ratio_female = int(form['female_range']) / 100
        sample_min_size = int(form['sample_min_size'])
        sample_min_size_uniform = int(form['sample_min_size_uniform'])
    except ValueError:
        return render_template('diversity_analysis.html', success='False', error_message="Invalid Parameters Passed")

    searcher = diversity_tools.NameSearch(ratio_female=ratio_female, sample_min_size=sample_min_size,
                                          sample_min_size_uniform=sample_min_size_uniform)

    result = searcher.summarize_gender(names_list)

    return render_template('diversity_analysis.html', result=result)
