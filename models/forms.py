from flask_wtf import FlaskForm
from wtforms import StringField, DateField
from wtforms.validators import DataRequired

class ReservationForm(FlaskForm):
    name = StringField('Nombre', validators=[DataRequired()])
    room_type = StringField('Tipo de Habitación', validators=[DataRequired()])
    check_in = DateField('Fecha de Entrada', format='%Y-%m-%d', validators=[DataRequired()])
    check_out = DateField('Fecha de Salida', format='%Y-%m-%d', validators=[DataRequired()])
