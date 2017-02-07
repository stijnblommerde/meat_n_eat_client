import urllib
import json
import time

from flask import flash
from flask_login import current_user
from httplib2 import Http, ServerNotFoundError
from flask import render_template, request, redirect, url_for, session, \
    flash, abort
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

    if request.method == 'POST':
        print('enter post')
        content = request.get_json(force=True)
        auth_code = content['auth_code']
        data = dict(auth_code=auth_code)
        try:
            response, content_bytes = h.request(
                'http://localhost:5000/api/v1/google/login', method='POST',
                body=json.dumps(data),
                headers={"Content-Type": "application/json"})
            if response['status'] == '404':
                return render_template('404.html'), 404
            token = json.loads(content_bytes.decode())['token']
            session['api_token'] = token
            return redirect(url_for('main.index'))
        except:
            return 'request refused'
    return redirect(url_for('main.index'))


@main.route('/')
@login_required
def index():
    print('enter index')
    print('token:', session.get('api_token'))
    if not session.get('api_token'):
        print('no token stored')
        return redirect(url_for('main.get_token'))
    try:
        h = Http()
        h.add_credentials(session.get('api_token'), '')
        response, content_bytes = h.request(
            'http://localhost:5000/api/v1/requests', method='GET')
    except:
        return 'connection refused'
    content = content_bytes.decode()
    print('response:', response)
    print('content:', content)
    if content == 'no open meal requests of others':
        print('enter no open meal requests')
        flash('No open meal requests of others')
        return render_template('index.html', requests=[])
    elif content == 'Unauthorized Access':
        print('unauthorized access')
        return redirect(url_for('main.get_token'))
    requests = json.loads(content)
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