from flask import Flask, render_template, url_for, request, redirect,flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc
import schedule
import time 
import threading
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, ValidationError
from wtforms.validators import InputRequired, Email, Length, email_validator
import phonenumbers
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from alert_program import email_alerts as e_alerts, phone_alerts as p_alerts


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user-tasks.db'
db = SQLAlchemy(app)
Bootstrap(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'



#===================== CLASSES ======================
class Loginform(FlaskForm):
	username = StringField('Username:', validators = [InputRequired(), Length(min = 4, max = 15)])
	password = PasswordField('Password:', validators = [InputRequired(), Length(min=6, max = 80)])
	remember_me = BooleanField('Remember me')

class Registerform(FlaskForm):
	password = PasswordField('Password', validators = [InputRequired(),Length(min=6, max = 80)])
	username = StringField('Username', validators = [InputRequired(),Length(min = 4, max = 15)] )
	email = StringField('Email', validators = [InputRequired(), Email(message = 'Invalid email'), Length(min = 6, max = 50)])
	phone = StringField('Phone (optional)')

	def validate_phone(form, field):
		if len(field.data) > 16 and len(field.data) < 10:
			flash('Invalid phone number.')
			return redirect('/signup')
		elif len(field.data) == 0:
			return
		try:
			input_number = phonenumbers.parse(field.data)
			if not (phonenumbers.is_valid_number(input_number)):
				flash('Invalid phone number.')
				return redirect('/signup')
		except phonenumbers.NumberParseException:
			input_number = phonenumbers.parse("+1"+field.data)
			if not (phonenumbers.is_valid_number(input_number)):
				flash('Invalid phone number.')
				return redirect('/signup')

class Settingsform(FlaskForm):
	username = StringField('Username', validators = [Length(min = 4, max = 15)])
	email= StringField('Email', validators = [Length(min = 6, max = 50), Email(message = 'Invalid email.')])
	curr_password = PasswordField('Current Password', validators = [Length(min=6, max = 80)])
	new_password = PasswordField('New Password', validators = [Length(min=6, max = 80)])
	confirm_password = PasswordField('Confirm Password', validators = [Length(min=6, max = 80)])
	phone = StringField('Phone')

	def validate_phone(form, field):
		if len(field.data) > 16 and len(field.data) < 10:
			flash('Invalid phone number.')
			return redirect('/settings')
		elif len(field.data) == 0:
			return
		try:
			input_number = phonenumbers.parse(field.data)
			if not (phonenumbers.is_valid_number(input_number)):
				flash('Invalid phone number.')
				return redirect('/settings')
		except:

			input_number = phonenumbers.parse("+1"+field.data)
			if not (phonenumbers.is_valid_number(input_number)):
				flash('Invalid phone number.')
				return redirect('/settings')


				
class User(UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(15), unique = True)
	email = db.Column(db.String(50), unique = True)
	password = db.Column(db.String(80))
	phone = db.Column(db.String(16))
	email_alert = db.Column(db.Boolean)
	phone_alert = db.Column(db.Boolean)
	alert_start_hr = db.Column(db.Integer)
	alert_start_min = db.Column(db.String(2))
	alert_TOD = db.Column(db.Boolean)
	tasks = db.relationship('Tasks', backref = 'owner')

	def __repr__(self):
		return '<User %r>' % self.id

class Tasks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    complete = db.Column(db.Boolean)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Task %r>' % self.id



@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))



#======================= ROUTES ============================
@app.route('/', methods = ['POST', 'GET'])
def index():
	if request.method == 'POST':
		name = request.form['name']
		email = request.form['email']
		subj = request.form['subject']
		mess = request.form['message']
		body = f'Name: {name} \nEmail: {email} \n\n\n{mess}'
		e_alerts(subj, body, 'jfetero@hawk.iit.edu')
		return render_template('index.html', success = True)
	else:
		return render_template('index.html')
	

