import re
import typing
from datetime import datetime

import seaborn as sns
from flask_login import UserMixin
from sqlalchemy import and_
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import load_only, backref
from werkzeug.security import check_password_hash, generate_password_hash

from app_folder import db, login_manager

# Match for abbreviations
# Two or more characters with "." in between
# Except at start of line
abbreviation_catch = re.compile(r"(\.)")


def standardize_name(s):
    # remove periods from abbreviations
    s = abbreviation_catch.sub("", s)
    s = s.split(",")[0]
    s = s.lower()
    return s


Tags_Documents = db.Table('tags_documents',
                          db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True),
                          db.Column('document_id', db.Integer, db.ForeignKey('documents.id'), primary_key=True),
                          info={"bind_key": "anode"})

User_Seen_Documents = db.Table("user_seen_documents",
                               db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
                               db.Column("document_id", db.Integer, db.ForeignKey("documents.id"), primary_key=True),
                               info={"bind_key": "anode"})

User_Flag_Documents = db.Table("user_flag_documents",
                               db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
                               db.Column("document_id", db.Integer, db.ForeignKey("documents.id"), primary_key=True),
                               info={"bind_key": "anode"})


class User_LabelProjects(db.Model):
    __bind_key__ = "anode"
    __tablename__ = "user_labelprojects"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("label_projects.id"), nullable=False)
    active = db.Column(db.Boolean, default=False)

    user = db.relationship("User",
                           backref=backref("user_projects", cascade='all, delete-orphan'))
    project = db.relationship("LabelProject",
                              backref=backref("users", cascade='all, delete-orphan'))

    def __init__(self, user=None, project=None, is_active=False):
        self.project = project
        self.user = user
        self.is_active = is_active


class LabelProject(db.Model):
    __bind_key__ = "anode"
    __tablename__ = "label_projects"

    JSON_KEYS = ["id", "name", "created", "active", "labels"]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    created = db.Column(db.DateTime, default=datetime.now())
    active = db.Column(db.Boolean, default=True)
    labels = db.relationship("Label", back_populates="project", cascade="all, delete, delete-orphan")
    _tasks = db.relationship("Document", backref="project", lazy="dynamic", order_by="Document.index")

    @property
    def tasks(self):
        return self._tasks

    def tasks_complete(self, user_id: int):
        user = User.query.get(user_id)
        return self.tasks.filter(Document.seen_by.contains(user))

    def project_status(self, user_id: int):
        return self.tasks_complete(user_id).count() / self.tasks.count()

    def project_index(self, user_id: int):
        user = User.query.get(user_id)
        user_seen = db.session.query(User_Seen_Documents).filter(User_Seen_Documents.c.user_id == user.id).subquery()
        user_flagged = db.session.query(User_Flag_Documents).filter(User_Flag_Documents.c.user_id == user.id).subquery()
        index = db.session.query(Document, user_seen.c.user_id, user_flagged.c.user_id) \
            .options(load_only(Document.id, Document.name, Document.project_id)) \
            .outerjoin(user_seen, Document.id == user_seen.c.document_id) \
            .outerjoin(user_flagged, Document.id == user_flagged.c.document_id) \
            .filter(Document.project_id == self.id) \
            .with_entities(Document.id, Document.name, user_seen.c.user_id, user_flagged.c.user_id).all()
        index_out = []
        for i in index:
            td = {
                "id":      i[0], "name": i[1], "seen": True if i[2] else False,
                "flagged": True if i[3] else False
                }
            index_out.append(td)
        return index_out

    def mark_seen(self, doc_id: typing.Union[int, str], user_id: int):
        user = User.query.get(user_id)
        doc = Document.query.get(doc_id)
        if user not in doc.seen_by:
            doc.seen_by.append(user)
            db.session.commit()

    def next_document(self, user_id: int, doc_id: typing.Union[type(None), int, str] = None):
        user = User.query.get(user_id)
        if not doc_id:
            return self.tasks.filter(~Document.seen_by.contains(user)).first()
        doc_idx = Document.query.get(doc_id).index
        return Document.query.filter(and_(
                Document.project_id == self.id,
                Document.index > doc_idx,
                ~Document.seen_by.contains(user))).first()

    def fetch_document(self, doc_id: typing.Union[int, str]):
        return Document.query.get(doc_id)

    def previous_document(self, doc_id: typing.Union[type(None), int, str] = None):
        if not doc_id:
            return self.tasks.first()
        doc_idx = Document.query.get(doc_id).index
        return Document.query.filter(and_(
                Document.project_id == self.id),
                Document.index == (doc_idx - 1)).first()

    def to_dict(self):
        return {k: getattr(self, k, None) for k in self.JSON_KEYS}


class Label(db.Model):
    __bind_key__ = "anode"
    __tablename__ = "labels"

    JSON_KEYS = ["id", "name", "bg_color", "text_color", "hotkey", "active"]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    created = db.Column(db.DateTime, default=datetime.now())
    active = db.Column(db.Boolean, default=True)
    _bg_color = db.Column(db.String(128))
    text_color = db.Column(db.String(128))
    hotkey = db.Column(db.String(128))

    project = db.relationship("LabelProject", back_populates="labels")
    project_id = db.Column(db.Integer, db.ForeignKey('label_projects.id'))

    def to_dict(self):
        return {k: getattr(self, k, None) for k in self.JSON_KEYS}

    @classmethod
    def generate_color(cls, palette='hls'):
        """
        Generate a random color that is not already in use
        """
        n_labels = db.session.query(Label).options(load_only("_bg_color")).filter(Label._bg_color != None).count()
        colors = sns.color_palette(palette, n_colors=(n_labels + 1)).as_hex()
        return colors[-1]

    @property
    def bg_color(self):
        return self._bg_color

    @bg_color.setter
    def bg_color(self, bg_color_str: str, text_color_str: typing.Union[str, type(None)] = None):
        from app_folder.anode.utils import pick_font_color
        if not text_color_str:
            text_color_str = pick_font_color(bg_color_str)
        self._bg_color = bg_color_str
        self.text_color = text_color_str


