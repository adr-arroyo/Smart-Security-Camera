import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage

class EmailSender(object):

	def __init__(self, fromEmail = 'email@gmail.com', fromEmailPassword = 'password', toEmail = 'email2@gmail.com') -> None:
		# Email you want to send the update from (only works with gmail)
		self.fromEmail = fromEmail
		# You can generate an app password here to avoid storing your password in plain text
		# https://support.google.com/accounts/answer/185833?hl=en
		self.fromEmailPassword = fromEmailPassword

		# Email you want to send the update to
		self.toEmail = toEmail

	def sendEmail(self, image):
		msgRoot = MIMEMultipart('related')
		msgRoot['Subject'] = 'Security Update'
		msgRoot['From'] = self.fromEmail
		msgRoot['To'] = self.toEmail
		msgRoot.preamble = 'Raspberry pi security camera update'

		msgAlternative = MIMEMultipart('alternative')
		msgRoot.attach(msgAlternative)
		msgText = MIMEText('Smart security cam found object')
		msgAlternative.attach(msgText)

		msgText = MIMEText('<img src="cid:image1">', 'html')
		msgAlternative.attach(msgText)

		msgImage = MIMEImage(image)
		msgImage.add_header('Content-ID', '<image1>')
		msgRoot.attach(msgImage)

		smtp = smtplib.SMTP('smtp.gmail.com', 587)
		smtp.starttls()
		smtp.login(self.fromEmail, self.fromEmailPassword)
		smtp.sendmail(self.fromEmail, self.toEmail, msgRoot.as_string())
		smtp.quit()
