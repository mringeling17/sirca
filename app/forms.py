from flask_wtf import Form
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email

class EmailForm(Form):
    email = TextField('Email', validators= [DataRequired(), Email()])

class PasswordForm(Form):
    email = TextField('Email', validators=[DataRequired(), Email()])