class Tag(db.Model):
    __bind_key__ = "anode"
    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    user = db.relationship("User",
                           backref=backref("tags", cascade='all, delete-orphan'))
    documents = db.relationship("Document",
                                secondary=Tags_Documents,
                                backref="tags")


class Document(db.Model):
    __bind_key__ = "anode"
    __tablename__ = "documents"

    JSON_KEYS = ["id", "project_id", "name", "text", "text_abridged"]

    id = db.Column(db.Integer, primary_key=True)
    index = db.Column(db.Integer)
    project_id = db.Column(db.Integer, db.ForeignKey('label_projects.id'))
    name = db.Column(db.String(128), nullable=True)
    text = db.Column(db.Text)
    text_abridged = db.Column(db.Text)
    created = db.Column(db.DateTime, default=datetime.now())
    labels = association_proxy("doc_labels", "label")
    seen_by = db.relationship("User", secondary=User_Seen_Documents, lazy=True, back_populates='documents_seen')
    flagged_by = db.relationship("User", secondary=User_Flag_Documents, lazy=True, back_populates='documents_flagged')

    def mark_null_labels(self, user_id: int, value: bool = False):
        unmarked = DocumentLabel.query.filter(and_(
                DocumentLabel.user_id == user_id,
                DocumentLabel.document_id == self.id,
                DocumentLabel.selected == None)).all()

        if not unmarked:
            return None
        for dl in unmarked:
            dl.selected = value
        db.session.commit()

    def labels_data(self, user_id: int) -> list:
        """
        Returns a projects labels with any user annotations
        :param user: User object
        :return:
        """
        user = User.query.get(user_id)
        project_labels = [label.to_dict() for label in self.project.labels]
        user_labels = list(filter(lambda x: x.user_id == user.id, self.doc_labels))
        output = []
        for label in project_labels:
            matched_user_label = next((user_label for user_label in user_labels if user_label.label_id == label['id']),
                                      None)
            if not matched_user_label:
                label.update({'selected': None})
            else:
                label.update({'selected': matched_user_label.selected})
            output.append(label)
        return output

    def labeltools(self, user_id: int) -> list:
        tools = []
        tools.append({'id': 'flag', 'active': self.is_flagged_by_user(user_id)})
        return tools

    def is_flagged_by_user(self, user_id):
        return user_id in [user.id for user in self.flagged_by]

    def to_dict(self, user_id: int) -> dict:
        d = {k: getattr(self, k, None) for k in self.JSON_KEYS}
        d['labels_data'] = self.labels_data(user_id)
        d['labeltools'] = self.labeltools(user_id)
        return d


class DocumentLabel(db.Model):
    NA = None
    YES = True
    NO = False

    __bind_key__ = "anode"
    __tablename__ = "documentlabels"

    document_id = db.Column(db.Integer, db.ForeignKey("documents.id"), primary_key=True)
    label_id = db.Column(db.Integer, db.ForeignKey("labels.id"), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    selected = db.Column(db.Boolean, default=None, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.now())

    label = db.relationship(Label,
                            backref=backref("documents", cascade='all, delete-orphan'))

    user = db.relationship("User",
                           backref=backref("labels", cascade='all, delete-orphan'))

    document = db.relationship(Document,
                               backref=backref("doc_labels", cascade='all, delete-orphan'))

    def __init__(self, label=None, document=None, user=None, selected=False):
        self.document = document
        self.label = label
        self.user = user
        self.selected = selected


class User(UserMixin, db.Model):
    __bind_key__ = "anode"
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128))
    password_hash = db.Column(db.Text)
    _is_active = db.Column(db.Boolean, default=True)
    projects = association_proxy("user_projects", "project",
                                 creator=lambda project: User_LabelProjects(project=project))
    documents_seen = db.relationship("Document", secondary=User_Seen_Documents, lazy=True, back_populates='seen_by')
    documents_flagged = db.relationship("Document", secondary=User_Flag_Documents, lazy=True,
                                        back_populates='flagged_by')

    def __init__(self, username, password):
        self.username = username
        self.password_hash = generate_password_hash(password)

    @property
    def is_active(self):
        return self._is_active

    @property
    def active_project(self):
        if not self.user_projects:
            return None
        active_project = next((prj for prj in self.user_projects if prj.active), None)
        if not active_project:
            return None
        return active_project.project

    @active_project.setter
    def active_project(self, project: LabelProject):
        current_active = next((prj for prj in self.user_projects if prj.active), None)
        if current_active:
            current_active.active = False
        matched_project = next((prj for prj in self.user_projects if prj.project_id == project.id), None)
        if not matched_project:
            raise IndexError("No project found for ID {}".format(project.id))
        matched_project.active = True
        db.session.commit()

    def get_id(self):
        return str(self.id)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_new_password(self, new_password):
        self.password_hash = generate_password_hash(new_password)


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))
