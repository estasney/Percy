from typing import Union
from colour import Color
from app_folder.anode_models import *


def get_latest_project(user):
    user = User.query.get(user.id)
    return user.active_project


def update_project_labels(project: LabelProject, client_labels: list, user_id: Union[str, int]):
    """
        Request returns the state of one or more labels. Look for changes to state and update accordingly in db
    """
    user = User.query.get(user_id)
    db_labels = project.labels

    label_keys = ['active', ('bg_color', '_bg_color'), 'hotkey', 'name', 'text_color']

    for label in client_labels:
        # Existing or new?
        try:
            label_id = int(label['id'])
        except (ValueError, TypeError):
            label_id = None

        # If existing attempt to find match db label
        if label_id:
            matched_db_label = next((dl for dl in db_labels if dl.id == label_id), None)
        else:
            matched_db_label = None

        if not matched_db_label:
            label_params = {"project_id": project.id}
            for k in label_keys:
                if isinstance(k, str):
                    label_params[k] = label.get(k, None)
                else:
                    label_params[k[1]] = label.get(k[0], None)

            db_label = Label(**label_params)
            db.session.add(db_label)
        else:
            for k in label_keys:
                if isinstance(k, str):
                    client_key, db_key = k, k
                else:
                    client_key, db_key = k[0], k[1]
                new_value, old_value = label.get(client_key, None), getattr(matched_db_label, db_key)
                if new_value == old_value:
                    continue
                setattr(matched_db_label, db_key, new_value)

    db.session.commit()
    return project.labels


def update_doc_labels(doc_id, client_labels, client_labeltools, user_id):
    """
    Request returns the current state of the labels. Look for changes to state and update accordingly in db
    """

    user = User.query.get(user_id)
    db_labels = DocumentLabel.query.filter(and_(
            DocumentLabel.document_id == doc_id,
            DocumentLabel.user_id == user_id)).all()
    document = Document.query.get(doc_id)
    doc_labels_out = []

    for label in client_labels:
        # Map to a db label
        client_label_state = label['selected']
        matched_db_label = next((dl for dl in db_labels if dl.label_id == int(label['id'])), None)
        if not matched_db_label:  # This doesn't exist, create it
            matched_label = Label.query.get(int(label['id']))
            matched_db_label = DocumentLabel(document=document, label=matched_label, user=user,
                                             selected=client_label_state)
            db.session.add(matched_db_label)
        else:  # It does exist mark selected if it is True or False
            if client_label_state is not None:
                matched_db_label.selected = client_label_state
        doc_labels_out.append(matched_db_label)

    # look for flags
    doc_flag = next((lt for lt in client_labeltools if lt['id'] == 'flag'), None)
    if not doc_flag:
        db.session.commit()
        return doc_labels_out

    client_doc_flagged = doc_flag['active'] is True
    db_doc_flagged = document.is_flagged_by_user(user_id)

    if client_doc_flagged != db_doc_flagged:
        if client_doc_flagged and not db_doc_flagged:
            document.flagged_by.append(user)
        else:
            del_obj = User_Flag_Documents.delete().where(and_(
                    User_Flag_Documents.c.user_id == user_id,
                    User_Flag_Documents.c.document_id == doc_id
                    ))

            db.session.execute(del_obj)

    db.session.commit()
    return doc_labels_out


def get_labels(doc_id=None, project_id=None):
    if not project_id:
        latest_label_project = LabelProject.query.filter(LabelProject.active == True).first()
    else:
        latest_label_project = LabelProject.query.get(project_id)

    labels = Label.query.filter(Label.project_id == latest_label_project.id).all()
    labels_out = []
    if not doc_id:
        for label in labels:
            ld = label.to_dict()
            ld.update({'selected': False})
            labels_out.append(ld)
    else:
        doc = Document.query.get(doc_id)
        doc_labels = doc.selected_labels
        for label in labels:
            ld = label.to_dict()
            ld_selected = label.id in doc_labels
            ld.update({'selected': ld_selected})
            labels_out.append(ld)
    return labels_out


def get_next_document(action: str, project: LabelProject, user_id: int, incoming_doc_id: Union[int, str], step: int = 1,
                      outgoing_doc_id: Union[type(None), str, int] = None):
    """
    Handles client requests for documents.

    ====
    'setup'
    ====
    first request - incoming and outgoing ids are None
    no documents are marked as seen

    ====
    'next' / 'back'
    ====
    user wants next document - supplies incoming id. outgoing is none
    mark incoming document as seen
    mark all labels for document that have selected == None as False
    """
    data = {}
    if action == 'setup':
        doc_out = project.next_document(user_id=user_id, doc_id=None)
        data["project_status"] = project.project_status(user_id)
        data.update(doc_out.to_dict(user_id))
    elif action in ['next', 'back', 'fetch']:
        doc_in = Document.query.get(incoming_doc_id)
        project.mark_seen(doc_id=incoming_doc_id, user_id=user_id)
        doc_in.mark_null_labels(user_id=user_id, value=False)
        if action == 'next':
            doc_out = project.next_document(user_id=user_id, doc_id=incoming_doc_id)
        elif action == 'back':
            doc_out = project.previous_document(doc_id=incoming_doc_id)
        elif action == 'fetch':
            doc_out = project.fetch_document(doc_id=outgoing_doc_id)
        data["project_status"] = project.project_status(user_id)
        data.update(doc_out.to_dict(user_id))
    return data

def pick_font_color(color_str: str, luminance_threshold: float = 0.5) -> str:
    """
    Given a background color, determine whether a font should be black or white based on calculated luminance
    :param color_str: Color string such as hex, RGB, etc
    :param luminance_threshold: Luminances above this threshold return 'black', below returns 'white'
    :return: 'black' or 'white'
    """
    c = Color(color_str)
    lum = c.get_luminance()
    if lum >= luminance_threshold:
        return '#000000'
    else:
        return '#ffffff'
