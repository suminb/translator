from flask_wtf import Form
from flask.ext.babel import gettext as _
from wtforms import TextField, TextAreaField, SelectField
from wtforms.validators import DataRequired

from utils import language_options

class TranslationRequestForm(Form):
    source = SelectField(_('Source language'), choices=language_options(), validators=[DataRequired()])
    target = SelectField(_('Target language'), choices=language_options(), validators=[DataRequired()])
    text = TextAreaField(_('Original text'), validators=[DataRequired()])

