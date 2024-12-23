from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, DecimalField, SelectField, BooleanField
from wtforms.validators import DataRequired, URL


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])

    submit = SubmitField("Let Me In!")


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])

    submit = SubmitField("Sign Me Up!")


class DishForm(FlaskForm):
    name = StringField("Name des Gerichts", validators=[DataRequired()])
    img_url = StringField("Bild URL", validators=[DataRequired(), URL()])

    submit = SubmitField("Zutaten Hinzufügen")


class IngredientForm(FlaskForm):
    ingredient_name = StringField("Zutat", validators=[DataRequired()])
    amount = DecimalField("Menge", validators=[DataRequired()])
    unit = SelectField("Einheit", validators=[DataRequired()], choices=[("Stk"), ("ml"), ("kg"), ("g"), ("Pr"), ("El"), ("Tl")])

    submit = SubmitField("Zutat Hinzufügen")


class CategoryForm(FlaskForm):
    rice = BooleanField("Reis")
    noodle = BooleanField("Nudeln")
    vegetables = BooleanField("Gemüse")
    chicken = BooleanField("Huhn")
    pork = BooleanField("Schwein")
    beef = BooleanField("Rind")
    vegetarian = BooleanField("Vegetarisch")

    submit = SubmitField("Kategorien bestätigen")


class WeeklyForm(FlaskForm):
    start = SelectField("Von", validators=[DataRequired()], choices=[("Mo"), ("Di"), ("Mi"), ("Do"), ("Fr"), ("Sa"), ("So")])
    end = SelectField("Bis", validators=[DataRequired()], choices=[("Mo"), ("Di"), ("Mi"), ("Do"), ("Fr"), ("Sa"), ("So")])
    vegetarian_days = SelectField("Vegetarische Tage", validators=[DataRequired()], choices=[(0), (1), (2), (3), (4), (5), (6), (7)])

    submit = SubmitField("Essensplan erstellen")
