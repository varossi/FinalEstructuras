from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired

class UsuarioForm(FlaskForm):
    username = StringField('username', validators=[DataRequired()])
    password = StringField('password', validators=[DataRequired()])
    fullname = StringField('fullname', validators=[DataRequired()])

