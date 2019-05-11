from flask import jsonify

from app_folder.autocomplete import bp, autocomplete_tools


@bp.route('/', methods=['GET'])
def autocomplete():
    terms = autocomplete_tools.get_autocomplete(dataset='words')
    return jsonify(terms)


@bp.route('/skills', methods=['GET'])
def autocomplete_skills():
    terms = autocomplete_tools.get_autocomplete(dataset='skills')
    return jsonify(terms)


@bp.route('/names', methods=['GET'])
def autocomplete_names():
    names = autocomplete_tools.get_autocomplete(dataset="names")
    return jsonify(names)