@app.route('/contact_me', methods = ['POST', 'GET'])
@login_required
def contact_me():

	if request.method == 'POST':
		name = request.form['name']
		email = request.form['email']
		subj = request.form['subject']
		mess = request.form['message']
		body = f'Name: {name} \nEmail: {email} \n\n\n{mess}'
		e_alerts(subj, body, 'jfetero@hawk.iit.edu')
		return render_template('contact_me.html', success = True, name = current_user.username)
	else:
		return render_template('contact_me.html', name = current_user.username )


@app.route('/settings', methods = ['POST', 'GET'])
@login_required
def settings():
	form = Settingsform()
	if request.method == "POST":
		user = User.query.filter_by(id = current_user.id).first()
		#--------Info --------
		if user.username != form.username.data and len(form.username.data)>4 and len(form.username.data)<15:
			user.username = form.username.data
			try:
				db.session.commit()
				flash('Changes Saved.')
			except exc.IntegrityError:
				flash('Username Already in Use.')
				return redirect('/settings')

		if user.email != form.email.data and len(form.email.data)>6 and len(form.username.data)<50 :
			user.email = form.email.data
			try:
				db.session.commit()
				flash('Changes Saved.')
				return redirect('/settings')
			except exc.IntegrityError:
				flash('Invalid Email.')
				return redirect('/settings')

		if user.phone != form.phone.data and len(form.phone.data) >= 10:
			user.phone = form.phone.data
			try:
				db.session.commit()
				flash('Changes Saved.')
			except:
				flash('Invalid Phone Number.')
				return redirect('/settings')


		#---------password--------
		curr_password = form.curr_password.data
		new_password = form.new_password.data
		confirm_password = form.confirm_password.data

		if check_password_hash(user.password, form.curr_password.data) and len(form.curr_password.data) > 6 and len(form.curr_password.data)<80 :
			if form.new_password.data == form.confirm_password.data:
				user.password = generate_password_hash(form.new_password.data, method = 'sha256')
				try:
					db.session.commit()
					flash('Changes Saved.')
				except:
					flash('Please Try Again.')
					return redirect('/settings')
			else:
				flash('Passwords Do Not Match.')
				return redirect('/settings')
		elif not check_password_hash(user.password, form.curr_password.data) and len(form.curr_password.data) > 6 and len(form.curr_password.data)<80:
			flash('Incorrect Password.')
			return redirect('/settings')
		else:
			try:
				db.session.commit()
				flash('Changes Saved.')
			except:
				flash('Please Try Again.')
				return redirect('/settings')

		#--------Alerts---------
		try:
			if request.form['email_alert']:
				user.email_alert = True
				try:
					db.session.commit()
					
				except:
					return redirect('/settings')
		except:
			user.email_alert = False
			try:
				db.session.commit()
				
			except:
				return redirect('/settings')

		try:
			if request.form['phone_alert']:
				user.phone_alert = True
				try:
					db.session.commit()
					
				except:
					return redirect('/settings')
		except:
			user.phone_alert = False
			try:
				db.session.commit()
			except:
				return redirect('/settings')

		if request.form['alert_start_hr'] != user.alert_start_hr:
			user.alert_start_hr = request.form['alert_start_hr'] 
			try:
				db.session.commit()
			except:
				return redirect('/settings')

		if request.form['alert_start_min'] != user.alert_start_min:
			user.alert_start_min = request.form['alert_start_min'] 
			try:
				db.session.commit()
			except:
				return redirect('/settings')

		if request.form['alert_TOD'] == 'A.M':
			user.alert_TOD = False
			try:
				db.session.commit()
			except:
				return redirect('/settings')
		else:
			user.alert_TOD = True
			try:
				db.session.commit()
			except:
				return redirect('/settings')

		return redirect('/settings')
	else:
		content = {
			'name' : current_user.username,
			'email': current_user.email,
			'phone': current_user.phone,
			'phone_alert': current_user.phone_alert,
			'email_alert': current_user.email_alert,
			'alert_start_hr' : current_user.alert_start_hr,
			'alert_start_min' : current_user.alert_start_min,
			'alert_TOD': current_user.alert_TOD,
			'form' : form
		}
		return render_template('settings.html', **content)


