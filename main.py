import os
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, flash, request, send_file
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, JSON, Boolean, and_
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from forms import RegisterForm, LoginForm, DishForm, IngredientForm, CategoryForm, WeeklyForm
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
import random
import base64
import json
import pyperclip
from fpdf import FPDF

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

INGREDIENTS: dict = {}
FOOD_DICT: dict = {}

TRANS_DICT = {
    "rice": "Reis",
    "noodle": "Nudeln",
    "vegetarian": "Vegetarisch",
    "vegetables": "Gemüse",
    "chicken": "Huhn",
    "pork": "Schwein",
    "beef": "Rind",
}

WEEK_DICT = {
    "Mo": 1,
    "Di": 2,
    "Mi": 3,
    "Do": 4,
    "Fr": 5,
    "Sa": 6,
    "So": 7,
}

WEEK_DICT_INVER = {str(v): k for k, v in WEEK_DICT.items()}
PDF_PATH = "static/assets/pdf/Einkaufsliste.pdf"

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
Bootstrap5(app)


class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///food.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)


class Dish(db.Model):
    __tablename__ = "dish"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="dishes")

    name: Mapped[str] = mapped_column(String(250), nullable=False)
    created_on: Mapped[str] = mapped_column(String(250), nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    ingredients: Mapped[dict[str, tuple[float | int, str]]] = mapped_column(JSON, nullable=False)
    ingredient_count: Mapped[int] = mapped_column(Integer, nullable=False)

    rice: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    noodle: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    vegetarian: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    vegetables: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    chicken: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    pork: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    beef: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))
    dishes = relationship("Dish", back_populates="author")


with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("all_dishes"))
    else:
        return redirect(url_for("login"))


@app.route("/all-dishes")
def all_dishes():
    flash(request.args.get("message"))

    result = db.session.execute(db.select(Dish).where(Dish.author == current_user))
    dishes = result.scalars().all()

    return render_template("all_dishes.html", dishes=dishes)


@app.route("/weekly-dishes-form", methods=["POST", "GET"])
def weekly_dishes_form():
    form = WeeklyForm()

    if form.validate_on_submit():
        FOOD_DICT.clear()

        start = WEEK_DICT[form.start.data]
        end = WEEK_DICT[form.end.data]
        vegetarian_days = int(form.vegetarian_days.data)

        if start < end:
            days = end - start + 1
        elif start > end:
            days = 7 - start + end + 1
        else:
            days = 7

        if vegetarian_days >= days:
            vegetarian_days = days

        result = db.session.execute(db.select(Dish).where(and_(Dish.author == current_user, Dish.vegetarian)))
        vegetarian_dishes = result.scalars().all()

        if not len(vegetarian_dishes) >= vegetarian_days:
            vegetarian_days = len(vegetarian_dishes)
            flash("Nicht genug vegetarische Gerichte! Fehlende Gerichte wurden mit nicht vegetarischen ersetzt.")

        vegetarian_choices = random.sample(vegetarian_dishes, k=vegetarian_days)

        if vegetarian_days == 0:

            result = db.session.execute(db.select(Dish).where(and_(Dish.author == current_user, Dish.vegetarian == False)))
            dishes = result.scalars().all()

            if not len(dishes) >= days:
                flash("Nicht genügend Gerichte in der Datenbank! Bitte füge mehr Gericht hinzu oder reduziere die Tage.")
                return render_template("weekly_dish_form.html", form=form)

            dish_choice = random.sample(dishes, k=days)

            for i in range(0, days):
                FOOD_DICT[str(i + start)] = dish_choice[i]

        elif days != vegetarian_days:

            result = db.session.execute(db.select(Dish).where(Dish.author == current_user))
            dishes = result.scalars().all()

            dishes = [item for item in dishes if item not in vegetarian_choices]

            if not len(dishes) >= days:
                flash("Nicht genügend Gerichte in der Datenbank! Bitte füge mehr Gericht hinzu oder reduziere die Tage.")
                return render_template("weekly_dish_form.html", form=form)

            no_vegetarian_choices = random.sample(dishes, k=days-vegetarian_days)

            vegetarian_weekdays: list = random.sample(range(start, start + days), k=vegetarian_days)

            iter_vegetarian_choices = iter(vegetarian_choices)

            iter_no_vegetarian_choices = iter(no_vegetarian_choices)

            for i in range(start, start + days):
                if i in vegetarian_weekdays:
                    cur_dish = next(iter_vegetarian_choices)
                else:
                    cur_dish = next(iter_no_vegetarian_choices)

                FOOD_DICT[str(i)] = cur_dish

        else:
            for i in range(0, days):
                FOOD_DICT[str(i + start)] = vegetarian_choices[i]

        return redirect(url_for('weekly_dishes'))

    return render_template("weekly_dish_form.html", form=form)


