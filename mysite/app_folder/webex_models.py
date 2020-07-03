import hashlib
from datetime import datetime

from flask import current_app
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, VARCHAR
from sqlalchemy.orm import relationship

from app_folder import db


class APIUser(db.Model):
    __bind_key__ = "webex"
    __tablename__ = "webexusers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    api_key = Column(String(512), unique=True)

    @staticmethod
    def verify_auth_token(request):
        token = request.headers.get("Authorization")
        if not token:
            return False
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt='user-token',
                                   signer_kwargs={"digest_method": hashlib.sha3_512})
        try:
            data = s.loads(token, max_age=current_app.config.get('EXPIRE_API_TOKEN', 432_000))
        except SignatureExpired:
            current_app.logger.info("Expired Token")
            return None  # valid token, but expired
        except BadSignature:
            current_app.logger.info("Bad Signature")
            return None  # invalid token
        user = APIUser.query.get(data['id'])
        if user:
            return user
        else:
            return False

    def generate_api_token(self) -> str:
        s = URLSafeTimedSerializer(secret_key=current_app.config['SECRET_KEY'], salt='user-token',
                                   signer_kwargs={'digest_method': hashlib.sha3_512})
        data = {'id': self.id}
        token = s.dumps(data)
        self.api_key = token
        return token


class Person(db.Model):
    __bind_key__ = "webex"
    __tablename__ = 'people'

    id = Column(Integer, primary_key=True)
    external_id = Column(VARCHAR(128), nullable=False, unique=True)
    displayName = Column(VARCHAR(512))
    email = Column(VARCHAR(128), nullable=False, unique=True)
    lastActivity = Column(DateTime, nullable=True)
    lastStatus = Column(VARCHAR(512), nullable=True)

    statuses = relationship("Status", back_populates='person', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            "id":           self.id,
            "displayName":  self.displayName,
            "email":        self.email,
            "lastActivity": self.lastActivity,
            "lastStatus":   self.lastStatus
            }


class Status(db.Model):
    __bind_key__ = "webex"
    __tablename__ = 'statuses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    dt = Column(DateTime, default=datetime.now(), nullable=False)
    person_id = Column(Integer, ForeignKey("people.id"), nullable=False)
    value = Column(VARCHAR(128))

    person = relationship("Person", back_populates='statuses')
