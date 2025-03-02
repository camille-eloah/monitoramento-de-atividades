from flask import Flask , Blueprint, render_template, request, redirect, url_for, flash
from app.controllers.auth import executar_query
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from app import get_db_connection
from pymysql.err import IntegrityError

bp = Blueprint('index', __name__, url_prefix='/')

@bp.route('/index')
@bp.route('/')
def index():
    return render_template('index.html') 
