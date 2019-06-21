from app_folder import db


class Name(db.Model):
    __tablename__ = "names"

    name = db.Column(db.String(128), primary_key=True)
    male_count = db.Column(db.Integer, default=0)
    female_count = db.Column(db.Integer, default=0)

    def __repr__(self):
        return "{} : ({}, {})".format(self.name, self.male_count, self.female_count)
