import smtplib
import json
from email.message import EmailMessage
from twilio.rest import Client
import os


# with open('bot_alert.json') as f:
# 		data = json.load(f)

def email_alerts(subject, body, to):
	# print('alerting..')

	msg = EmailMessage()
	msg['Subject'] = subject
	msg['To'] = to
	msg['From'] = 'Task Master Alerts'
	msg.set_content(body)

	user = os.environ['USERNAME']
	passwd = os.environ['APP_PASS']

	server = smtplib.SMTP('smtp.gmail.com', 587)
	server.starttls()
	server.login(user, passwd)
	server.send_message(msg)
	server.quit()

def phone_carrier(number):
	sid = os.environ['TWIL_SID']
	tok = os.environ['TWIL_TOK']
	client = Client(sid, tok)
	phone = client.lookups \
				  .phone_numbers(number)\
				  .fetch(type=['carrier'])
	
	return phone.carrier['name']

def phone_alerts(number, subject,body):
	c = str(phone_carrier(number)).lower()

	avail={
		"t-mobile" : "@tmomail.net",
		'at&t': '@txt.att.net',
		'boost': '@sms.myboostmobile.com',
		'cricket': '@mms.cricketwireless.net',
		'sprint': '@messaging.sprintpcs.com',
		'verizon': '@vtext.com'
	}
	# print(c)
	temp = ''
	for key in avail:
		if key in c:
			temp = avail[key]
	return email_alerts(subject, body, f'{number}{temp}')



if __name__ == '__main__':
	




