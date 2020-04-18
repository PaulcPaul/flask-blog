from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, ValidationError, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from flask_login import current_user

from mysite.models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', 
    validators=[DataRequired(), Length(min=2, max=20)])

    email = StringField('Email', 
    validators=[DataRequired(), Email()])

    password = PasswordField('Password', validators=[DataRequired()])

    confirm_password = PasswordField('Confirm Password', 
    validators=[DataRequired(), EqualTo('password')])

    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Um usuário com esse nome já existe.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Um usuário com esse e-mail já existe.')

class LoginForm(FlaskForm):
    email = StringField('Email', 
    validators=[DataRequired(), Email()])

    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')

    submit = SubmitField('Login')

class UpdateAccountForm(FlaskForm):
    username = StringField('Username', 
    validators=[DataRequired(), Length(min=2, max=20)])

    email = StringField('Email', 
    validators=[DataRequired(), Email()])

    picture = FileField('Imagem', 
    validators=[FileAllowed(['jpg', 'png'])])

    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Um usuário com esse nome já existe.')
    
    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Um usuário com esse e-mail já existe.')

class PostForm(FlaskForm):
    title = StringField('Título', validators=[DataRequired()])

    content = TextAreaField('Texto', validators=[DataRequired()])

    submit = SubmitField('Postar')

class RespostaForm(FlaskForm):
    content = TextAreaField('Responda', validators=[DataRequired()])

    submit = SubmitField('Responder')