@app.route("/replace-weekly-dish")
def replace_weekly_dish():

    dish_id = request.args.get("dish_id")

    dish_to_replace = db.get_or_404(Dish, dish_id)

    if dish_to_replace.vegetarian:
        result = db.session.execute(db.select(Dish).where(and_(Dish.author == current_user, Dish.vegetarian)))
        dishes = result.scalars().all()
        veggie = True

    else:
        result = db.session.execute(db.select(Dish).where(and_(Dish.author == current_user, Dish.vegetarian == False)))
        dishes = result.scalars().all()
        veggie = False

    dishes = [item for item in dishes if item.id not in [v.id for k, v in FOOD_DICT.items()]]

    if len(dishes) <= 0:
        if veggie:
            flash("Nicht genügend vegetarische Gerichte in der Datenbank!")
        else:
            flash("Nicht genügend nicht vegetarische Gerichte in der Datenbank!")
    else:
        for k, v in FOOD_DICT.items():
            if v.id == dish_to_replace.id:
                FOOD_DICT[k] = random.choice(dishes)

    return redirect(url_for('weekly_dishes'))


@app.route("/weekly-dishes")
def weekly_dishes():

    food_dict_trans = {WEEK_DICT_INVER[k]: v for k, v in FOOD_DICT.items()}

    return render_template("weekly_dishes.html", food_dict=food_dict_trans)


@app.route("/gen-shopping-list")
def gen_shopping_list():
    result = db.session.execute(db.select(Dish).where(Dish.author == current_user))
    dishes = result.scalars().all()

    dishes: list[Dish] = [item for item in dishes if item.id in [v.id for k, v in FOOD_DICT.items()]]

    ingredient_dict = {}

    for cur_dish in dishes:
        ingred: dict = cur_dish.ingredients
        for ingredient, value in ingred.items():
            if ingredient in ingredient_dict:
                ingred_value = ingredient_dict[ingredient]
                if ingred_value[1] == value[1]:
                    ingred_value[0] += value[0]
                else:
                    ingredient_dict[ingredient] = value
            else:
                ingredient_dict[ingredient] = value

    serialized_data = json.dumps(ingredient_dict)
    encoded_data = base64.urlsafe_b64encode(serialized_data.encode()).decode()

    return redirect(url_for("shopping_list", data=encoded_data))


@app.route("/shopping-list")
def shopping_list():
    encoded_data = request.args.get("data")
    if encoded_data:
        try:
            decoded_data = base64.urlsafe_b64decode(encoded_data).decode()
            ingredient_dict = json.loads(decoded_data)
        except Exception as e:
            return "Ungültige oder beschädigte Daten.", 400

    else:
        return "Einkaufsliste nicht vorhanden."

    return render_template("shopping_list.html", ingredient_dict=ingredient_dict, data=encoded_data)


@app.route("/share")
def share_shopping_list():
    encoded_data = request.args.get("data")
    shareable_link = f"{request.host_url}shopping-list?data={encoded_data}"
    pyperclip.copy(shareable_link)
    flash("Link Erfolgreich kopiert.")
    return redirect(url_for("shopping_list", data=encoded_data))


