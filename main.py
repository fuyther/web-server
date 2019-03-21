from flask import Flask, render_template, redirect, request, session
import sqlite3
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email, Length
import random


def mailbot(email):
    print(email)
    number = random.randint(100, 999)
    print(number)
    return str(number)


class RegistrationForm(FlaskForm):
    nickname = StringField('Ник', validators=[DataRequired(), Length(min=1, max=20)])
    surname = StringField('Фамилия', validators=[DataRequired(), Length(min=1, max=30)])
    name = StringField('Имя', validators=[DataRequired(), Length(min=1, max=30)])
    email = StringField('Почта', validators=[DataRequired(), Email(), Length(min=6, max=100)])
    password = PasswordField('Пароль (больше 8 знаков)', validators=[DataRequired(), Length(min=8, max=128)])
    password_valid = PasswordField('Подтверждение пароля', validators=[DataRequired(), Length(min=8, max=128)])
    registration = SubmitField('Верифицировать')


class ValidationForm(FlaskForm):
    code = StringField('Введите код высланный вам на почту', validators=[DataRequired(), Length(min=3, max=5)])
    validation = SubmitField('Отправить')


class LoginForm(FlaskForm):
    nickname = StringField('Ник', validators=[DataRequired(), Length(min=1, max=20)])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=8, max=128)])
    login = SubmitField('Войти')


class TournamentForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired(), Length(min=1, max=50)])
    size = StringField('Размер', validators=[DataRequired()])
    create = SubmitField('Создать')


class SettingForm(FlaskForm):
    nickname = StringField('Ник', validators=[DataRequired(), Length(min=1, max=20)])
    surname = StringField('Фамилия', validators=[DataRequired(), Length(min=1, max=30)])
    name = StringField('Имя', validators=[DataRequired(), Length(min=1, max=30)])
    email = StringField('Почта', validators=[DataRequired(), Email(), Length(min=6, max=100)])
    password = PasswordField('Пароль (больше 8 знаков)', validators=[DataRequired(), Length(min=8, max=128)])
    submit = SubmitField('Поменять')


class DB:
    def __init__(self):
        conn = sqlite3.connect('users.db', check_same_thread=False)
        self.conn = conn

    def get_connection(self):
        return self.conn

    def __del__(self):
        self.conn.close()


class UsersModel:
    def __init__(self, connection):
        self.connection = connection

    def init_table(self):
        cursor = self.connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                             nickname VARCHAR(20),
                             surname VARCHAR(30),
                             name VARCHAR(30), 
                             email VARCHAR(100),
                             password VARCHAR(128),
                             tournaments VARCHAR(300)
                             )''')
        cursor.close()
        self.connection.commit()

    def insert(self, nickname, surname, name, email,  password):
        cursor = self.connection.cursor()
        cursor.execute('''INSERT INTO users 
                          (nickname, surname, name, email, password, tournaments) 
                          VALUES (?,?,?,?,?)''', (nickname, surname, name, email, password, []))
        cursor.close()
        self.connection.commit()

    def insert_tournament(self, tournament):
        cursor = self.connection.cursor()
        cursor.execute('''INSERT INTO tournaments FROM users WHERE id=(?) 
                                  VALUES (?)''', str(self.get(session['id']), tournament))
        cursor.close()
        self.connection.commit()

    def get(self, user_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (str(user_id),))
        row = cursor.fetchone()
        return row

    def get_by_id(self, nickname, password):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE nickname = ? AND password = ?", (str(nickname), str(password)))
        row = cursor.fetchone()
        return row

    def get_mail(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT email FROM users WHERE id = (SELECT MAX(ID) FROM users)")
        row = cursor.fetchone()
        return row

    def get_password(self, nickname):
        cursor = self.connection.cursor()
        cursor.execute("SELECT password FROM users WHERE nickname = ?", (str(nickname),))
        row = cursor.fetchone()
        return row

    def get_all(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        return rows

    def exists(self, nickname, password):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE nickname = ? AND password = ?",
                       (nickname, password))
        row = cursor.fetchone()
        return (True, row[0]) if row else (False,)

    def update(self, id, target, value):
        cursor = self.connection.cursor()
        cursor.execute('''UPDATE users SET  (?) = ? WHERE id = ?''', (target, str(value), str(id)))
        cursor.close()
        self.connection.commit()

    def delete(self, id):
        cursor = self.connection.cursor()
        cursor.execute('''DELETE FROM users WHERE id = ?''', (str(id),))
        cursor.close()
        self.connection.commit()


class TournsModel:
    def __init__(self, connection):
        self.connection = connection

    def init_table(self):
        cursor = self.connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS tournaments 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                             name VARCHAR(50),
                             size INTEGER,
                             creator INTEGER,
                              player VARCHAR(150)
                             )''')
        cursor.close()
        self.connection.commit()

    def create(self, name, size, creator):
        cursor = self.connection.cursor()
        cursor.execute('''INSERT INTO tournaments 
                          (name, size, creator, player) 
                          VALUES (?,?,?,?)''', (name, size, creator, ""))
        cursor.close()
        self.connection.commit()

    def get(self, tournamentId):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM tournaments WHERE id = ?", (str(tournamentId),))
        row = cursor.fetchone()
        return row

    def get_all(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM tournaments")
        rows = cursor.fetchall()
        return rows

    def get_tourns_by_creator(self, creator):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM tournaments WHERE creator = ?", (str(creator)))
        rows = cursor.fetchall()
        return rows

    def exists(self, name):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM tournaments WHERE name = ?",
                       (name,))
        row = cursor.fetchone()
        return (True, row[0]) if row else (False,)

    def update(self, id, target, value):
        cursor = self.connection.cursor()
        cursor.execute('''UPDATE tournaments SET  (?) = ? WHERE id = ?''', (target, str(value), str(id)))
        cursor.close()
        self.connection.commit()

    def insert_player(self, tournamentId, playerId):
        tr = self.get(tournamentId)
        self.update(tournamentId, 'player', tr[4] + " " + str(playerId))

    def get_players(self, tId):
        tr = self.get(tId)
        return tr[4].split()

    def delete(self, id):
        cursor = self.connection.cursor()
        cursor.execute('''DELETE FROM tournaments WHERE id = ?''', (str(id),))
        cursor.close()
        self.connection.commit()


