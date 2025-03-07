from flask import Flask , Blueprint, render_template, request, redirect, url_for, flash
from app.controllers.auth import executar_query
from flask_login import LoginManager, current_user, login_required
from app import get_db_connection
import pymysql
from pymysql.err import IntegrityError

bp = Blueprint('logs', __name__, url_prefix='/logs')

@bp.route('/logs')
def index():
    return render_template('logs/logs.html') 