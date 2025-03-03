from flask import Blueprint, render_template, flash, redirect, url_for, request, abort, current_app
import sqlalchemy as sa
from app import db
from app.email import send_password_reset_email
from app.forms import LoginForm, RegistrationForm, EditProfileForm, EmptyForm, PostForm, ResetPasswordRequestForm, ResetPasswordForm
from app.models import User, Post
from urllib.parse import urlsplit
from flask_login import current_user, login_user, logout_user, login_required
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

bp = Blueprint('routes', __name__)

def change_username(user, new_username):
    user.username = new_username
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        abort(500)


def change_bio(user, new_bio):
    user.about_me = new_bio
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        abort(500)


@bp.before_request # means before view func
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('routes.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('routes.login'))
    return render_template('register.html', title='Register', form=form)

@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('route.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.email == form.email.data))
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('routes.login'))
    return render_template('reset_password_request.html', title='Reset Password', form=form)

@bp.route('/reset_passwrod/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('routes.index'))
    user = User.verif_reset_password_token(token)
    if not user:
        return redirect(url_for('routes.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('routes.login'))
    return render_template('reset_password.html', form=form)

@bp.route('/login', methods=['GET', 'POST']) # overrides default methods=['GET']
def login():
    if current_user.is_authenticated:
        return redirect(url_for('routes.index'))
    form = LoginForm()
    if form.validate_on_submit(): # runs all attached validators and if everything is ok return True
        user = db.session.scalar(sa.select(User).where(User.email == form.email.data))
        if user is None or not user.check_password(form.password.data):
            flash('FUCK OFF Неверный email или пароль')
            return redirect(url_for('routes.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('routes.index')
        return redirect(next_page)
    return render_template('login.html', title = 'Login', form=form) # renders html-template

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('routes.index'))

@bp.route('/user/<username>')
@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    page = request.args.get('page', 1, type=int)
    query = user.posts.select().order_by(Post.timestamp.desc())
    posts = db.paginate(query, page=page,
                        per_page=current_app.config['POSTS_PER_PAGE'],
                        error_out=False)
    next_url = url_for('routes.user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('routes.user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None 
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts, 
                           next_url=next_url, prev_url=prev_url, form=form)

@bp.route('/user/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        change_username(current_user, form.username.data)
        change_bio(current_user, form.about_me.data) 
        flash('Your changes have been saved.')
        return redirect(url_for('routes.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form)

@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.username == username))
        if user is None:
            flash(f'User {username} not found.')
            return redirect(url_for('routes.index'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('routes.user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash(f'You are following {username}!')
        return redirect(url_for('routes.user', username=username))
    else:
        return redirect(url_for('routes.index'))

@bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username))
        if user is None:
            flash(f'User {username} not found.')
            return redirect(url_for('routes.index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('routes.user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash(f'You are not following {username}.')
        return redirect(url_for('routes.user', username=username))
    else:
        return redirect(url_for('routes.index'))

@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    query = sa.select(Post).order_by(Post.timestamp.desc())
    posts = db.paginate(query, page=page, 
                        per_page=current_app.config['POSTS_PER_PAGE'], 
                        error_out=False)
    next_url = url_for('routes.explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('routes.explore', page=posts.prev_num) \
        if posts.has_prev else None 
    return render_template('index.html', title='Explore',
                            posts=posts.items, 
                            next_url=next_url, prev_url=prev_url)

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('routes.index'))
    page = request.args.get('page', 1, type=int)
    posts = db.paginate(current_user.following_posts(), page=page, 
                        per_page=current_app.config['POSTS_PER_PAGE'], 
                        error_out=False)
    next_url = url_for('routes.index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('routes.index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title = 'Home', 
                            form=form, posts=posts.items,
                            next_url=next_url, prev_url=prev_url)

