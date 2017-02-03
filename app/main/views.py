import urllib
import json

from flask import flash
from flask_login import current_user
from httplib2 import Http
from flask import render_template, request, redirect, url_for, session
from flask_login import login_required

from app import db
from app.main import main
from app.main.forms import EditProfileForm, EditProfileAdminForm
from app.models import User, Role

h = Http()


@main.route('/token', methods=['GET', 'POST'])
def get_token():
    """ login
    :return:
    """
    if request.method == 'GET':
        auth_code = render_template('clientOAuth.html')
        return auth_code
    elif request.method == 'POST':
        content = request.get_json(force=True)
        auth_code = content['auth_code']
        data = dict(auth_code=auth_code)
        response, content_bytes = h.request(
            'http://localhost:6000/api/v1/google/login', method='POST',
            body=json.dumps(data),
            headers={"Content-Type": "application/json"})
        token = json.loads(content_bytes.decode())['token']
        #TODO: store token in session and redirect
        print('token:', token)
        session['api_token'] = token
        print('session:', session)
        return render_template('index.html')


@main.route('/')
@login_required
def index():
    #print('session:', session)
    if not session.get('api_token'):
        return 'No token'
    h = Http()
    h.add_credentials(session.get('api_token'), '')
    response, content_bytes = h.request(
        'http://localhost:6000/api/v1/requests', method='GET')
    requests = json.loads(content_bytes.decode())['requests']
    print(requests)
    return render_template('index.html', requests=requests)


@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    return render_template('user.html', user=user)


@main.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('Your profile has been updated')
        return redirect(url_for('main.user', username=current_user.username))
    # input velden invullen met data opgeslagen in session
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/edit_profile/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('The profile has been updated')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)