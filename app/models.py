from datetime import datetime, timezone
from time import time
import typing
import sqlalchemy as sa
import sqlalchemy.orm as saorm
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5
from flask import current_app

from app import db, login


followers = sa.Table(
    'followers',
    db.metadata,
    sa.Column('follower_id', sa.Integer, sa.ForeignKey('user.id'), primary_key=True),
    sa.Column('followed_id', sa.Integer, sa.ForeignKey('user.id'), primary_key=True)
)   # auxiliary table, it has no data other then foreign keys, saorm there is no need to make a model class

class User(UserMixin, db.Model):
    id: saorm.Mapped[int] = saorm.mapped_column(primary_key=True)
    username: saorm.Mapped[str] = saorm.mapped_column(sa.String(64), index=True, unique=True)
    email: saorm.Mapped[str] = saorm.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: saorm.Mapped[typing.Optional[str]] = saorm.mapped_column(sa.String(256))
    about_me: saorm.Mapped[typing.Optional[str]] = saorm.mapped_column(sa.String(140))
    last_seen: saorm.Mapped[typing.Optional[datetime]] = saorm.mapped_column(default=lambda: datetime.now(timezone.utc))

    posts: saorm.WriteOnlyMapped['Post'] = saorm.relationship(back_populates='author')
    
    following: saorm.WriteOnlyMapped['User'] = saorm.relationship(
        secondary=followers, primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        back_populates='followers')
    followers: saorm.WriteOnlyMapped['User'] = saorm.relationship(
        secondary=followers, primaryjoin=(followers.c.followed_id == id),
        secondaryjoin=(followers.c.follower_id == id),
        back_populates='following')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

    def follow(self, user):
        if not self.is_following(user):
            self.following.add(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.following.remove(user)

    def is_following(self, user):
        query = self.following.select().where(User.id == user.id)
        return db.session.scalar(query) is not None

    def followers_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.followers.select().subquery())
        return db.session.scalar(query)

    def following_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.following.select().subquery())
        return db.session.scalar(query)

    def following_posts(self):
        Author = saorm.aliased(User)
        Follower = saorm.aliased(User)
        return (
            sa.select(Post)
            .join(Post.author.of_type(Author))
            .join(Author.followers.of_type(Follower), isouter=True)
            .where(sa.or_(
                Follower.id == self.id,
                Author.id == self.id,
            ))
            .group_by(Post)
            .order_by(Post.timestamp.desc())
        )
    
    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256'
        )
    @staticmethod
    def verif_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config,
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return db.session.get(User, id)

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