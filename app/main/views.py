import urllib
import json
from httplib2 import Http
from flask import render_template, request, redirect, url_for
from flask_httpauth import HTTPBasicAuth
from app.main import main

auth = HTTPBasicAuth()


@main.index


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
        h = Http()
        data = dict(auth_code=auth_code)
        response, content_bytes = h.request(
            'http://localhost:6000/api/v1/google/login', method='POST',
            body=json.dumps(data),
            headers={"Content-Type": "application/json"})
        token = json.loads(content_bytes.decode())['token']
        #TODO: store token in session and redirect
        return redirect(url_for())