@app.route('/login', methods = ['POST', 'GET'])
def login():
	form = Loginform()

	if form.validate_on_submit():
		user = User.query.filter_by(username = form.username.data).first()
		if user:
			if check_password_hash(user.password, form.password.data):
				login_user(user, remember = form.remember_me.data)
				return redirect('/dashboard')
		flash('Incorrect Username or Password')

	return render_template('login.html', form = form)

@app.route('/signup', methods = ['POST', 'GET'])
def signup():
	form = Registerform()
	if form.validate_on_submit():
		user = form.username.data
		em = form.email.data
		hashed = generate_password_hash(form.password.data, method = 'sha256')
		new_user = User(username = user, email = em, password = hashed, phone = form.phone.data, email_alert = False, phone_alert = False, alert_start_hr = 10, alert_start_min = '00', alert_TOD = False )
		try:	
			db.session.add(new_user)
			db.session.commit()
			_user = User.query.filter_by(username = user).first()
			login_user(_user)
			return redirect('/dashboard')
		except exc.IntegrityError:
			flash('Username or Email Already in Use')
		except phonenumbers.NumberParseException:
			flash('Invalid Phone')
			
	return render_template('signup.html', form = form)

@app.route('/dashboard', methods = ['POST', 'GET'])
@login_required
def dashboard():
	if request.method == 'POST':
		task_content = request.form['content']
		new_task = Tasks(content=task_content, complete = False, owner = current_user)

		try:
			db.session.add(new_task)
			db.session.commit()
			return redirect('/dashboard')
		except:
			return 'There was an issue adding your task'
	else:
		tasks = current_user.tasks
		return render_template('dashboard.html', tasks = tasks, name = current_user.username)

@app.route('/logout')
@login_required
def logout():
	logout_user()
	flash('Log out Successful.')
	return redirect(url_for('login'))


@app.route('/delete/<int:id>')
def delete(id):
    task_to_delete = Tasks.query.get_or_404(id)

    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/dashboard')
    except:
        return 'There was a problem deleting that task'

@app.route('/update/<int:id>')
def update(id):
	task = Tasks.query.get_or_404(id)
	task.complete = not task.complete
	try:
		db.session.commit()
		return redirect('/dashboard')
	except:
		return 'There was an issue updating your task'
	else:
		return render_template('dashboard.html')

def send_alerts():
	'''
		Background Process handled by threads
	'''
	users = User.query.filter_by(email_alert = True, phone_alert =True).all()

	for user in users:
		email = user.email
		phone = ''.join([i for i in user.phone if i !='-'])
		tasks = '\n'.join([task.content for task in user.tasks if task.complete == False])
		if user.alert_TOD == False and user.alert_start_hr == 12:
			start = f'00:{user.alert_start_min}'
		elif user.alert_TOD == False:
			if user.alert_start < 10:
				start = f'0{user.alert_start}:{user.alert_start_min}'
			else:
				start = f'{user.alert_start}:{user.alert_start_min}'
		elif user.alert_TOD == True and user.alert_start_hr == 12:
			start = f'12:{user.alert_start_min}'
		elif user.alert_TOD:
			start = str(user.alert_start_hr + 12)
			start = f'{start}:{user.alert_start_min}'
		

		if user.phone_alert and user.email_alert:
			schedule.every().day.at(f'{start}').do(lambda: e_alerts('To-do', tasks, email))
			schedule.every().day.at(f'{start}').do(lambda: p_alerts(phone, 'To-Do', tasks))
		elif user.email_alert and not user.phone_alert:
			schedule.every().day.at(f'{start}').do(lambda: e_alerts('To-Do', tasks, email))
		elif user.phone_alert and not user.email_alert:
			schedule.every().day.at(f'{start}').do(lambda: p_alerts(phone, 'To-Do', tasks))

	
		while True:
			schedule.run_pending()
			time.sleep(1)
			


threading.Thread(target=send_alerts).start()
app.run(debug = False)
#========================== MAIN ===========================================
# if __name__ == "__main__":
# 	threading.Thread(target=send_alerts).start()
# 	app.run(debug=True)