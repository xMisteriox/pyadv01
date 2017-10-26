from flask import Flask, render_template, request,\
    redirect, url_for, flash, abort
from flask_debugtoolbar import DebugToolbarExtension
from flask_login import LoginManager, \
    login_required, login_user, logout_user, UserMixin
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound

from shekels.forms import ExpenseForm, LoginForm, RegisterForm

import logging
import shekels.logger
shekels.logger.setup()

app = Flask(__name__)
app.secret_key = 'fdsafhsdalkghsdahg'
app.debug = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

toolbar = DebugToolbarExtension(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Log in please!"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../expense2.db'

db = SQLAlchemy(app)

migrate = Migrate(app, db)


class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String)
    full_name = db.Column(db.String)
    password = db.Column(db.String)

    # = db.relationship("Child", back_populates="parent")

    def __str__(self):
        return "User: {} {}".format(self.login,
                                    self.full_name)


class Expense(db.Model):
    __tablename__ = 'expense'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    price = db.Column(db.Integer)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                        nullable=False)
    user = db.relationship("User", backref="expenses")


@login_manager.user_loader
def load_user(id):
    return db.session.query(User).get(id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = db.session.query(User).filter(
                User.login == form.login.data
            ).one()
        except NoResultFound:
            flash(message='bad login')
        else:
            if user.password == form.password.data:
                login_user(user)
                flash('Welcome {}!'.format(user.login))
                app.logger.log(10, 'Logged user {}'.format(user.login))
                next = request.args.get('next')
                return redirect(next or url_for('index'))
            else:
                flash(message='bad login')
    return render_template('login.html', form=form)


@app.route('/')
def index():
    logging.info('hello')
    return render_template('index.html')


@app.route('/hello')
@login_required
def user_list():
    logging.info('DUPA')
    query = db.session.query(User)
    if 'name' in request.args:
        name = '%{}%'.format(request.args['name'])
        query = query.filter(User.name.like(name))

    user_list = query.all()

    return render_template('user_list.html', users=user_list)


@app.route('/list')
@login_required
def list():
    expenses = db.session.query(Expense).all()
    return render_template('list.html',
                           expenses=expenses)


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    form = ExpenseForm()
    if form.validate_on_submit():
        expense = Expense(
            name=form.name.data,
            price=form.price.data
        )
        db.session.add(expense)
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('add.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            login=form.login.data,
            full_name=form.full_name.data,
            password=form.password.data
        )
        db.session.add(user)
        db.session.commit()
        flash('User registered {}! Please log in.'.format(user.login))
        return redirect(url_for('index'))

    return render_template('register.html', form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
