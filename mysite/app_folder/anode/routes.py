from flask import render_template, request, jsonify, redirect, url_for
from flask_login import login_user, login_required, current_user, logout_user

from app_folder import db
from app_folder.anode import bp
from app_folder.anode.utils import (get_latest_project, get_labels, get_next_document, update_doc_labels,
                                    update_project_labels)
from app_folder.anode_models import LabelProject, Document, User


@bp.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('anode.login'))

    latest_project = get_latest_project(current_user)
    if not latest_project:
        return render_template("anode/main/index.html")

    else:
        return render_template("anode/main/index.html", project_status=latest_project.project_status(current_user.id),
                               project_name=latest_project.name, project_id=latest_project.id,
                               endpoint=url_for('anode.label_docs', project_id=latest_project.id, category='label'),
                               btn_text="Start Labeling")


@bp.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template("anode/main/login.html", error=False)
    user = User.query.filter_by(username=request.form['username']).first()
    if user is None:
        return render_template("anode/main/login.html", error=True)

    if not user.check_password(request.form['password']):
        return render_template('anode/main/login.html', error=True)

    login_user(user, remember=True)
    return redirect(url_for('anode.index'))


@bp.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect(url_for('anode.index'))


@login_required
@bp.route("/api/label/manage/<project_id>", methods=['GET', 'POST', 'PATCH', 'DELETE'])
def label_api_sub(project_id):
    project = LabelProject.query.get(project_id)
    if request.method == 'GET':
        labels = [label.to_dict() for label in project.labels]
        r = {"status": "success", "labels": labels}
        return jsonify(r), 200
    elif request.method == 'POST':
        labels_data = request.json.get('labels', None)
        if not labels_data:
            error_message = "Missing field labels"
            r = {"status": "error", "message": error_message}
            return jsonify(r), 400
        update_project_labels(project, client_labels=labels_data, user_id=current_user.id)


@login_required
@bp.route('/api/label/<project_id>', methods=['GET', 'POST', 'PATCH', 'DELETE'])
def label_api(project_id):
    project = LabelProject.query.get(project_id)
    if request.method == 'GET':
        action = request.args.get('action', default='setup', type=str)
        doc_id_in = request.args.get('doc_id_in', default=None)
        doc_id_out = request.args.get('doc_id_out', default=None)
        # next_document = partial(get_next_document, action=action, user_id=current_user.id, project=project,
        #                         incoming_doc_id=doc_id_in, outgoing_doc_id=doc_id_out)
        doc = get_next_document(action=action, project=project, user_id=current_user.id, incoming_doc_id=doc_id_in,
                                outgoing_doc_id=doc_id_out)
        if action == "setup":
            r = {"status": "success", "document": doc, "index": project.project_index(current_user.id)}
        else:
            r = {"status": "success", "document": doc, "index": project.project_index(current_user.id)}
        db.session.commit()
        return jsonify(r), 200

    if request.method == "POST":
        # We will be changing selected on one label
        doc_id, labels_data = request.json.get('doc_id_in', None), request.json.get('labels', None)
        if not all([doc_id, labels_data]):
            error_message = ""
            if not doc_id:
                error_message += "Missing field doc_id_in "
            if not labels_data:
                error_message += "Missing field labels "
            r = {"status": "error", "message": error_message}
            return jsonify(r), 400
        update_doc_labels(doc_id, labels_data, user_id=current_user.id)
        doc = Document.query.get(doc_id)
        r = {"status": "success", "document": doc.to_dict(current_user.id)}

        return jsonify(r), 200


@login_required
@bp.route("/label/<project_id>/<category>", methods=["GET", "POST"])
@bp.route("/label/<project_id>", methods=['GET', 'POST'], defaults={"category": None})
def label_docs(project_id, category):
    if category == "manage_labels":
        return render_template("anode/labels/projectLabelApp.html", project_id=project_id)
    if category == "label":
        return render_template("anode/labels/labelApp.html", project_id=project_id)


