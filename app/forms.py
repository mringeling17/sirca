from flask_wtf import Form
from wtforms import StringField, PasswordField, validators
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Email

class ForgotForm(Form):
    email = EmailField('Email Address', [validators.data_required(), validators.email()])

class PasswordResetForm(Form):
    current_password = PasswordField('Current Password', [validators.DataRequired(), validators.length(min=6, max=80)])