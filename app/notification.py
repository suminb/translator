from flask.ext.mail import Mail, Message
from flaskext.babel import Babel, gettext as _

from __init__ import app, db, config
from models import *

app.config['MAIL_SERVER'] = config.MAIL_SERVER
app.config['MAIL_PORT'] = config.MAIL_PORT
app.config['MAIL_USERNAME'] = config.MAIL_USERNAME
app.config['MAIL_PASSWORD'] = config.MAIL_PASSWORD

mail = Mail(app)
babel = Babel(app)

@babel.localeselector
def get_locale():
    return 'ko'

def sendmail(notification):
    message = Message(
        subject=_('You have a notification from Better Translator'),
        body=notification.payload,
        sender=(_('app-title'), 'translator@suminb.com'),
        recipients=[notification.user.email]
    )

    with app.app_context():
        mail.send(message)

        db.session.delete(notification)


def main():
    for notification in NotificationQueue.query.all():
        sendmail(notification)

    db.session.commit()


if __name__ == '__main__':
    #main()

    with app.app_context():
        print _('app-title')