@app.route("/gen-pdf")
def gen_pdf_shopping_list():
    encoded_data = request.args.get("data")
    if encoded_data:
        try:
            decoded_data = base64.urlsafe_b64decode(encoded_data).decode()
            ingredient_dict: dict = json.loads(decoded_data)
        except Exception as e:
            return "Ungültige oder beschädigte Daten.", 400
    else:
        return "Einkaufsliste nicht vorhanden."

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=15)

    line_count = 1

    pdf.cell(200, 10, txt="Einkaufsliste",
             ln=line_count, align='C')

    for k, v in ingredient_dict.items():
        line_count += 1

        line = f"{k}_____________________________________________________________{v[0]} {v[1]}"

        line = line.replace("_", "", len(k))
        line = line.replace("_", "", len(str(v[0])))
        line = line.replace("_", "", len(str(v[1])))

        pdf.cell(200, 10, txt=line,
                 ln=line_count, align='L')

    pdf.output(PDF_PATH)

    return send_file(PDF_PATH, as_attachment=True)


@app.route("/dish")
def dish():
    name = request.args.get("name")

    result = db.session.execute(db.select(Dish).where(and_(Dish.name == name), Dish.author == current_user))
    cur_dish = result.scalar()

    true_attributes = [
        attr for attr, value in vars(cur_dish).items() if value is True
    ]

    true_list = [TRANS_DICT[word] for word in true_attributes]

    cat_str = (str(true_list).replace("[", "(").replace("]", ")").replace("'", ""))

    return render_template("dish.html", dish=cur_dish, cat=cat_str)


@app.route("/add-dish", methods=["GET", "POST"])
def add_dish():
    form = DishForm()
    if form.validate_on_submit():
        name = form.name.data
        img_url = form.img_url.data

        result = db.session.execute(db.select(Dish).where(and_(Dish.name == name, Dish.author == current_user)))
        test = result.scalars().all()

        if not test:
            INGREDIENTS.clear()
            return redirect(url_for("add_ingredients", name=name, img_url=img_url, ingredients=INGREDIENTS))
        else:
            flash("Du hast schon ein Gericht mit diesem Namen.")
            return render_template("add_dish.html", form=form)

    return render_template("add_dish.html", form=form)


@app.route("/add-ingredients", methods=["GET", "POST"])
def add_ingredients():
    form = IngredientForm()
    name = request.args.get("name")
    img_url = request.args.get("img_url")

    if form.validate_on_submit():
        ingredient = form.ingredient_name.data
        amount = float(form.amount.data)
        unit = form.unit.data

        INGREDIENTS[ingredient.title()] = (amount, unit)

        return redirect(url_for("add_ingredients", name=name, img_url=img_url, ingredients=INGREDIENTS))

    return render_template("add_ingredients.html", form=form, name=name, img_url=img_url, ingredients=INGREDIENTS)


@app.route("/add-category", methods=["GET", "POST"])
def add_category():

    if not INGREDIENTS:
        flash("Füge mindestens eine Zutat hinzu.")
        return redirect(url_for('add_ingredients'))

    form = CategoryForm()
    name = request.args.get("name")
    img_url = request.args.get("img_url")

    if form.validate_on_submit():

        if form.vegetarian.data:
            if form.chicken.data or form.pork.data or form.beef.data:
                flash("Gericht kann nicht vegetarisch mit Fleisch sein!")
                return render_template("add_category.html", form=form, name=name)

        new_dish = Dish(
            name=name,
            created_on=date.today().strftime("%d.%m.%Y"),
            img_url=img_url,
            ingredients=INGREDIENTS,
            author=current_user,
            ingredient_count=len(INGREDIENTS),
            rice=form.rice.data,
            noodle=form.noodle.data,
            vegetarian=form.vegetarian.data,
            vegetables=form.vegetables.data,
            chicken=form.chicken.data,
            pork=form.pork.data,
            beef=form.beef.data,
        )

        db.session.add(new_dish)
        db.session.commit()

        return redirect(url_for("all_dishes", message="Gericht hinzugefügt."))

    return render_template("add_category.html", form=form, name=name)


@app.route("/delete")
def delete_dish():
    dish_id = request.args.get("id")
    dish_to_del = db.get_or_404(Dish, dish_id)
    db.session.delete(dish_to_del)
    db.session.commit()

    return redirect(url_for("all_dishes"))


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():

        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        if user:
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for("home"))

    return render_template("register.html", form=form, current_user=current_user)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        password = form.password.data
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('home'))

    return render_template("login.html", form=form, current_user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)
