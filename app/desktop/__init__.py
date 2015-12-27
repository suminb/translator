"""A module for the desktop app."""
from flask import Blueprint, render_template


desktop_module = Blueprint('desktop', __name__, template_folder='templates')


@desktop_module.route('')
def desktop_index():
    return render_template('desktop_index.html')
