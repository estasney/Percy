from flask import render_template, request

from app_folder.main import bp
from app_folder.tools import upload_tools, diversity_tools


@bp.route('/')
def open_page():
    return render_template('home_page.html')


@bp.route('/diversity_lookup', methods=['GET', 'POST'])
def lookup_name():
    if request.method == "GET":
        return render_template("diversity_lookup.html")

    namesearch = diversity_tools.NameStats()
    name_lookup = request.form.get('q', '')
    result = namesearch.lookup(name_lookup)
    if not result:
        return render_template('diversity_lookup.html', success='False', original=name_lookup)
    return render_template('diversity_lookup.html', success='True', original=name_lookup, result=result)


@bp.route('/diversity_score', methods=['GET', 'POST'])
def infer_diversity():
    if request.method == "GET":
        return render_template('diversity_score.html')

    file_upload = upload_tools.UploadManager(request)

    if not file_upload.status:
        return render_template('diversity_score.html', success='False')

    names_list = file_upload.file_data()

    if not names_list or names_list is False:
        return render_template('diversity_score.html', success='False', error_message=file_upload.status)

    results = diversity_tools.search_data(names_list)

    """
    Returns a dict with
        :total - the number of names
        :male - n male
        :female - n female
        :unknown - n unknown
        :95 - +/- for 95% confidence
        :99 - +/- for 99% confidence
        :ratio_female - n female / total
    """
    return render_template('diversity_score.html', n_known=results['known'], total=results['total'],
                           r_female=results['ratio_female'], n_unknown=results['unknown'], ci_95=results['95'],
                           ci_99=results['99'], success='True', n_male=results['male'], n_female=results['female'])
