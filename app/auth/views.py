from flask import render_template, redirect, url_for, request, flash, \
    current_app
from flask_login import login_required, login_user, logout_user, current_user

from app import db
from app.auth.forms import LoginForm, RegistrationForm, UpdatePasswordForm, \
    ResetPasswordForm, PasswordResetRequestForm, ChangeEmailRequestForm
from app.decorators import admin_required, permission_required
from app.models import User, Permission
from . import auth
from ..email import send_email


@auth.before_app_request
def before_request():
    """ before request hook
    User is registered and logged in, but cannot access app yet because
    email needs to be confirmed.
    :return:
    """

    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed \
            and request.endpoint[:5] != 'auth.':
            return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    """ Explain user how to confirm email
    :return:
    """
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


# url prefixed with /auth (url_prefix app/__init__.py)
@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # Login and validate the user.
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or
                            url_for('main.index'))
        flash('Invalid email or password.')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out')
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # store user in database
        user = User(username=form.username.data, email=form.email.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(current_app.config.get('MAIL_TO') or user.email,
                   'Confirm Your Account',
                   'auth/email/confirm',
                   user=user, token=token)
        flash('A confirmation email has been sent to you by email.')
        return redirect(url_for('main.index'))
    return render_template('auth/register.html', form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash('You have confirmed your account.')
    else:
        flash('The confirmation link is invalid or expired.')
    return redirect(url_for('main.index'))


@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_app.config.get('MAIL_TO') or current_user.email,
               'Confirm Your Account',
               'auth/email/confirm',
               user=current_user, token=token)
    flash('A confirmation email has been sent to you by email.')
    return redirect(url_for('main.index'))


@auth.route('/update_password', methods=['GET', 'POST'])
@login_required
def update_password():
    form = UpdatePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.new_password.data
            db.session.add(current_user)
            flash('Password has been updated.')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid password')
    return render_template('auth/update_password.html', form=form)


@auth.route('/reset_password/', methods=['GET', 'POST'])
def password_reset_request():
    if not current_user.is_anonymous:
        return redirect(url_for('main/index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        token = user.generate_reset_password_token()
        send_email(current_app.config.get('MAIL_TO') or current_user.email,
                   'Reset your password',
                   'auth/email/reset_password',
                   user=user, token=token)
        flash('Email to reset password has been sent.')
        return redirect(url_for('main.index'))
    return render_template('auth/password_reset_request.html', form=form)


@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if not current_user.is_anonymous:
        return redirect(url_for('main/index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            return redirect(url_for('main.index'))
        if user.reset_password(token, form.new_password.data):
            db.session.add(user)
            flash('Password has been reset')
            return redirect(url_for('auth.login'))
        else:
            return redirect(url_for('main.index'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/change_email', methods=['GET', 'POST'])
@login_required
def change_email_request():
    form = ChangeEmailRequestForm()
    if form.validate_on_submit():
        current_user.pending_email = form.new_email.data
        token = current_user.generate_change_email_token(form.new_email.data)
        send_email(current_app.config.get('MAIL_TO') or form.new_email.data,
                   'Change your email',
                   'auth/email/change_email',
                   user=current_user, token=token)
        flash('An email with instructions to confirm your new email '
              'address has been sent to you.')
        return redirect(url_for('main.index'))
    else:
        flash('Invalid email or password.')
    return render_template('auth/change_email_request.html', form=form)


@auth.route('/change_email/<token>')
@login_required
def change_email(token):
    if current_user.change_email(token):
        flash('primary email has been changed')
    else:
        flash('token is expired or invalid')
    return redirect(url_for('main.index'))

