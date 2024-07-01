from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField
from wtforms.validators import DataRequired, ValidationError

class ReservationForm(FlaskForm):
    name = StringField('Nombre', validators=[DataRequired()])
    room_type = SelectField('Tipo de Habitación', choices=[('sencilla', 'Sencilla'), ('doble', 'Doble')], validators=[DataRequired()], render_kw={"class": "form-control"})
    check_in = DateField('Fecha de Entrada', format='%Y-%m-%d', validators=[DataRequired()])
    check_out = DateField('Fecha de Salida', format='%Y-%m-%d', validators=[DataRequired()])

    def validate_check_out(self, field):
        if field.data <= self.check_in.data:
            raise ValidationError('La fecha de salida debe ser después de la fecha de entrada.')

