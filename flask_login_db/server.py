from flask import render_template, redirect, url_for, flash, abort, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, current_user, logout_user

from functools import wraps
from modules.forms import LoginForm, RegisterForm
from modules.config import app, db, login_manager
from modules.databases import User

admin_list = [1]

with app.app_context():
    db.create_all()

# 4) Flask-login también requiere definir una función "user_loader",
# dado un ID de usuario, devuelve el objeto usuario asociado.
@login_manager.user_loader  
def user_loader(user_id):
    print(user_id)
    return db.session.get(User, user_id) 

# 9)usuarios admin
def is_admin():
    if current_user.is_authenticated and current_user.id in admin_list:
        return True
    else:
        return False

# https://flask.palletsprojects.com/en/2.3.x/patterns/viewdecorators/
# decorador para restringir el acceso a una vista a usuarios administradores
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.id not in admin_list:
            return abort(403) # la función abort() permite devolver errores HTTP de forma sencilla
                              # 403 significa "Forbidden"
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def home():

    if 'username' in session:
        username = session['username']
    else:
        username = 'Invitado'

    print(current_user)
    return render_template('home.html', user=username, logged_in=current_user.is_authenticated)

# 6)login
@app.route("/login", methods= ["GET", "POST"])
def login():
    login_form = LoginForm()
    # Acceso a la información ingresada en el formulario
    # cuando el usuario realiza el "submit".
    if login_form.validate_on_submit():
        #hacemos una consulta filtrando por email para
        #saber si hay un usuario registrado con ese email
        user = User.query.filter_by(email=login_form.email.data).first()
        if not user:
            flash("That email does not exist, please try again")
        elif not check_password_hash(user.password, login_form.password.data):
            flash("Password incorrect, please try again.")
        else:
            login_user(user)
            print(current_user)
            session['username'] = user.username
            print(session['username'])

            # return redirect(url_for('welcome', username=user.username))
            if is_admin():
                return redirect(url_for('admin', username=user.username)) 
            else:
                return redirect(url_for('welcome', username=user.username))        
    return render_template('login.html', form=login_form)

# 5) Register
@app.route("/register", methods= ["GET", "POST"])
def register():
    register_form = RegisterForm()
    # Acceso a la información ingresada en el formulario
    # cuando el usuario realiza el "submit".
    if register_form.validate_on_submit():
        # Verifico que no exista usuario con igual email
        if User.query.filter_by(email=register_form.email.data).first():
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))
        # Si el registro es correcto, se crea un nuevo usuario en la db
        encripted_pass = generate_password_hash(
            password= register_form.password.data,
            method= 'pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email = register_form.email.data,
            password = encripted_pass, #register_form.password.data
            username = register_form.username.data
        )
        
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template('register.html', form=register_form)

# 8) decoramos la vista con login_required para asegurar de que el usuario actual está conectado
# y autenticado antes de llamar a la función
@app.route("/welcome/<username>")
@login_required
def welcome(username):           
    return render_template('welcome.html', user=username)

# 10)
@app.route("/admin/<username>")
@admin_only
def admin(username):           
    return render_template('admin.html', user=username)

# 7)logout
@app.route("/logout")
def logout():   
    print(current_user)  
    logout_user()      
    print(current_user)
    session['username'] = 'Invitado' 
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')