from datetime import datetime, timezone
import typing
import sqlalchemy as sa
import sqlalchemy.orm as saorm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5

from app import db, login

class User(UserMixin, db.Model):
    id: saorm.Mapped[int] = saorm.mapped_column(primary_key=True)
    username: saorm.Mapped[str] = saorm.mapped_column(sa.String(64), index=True, unique=True)
    email: saorm.Mapped[str] = saorm.mapped_column(sa.String(64), index=True, unique=True)
    password_hash: saorm.Mapped[typing.Optional[str]] = saorm.mapped_column(sa.String(256))
    about_me: saorm.Mapped[typing.Optional[str]] = saorm.mapped_column(sa.String(140))
    last_seen: saorm.Mapped[typing.Optional[datetime]] = saorm.mapped_column(default=lambda: datetime.now(timezone.utc))

    posts: saorm.WriteOnlyMapped['Post'] = saorm.relationship(back_populates='author')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))

class Post(db.Model):
    id: saorm.Mapped[int] = saorm.mapped_column(primary_key=True)
    body: saorm.Mapped[str] = saorm.mapped_column(sa.String(140))
    timestamp: saorm.Mapped[datetime] = saorm.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    user_id: saorm.Mapped[int] = saorm.mapped_column(sa.ForeignKey(User.id), index=True)

    author: saorm.Mapped[User] = saorm.relationship(back_populates='posts')

    def __repr__(self):
        return '<Post {}>'.format(self.body)