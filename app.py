# Importar las librerías necesarias para Flask y otras funcionalidades
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_mysqldb import MySQL
from config import config
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf import CSRFProtect
from models.ModelUser import ModelUser
from models.forms import ReservationForm
from models.nuevousuario import UsuarioForm
from models.entities.User import User
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
import matplotlib
matplotlib.use('Agg')  # Configurar matplotlib para usar un backend sin interfaz gráfica
import matplotlib.pyplot as plt
import io
import base64
import numpy as np
from pandas import pandas as pd

# Crear una instancia de la aplicación Flask
app = Flask(__name__)
csrf = CSRFProtect(app)  # Proteger la aplicación contra ataques CSRF

# Configurar la base de datos MySQL
db = MySQL(app)

# Configurar el administrador de sesiones para Flask-Login
Login_manager_app = LoginManager(app)
Login_manager_app.login_view = "login"  # Redirigir a 'login' si el usuario no está autenticado

# Función de carga de usuario para Flask-Login
@Login_manager_app.user_loader
def load_user(id):
    return ModelUser.get_by_id(db, id)

# Ruta de la página principal, redirige a la página de inicio de sesión
@app.route('/')
def index():
    return redirect(url_for('login'))

# Ruta para la página de historia, accesible solo para usuarios autenticados
@app.route('/historia')
@login_required
def historia():
    return render_template('historia.html')

# Ruta para la página de inicio de sesión, maneja GET y POST
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Crear una instancia de User con los datos del formulario
        user = User(0, request.form['username'], request.form['password'])
        logged_user = ModelUser.login(db, user)  # Intentar autenticar al usuario

        if logged_user is not None:
            if logged_user.password:  # Verificar si la contraseña es correcta
                login_user(logged_user)  # Iniciar sesión para el usuario autenticado
                return redirect(url_for('home'))  # Redirigir a la página principal
            else:
                flash("Contraseña incorrecta...")  # Mensaje de error
                return render_template('auth/login.html')
        else:
            flash("Usuario no encontrado...")  # Mensaje de error
            return render_template('auth/login.html')
    else:
        return render_template('auth/login.html')

# Ruta para la página de estadísticas, accesible solo para usuarios autenticados
@app.route('/estadisticas')
@login_required
def estadisticas():
    cursor = db.connection.cursor()
    cursor.execute('SELECT check_in, check_out, room_type FROM reservations')
    reservations = cursor.fetchall()  # Obtener todas las reservas

    # Crear un diccionario para el conteo de ocupación por fecha
    occupancy = {date: 0 for date in pd.date_range(start='2024-01-01', end='2024-12-31')}

    for res in reservations:
        check_in, check_out, room_type = res
        for date in pd.date_range(start=check_in, end=check_out):
            occupancy[date] += 1  # Incrementar el conteo de ocupación para cada fecha en el rango

    dates = list(occupancy.keys())
    counts = list(occupancy.values())

    # Datos para las estadísticas adicionales
    df = pd.DataFrame(reservations, columns=['check_in', 'check_out', 'room_type'])
    df['check_in'] = pd.to_datetime(df['check_in'])
    df['check_out'] = pd.to_datetime(df['check_out'])

    # Calcular el mes con más reservas
    df['month'] = df['check_in'].dt.month
    month_counts = df['month'].value_counts()
    most_common_month = month_counts.idxmax()

    # Calcular la habitación más solicitada
    room_type_counts = df['room_type'].value_counts()
    most_requested_room = room_type_counts.idxmax()

    max_rooms = TOTAL_SIMPLE_ROOMS + TOTAL_DOUBLE_ROOMS
    colors = plt.cm.RdYlGn_r(np.linspace(0, 1, max_rooms + 1))

    plt.figure(figsize=(15, 7.5))  # Configurar el tamaño de la figura
    bars = plt.bar(dates, counts, color=[colors[min(count, max_rooms)] for count in counts], edgecolor='black')
    plt.xlabel('Fecha', fontsize=14)  # Etiqueta del eje X
    plt.ylabel('Número de Reservas', fontsize=14)  # Etiqueta del eje Y
    plt.title('Ocupación de Habitaciones por Día en 2024', fontsize=18)  # Título del gráfico

    img = io.BytesIO()
    plt.savefig(img, format='png')  # Guardar el gráfico en un objeto BytesIO
    img.seek(0)
    img_url = base64.b64encode(img.getvalue()).decode()  # Convertir la imagen a una cadena base64

    return render_template('estadisticas.html', img_url=f'data:image/png;base64,{img_url}', most_common_month=most_common_month, most_requested_room=most_requested_room)

# Definir el número total de habitaciones
TOTAL_SIMPLE_ROOMS = 10
TOTAL_DOUBLE_ROOMS = 5

# Ruta para la página de nueva reserva, accesible solo para usuarios autenticados
@app.route('/nuevareserva', methods=['GET', 'POST'])
@login_required
def nuevareserva():
    form = ReservationForm()
    available_rooms = ''
    if form.validate_on_submit():
        name = form.name.data
        room_type = form.room_type.data
        check_in = form.check_in.data
        check_out = form.check_out.data

        cursor = db.connection.cursor()
        cursor.execute('''SELECT COUNT(*) FROM reservations 
                          WHERE room_type = %s AND 
                                (check_in < %s AND check_out > %s)''', 
                       (room_type, check_out, check_in))
        booked_rooms = cursor.fetchone()[0]  # Contar las habitaciones reservadas
        max_rooms = 10 if room_type == 'sencilla' else 5  # Determinar el número máximo de habitaciones
        available_rooms = max_rooms - booked_rooms

        if booked_rooms >= max_rooms:
            flash('No hay habitaciones disponibles para el tipo y fechas seleccionadas', 'danger')  # Mensaje de error
        else:
            cursor.execute('''INSERT INTO reservations (user_id, name, room_type, check_in, check_out) 
                              VALUES (%s, %s, %s, %s, %s)''', 
                           (current_user.id, name, room_type, check_in, check_out))
            db.connection.commit()
            flash('Reserva realizada exitosamente', 'success')  # Mensaje de éxito
            return redirect(url_for('reservations'))
    
    return render_template('nuevareserva.html', form=form, available_rooms=available_rooms)

