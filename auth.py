from flask import request, redirect, url_for, session, flash, render_template
from functools import wraps
import hashlib
import os

# Credenziali utente (modifica con le tue credenziali)
USERS = {
    'admini': hashlib.sha256('Valt2023'.encode()).hexdigest()
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def init_auth(app):
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            if username in USERS and USERS[username] == hashlib.sha256(password.encode()).hexdigest():
                session['logged_in'] = True
                session['username'] = username
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect(url_for('index'))
            else:
                flash('Username o password non validi', 'danger')
        
        # Usa direttamente render_template senza riferimento a app
        return render_template('login.html')
    
    @app.route('/logout')
    def logout():
        session.pop('logged_in', None)
        session.pop('username', None)
        flash('Logout effettuato con successo', 'success')
        return redirect(url_for('login'))
    
    return app