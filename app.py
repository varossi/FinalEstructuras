from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
from config import config
from flask_login import LoginManager,login_user,logout_user,login_required,current_user
from flask_wtf import FlaskForm, CSRFProtect
from models.ModelUser import ModelUser
from models.forms import ReservationForm
from models.nuevousuario import UsuarioForm
from models.entities.User import User
from datetime import datetime
from werkzeug.security import generate_password_hash

app = Flask(__name__)
csrf = CSRFProtect(app)

db = MySQL(app)
Login_manager_app=LoginManager(app)
Login_manager_app.login_view = "login"


@Login_manager_app.user_loader
def load_user(id):
    return ModelUser.get_by_id(db,id)

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
    
        user =User(0,request.form['username'],request.form['password'])
        logged_user=ModelUser.login(db,user)
        if logged_user != None:
            if logged_user.password:
                login_user(logged_user)
                return redirect(url_for('home'))
            else:
                flash("Contraseña incorrecta...")
                return render_template('auth/login.html')
        else:
            flash("usuario no encontrado...")
            return render_template('auth/login.html')
    else:
        return render_template('auth/login.html')

@app.route('/logout')
def logout():
    logout_user()
    return render_template('auth/login.html')

@app.route('/home')
@login_required
def home():
    return render_template('home.html')

@app.route('/contacto')
@login_required
def contacto():
    return render_template('contacto.html')

@app.route('/fotos')
@login_required
def fotos():
    return render_template('fotos.html')


@app.route('/nuevareserva', methods=['GET', 'POST'])
@login_required
def nuevareserva():
    form = ReservationForm()
    if request.method == 'POST':
        name = request.form['name']
        room_type = request.form['room_type']
        check_in = datetime.strptime(request.form['check_in'], '%Y-%m-%d')
        check_out = datetime.strptime(request.form['check_out'], '%Y-%m-%d')

        cursor = db.connection.cursor()
        cursor.execute('INSERT INTO reservations (user_id, name, room_type, check_in, check_out) VALUES (%s, %s, %s, %s, %s)', 
                       (current_user.id, name, room_type, check_in, check_out))
        db.connection.commit()
        return redirect('/reservas')
    
    return render_template('nuevareserva.html', form=form)

@app.route('/reservas')
@login_required
def reservations():

    cursor = db.connection.cursor()
    cursor.execute('SELECT * FROM reservations WHERE user_id = %s', (current_user.id,))
    reservations = cursor.fetchall()
    return render_template('reservas.html', reservations=reservations)

@app.route('/nuevousuario', methods=['GET', 'POST'])
def nuevousuario():
    form = UsuarioForm()
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        fullname = request.form['fullname']

        cursor = db.connection.cursor()
        cursor.execute('INSERT INTO user (username, password, fullname) VALUES (%s, %s, %s)', (username, password, fullname))
        db.connection.commit()
        return redirect('/login')
    
    return render_template('nuevousuario.html', form=form)



def status_401(error):
    return render_template('auth/login.html')

def query_string():
    print(request)
    print(request.args)
    print(request.args.get('param1'))
    return "ok"

def pagina_no_encontrada(error):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.config.from_object(config['development'])
    app.add_url_rule('/query_string', view_func=query_string)
    app.register_error_handler(404, pagina_no_encontrada)
    app.register_error_handler(401, status_401)
    app.run(port=5000)