# Ruta para verificar la disponibilidad de habitaciones por día en un mes
@app.route('/check_availability', methods=['GET'])
def check_availability():
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)

    if not (1 <= month <= 12):
        return jsonify({'error': 'Invalid month'}), 400  # Validación del mes

    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year
    
    first_day = datetime(year, month, 1).date()
    last_day = datetime(next_year, next_month, 1).date() - timedelta(days=1)

    # Obtener las reservas para el mes
    cursor = db.connection.cursor()
    query = '''
        SELECT check_in, check_out 
        FROM reservations 
        WHERE check_in < %s AND check_out >= %s
    '''
    cursor.execute(query, (last_day, first_day))
    reservations = cursor.fetchall()
    cursor.close()
    
    # Diccionario de disponibilidad
    days_in_month = (last_day - first_day).days + 1
    availability = {day: 0 for day in range(1, days_in_month + 1)}
    
    # Actualizar la disponibilidad
    for reservation in reservations:
        check_in = reservation[0]
        check_out = reservation[1]
        
        start_day = max(check_in, first_day)
        end_day = min(check_out, last_day)
        
        if start_day <= end_day:
            for day in range((start_day - first_day).days + 1, (end_day - first_day).days + 2):
                if day in availability:
                    availability[day] += 1
    
    # Definir el límite de habitaciones disponibles para cambiar los colores
    max_rooms = 15
    availability = {day: (max_rooms - count) for day, count in availability.items()}
    
    return jsonify(availability)

# Ruta para verificar la disponibilidad de habitaciones de un tipo específico
@app.route('/check_available_rooms')
@login_required
def check_available_rooms():
    room_type = request.args.get('room_type')
    check_in = request.args.get('check_in')
    check_out = request.args.get('check_out')

    cursor = db.connection.cursor()
    cursor.execute('''SELECT COUNT(*) FROM reservations 
                      WHERE room_type = %s AND 
                            (check_in < %s AND check_out > %s)''',
                   (room_type, check_out, check_in))
    booked_rooms = cursor.fetchone()[0]
    max_rooms = 10 if room_type == 'sencilla' else 5  # Determinar el número máximo de habitaciones

    available_rooms = max_rooms - booked_rooms
    return jsonify(available_rooms=available_rooms)

# Ruta para eliminar una reserva específica
@app.route('/delete_reservation/<int:reservation_id>')
@login_required
def delete_reservation(reservation_id):
    cursor = db.connection.cursor()
    cursor.execute('DELETE FROM reservations WHERE id = %s', (reservation_id,))
    db.connection.commit()
    cursor.close()
    return redirect('/reservas')

# Ruta para la página de reservas del usuario autenticado
@app.route('/reservas')
@login_required
def reservations():
    cursor = db.connection.cursor()
    cursor.execute('SELECT * FROM reservations WHERE user_id = %s', (current_user.id,))
    reservations = cursor.fetchall()
    return render_template('reservas.html', reservations=reservations)

# Ruta para la página de registro de nuevos usuarios
@app.route('/nuevousuario', methods=['GET', 'POST'])
def nuevousuario():
    form = UsuarioForm()
    if form.validate_on_submit():
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        fullname = request.form['fullname']

        cursor = db.connection.cursor()
        cursor.execute('INSERT INTO user (username, password, fullname) VALUES (%s, %s, %s)', (username, password, fullname))
        db.connection.commit()
        return redirect('/login')
    
    return render_template('nuevousuario.html', form=form)

# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    logout_user()
    return render_template('auth/login.html')

# Ruta para la página de inicio, accesible solo para usuarios autenticados
@app.route('/home')
@login_required
def home():
    return render_template('home.html')

# Ruta para la página de contacto, accesible solo para usuarios autenticados
@app.route('/contacto')
@login_required
def contacto():
    return render_template('contacto.html')

# Ruta para la página de fotos, accesible solo para usuarios autenticados
@app.route('/fotos')
@login_required
def fotos():
    return render_template('fotos.html')

# Función para manejar errores 401 (no autorizado)
def status_401(error):
    return render_template('auth/login.html')

# Función para imprimir los parámetros de la solicitud
def query_string():
    print(request)
    print(request.args)
    print(request.args.get('param1'))
    return "ok"

# Función para manejar errores 404 (página no encontrada)
def pagina_no_encontrada(error):
    return render_template('404.html'), 404

# Ejecutar la aplicación Flask
if __name__ == '__main__':
    app.config.from_object(config['development'])  # Configurar la aplicación con los ajustes de desarrollo
    app.add_url_rule('/query_string', view_func=query_string)  # Añadir una ruta para prueba
    app.register_error_handler(404, pagina_no_encontrada)  # Registrar manejador de errores 404
    app.register_error_handler(401, status_401)  # Registrar manejador de errores 401
    app.run(port=5000)  # Ejecutar la aplicación en el puerto 5000