db = DB()
users_model = UsersModel(db.get_connection())
users_model.init_table()
tourns_model = TournsModel(db.get_connection())
tourns_model.init_table()
app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


def check():
    if 'user' in session:
        return True
    return False


@app.route('/', methods=['GET', 'POST'])
def main():
    if 'user' in session:
        return redirect('/mypage')
    form = LoginForm()
    user_name = form.nickname.data
    password = form.password.data
    session['user'] = user_name
    user = users_model.get_by_id(user_name, password)
    if user:
        session['id'] = user[0]
    exists = users_model.exists(user_name, password)
    if exists[0] and form.validate_on_submit():
        return redirect('/mypage')
    return render_template('main.html', title='Главная', form=form)


@app.route('/registration', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        users_model.insert(request.form['nickname'], request.form['name'], request.form['surname'],
                           request.form['email'], request.form['password'])
        return redirect('/validation')
    return render_template('regform.html', title='Регистрация', form=form)


code = mailbot(users_model.get_mail())
print(code)


@app.route('/validation', methods=['GET', 'POST'])
def validation():
    form = ValidationForm()
    if form.validate_on_submit() and \
            request.form['code'] == code:
        return redirect('/')
    return render_template('validation.html', title='Верификация', form=form)


@app.route('/mypage', methods=['GET', 'POST'])
def logged():
    if 'user' in session:
        return render_template('mypage.html', title='account')
    else:
        return redirect('/')


@app.route('/tournaments')
def tournaments():
    if not check():
        return redirect('/')
    return render_template('tournaments.html', title='Tournaments')


@app.route('/tournaments/create', methods=['GET', 'POST'])
def tourn_creation():
    if not check():
        return redirect('/')
    form = TournamentForm()
    name = form.name.data
    size = form.size.data
    print("here")
    if request.method == 'POST':
        print('created')
        tourns_model.create(name, size, session['user'])
        return redirect('/tournaments')
    return render_template('tourn_creation.html', title='Tournaments Creation', form=form)


@app.route('/tournaments/<int:id>')
def tournament(id):
    tr = tourns_model.get(id)[4]
    tr_name = []
    for player in tr:
        tr_name.append((player, users_model.get(player)[1]))
    return render_template('tournament.html', tr=tr_name)


@app.route('/settings')
def settings():
    if not check():
        return redirect('/')
    form = SettingForm()
    if form.validate_on_submit():
        id = session['id']
        users_model.update(id, 'nickname', form.nickname.data)
        users_model.update(id, 'surname', form.surname.data)
        users_model.update(id, 'name', form.name.data)
        users_model.update(id, 'email', form.email.data)
        users_model.update(id, 'password', form.password.data)
        return redirect('/mypage')
    return render_template('settings.html', form=form)


@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('password', None)
    return redirect('/')


print(users_model.get_all())
print(tourns_model.get_all())

if __name__ == "__main__":
    app.run("localhost", port=31173)
