from flask import Blueprint, request, render_template, url_for, redirect
from flask_login import login_user, login_required, logout_user

from .models import User

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        result = User.check_login(email, password)
        if result:
            login_user(result, remember=True)
            return redirect(url_for('views.home'))
        else:
            return render_template('login.html', error=True)

    return render_template('login.html')


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        result = User.validate_email(email)
        if result:
            User.create_new_user(email, password)
            return redirect(url_for('auth.login'))
        else:
            return render_template('register.html', error=True)
    return render_template('register.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
