from flask import Flask, render_template, render_template_string, url_for,request
import sys
from datetime import datetime
import requests
import configparser
import mariadb

app = Flask(__name__)


config = configparser.ConfigParser()
config.read("config.ini")

try:
	connection = mariadb.connect(host=config['database']['host'],user=config['database']['user'], password=config['database']['password'],database=config['database']['database'],port=int(config['database']['port']), autocommit=True)
	now = datetime.now().strftime("[%d/%m/%Y %H:%M:%S]")
	print(f'{now} Connected to the database')
except mariadb.Error as e:
	now = datetime.now().strftime("[%d/%m/%Y %H:%M:%S]")
	print(f'{now} Cant connect to the database with reason: {e}')
	sys.exit(1)


@app.route("/")
def home():
	return render_template("login.html")

@app.route("/menu")
def menu():
	if (id:=request.cookies.get('userID')) and (password:=request.cookies.get('password')):
		pass
	else:
		return home()

@app.route("/api/login", methods=["GET","POST"])
def api_login():
	if request.method != 'POST':
		return home()

	password = request.form['password']
	id = request.form['id']
	if not (id and password):
		return home()
	cursor = connection.cursor()
	cursor.execute(f'SELECT password FROM company_members WHERE m_id={id} AND password=PASSWORD(\'{password}\')')
	pwd = cursor.fetchone()

	if not pwd:
		return home()

	resp = make_response(render_template('menu.html'))
	resp.set_cookie('userID', int(id))
	resp.set_cookie('password', pwd[0])	
	return resp

app.run()