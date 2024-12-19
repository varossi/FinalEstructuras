from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, ValidationError

def validate_username(form, field):
    if field.data.upper() == 'ADMIN':
        raise ValidationError('El nombre de usuario "admin" no está permitido.')

class UsuarioForm(FlaskForm):
    username = StringField('username', validators=[DataRequired(), validate_username])
    password = StringField('password', validators=[DataRequired()])
    fullname = StringField('fullname', validators=[DataRequired()])

