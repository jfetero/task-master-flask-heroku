from app import User, Tasks
import schedule
import time
from alert_program import email_alerts as e_alerts, phone_alerts as p_alerts
import phonenumbers
from apscheduler.schedulers.blocking import BlockingScheduler

sched = BlockingScheduler()

@sched.scheduled_job('interval', minutes=1)
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

sched.start()