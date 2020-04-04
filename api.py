from flask import Flask, request, jsonify
from urllib.parse import parse_qs
import pymysql
import os

connection = pymysql.connect(host = 'localhost',
							user = 'root',
							password = os.environ['DBPASS'],
							db = 'trivia',
							cursorclass = pymysql.cursors.DictCursor)

app = Flask(__name__)

# root
@app.route("/")
def index():
	"""
	this is a root dir of my server
	:return: str
	"""
	return "This is root!!!!"

# GET
#folosit pt verificarea autentificarii
@app.route('/users/<user>', methods=['GET'])
def has_user(user):
	json = parse_qs(request.get_data().decode('utf-8'))
	for k in json:
		if len(json[k]) == 1:
			json[k] = json[k][0]
	print(json)
	if len(json["username"]) == 0:
		return "Invalid input"
	with connection.cursor() as cursor:
		sql = "SELECT * FROM `Users` WHERE `username` = '{}'".format(json['username'])
		#sql = "SELECT * FROM `Users` WHERE `username` = '{}'".format(user)
		cursor.execute(sql)
		result = cursor.fetchone()
		if result:
			return "%s exists" % json['username']
			#return "%s already exists" % user
	return "%s not found" % json["username"] 
	#return "%s not found" % user

#POST
#folosit pt creare cont
@app.route('/api/create_account', methods=['POST'])
def create_account():
	json = parse_qs(request.get_data().decode('utf-8'))
	for k in json:
		if len(json[k]) == 1:
			json[k] = json[k][0]
	print(json)
	if len(json["username"]) == 0:
		return "Invalid input"

	with connection.cursor() as cursor:
		sql = "SELECT * FROM `Users` WHERE `username` = '{}'".format(json['username'])
		cursor.execute(sql)
		result = cursor.fetchone()
		if result:
			return "%s already exists" % json['username']
		
		sql = "INSERT INTO `Users` (`username`, `points`) VALUES ('{}', '{}')". format(json["username"], json["points"])
		cursor.execute(sql)

	connection.commit()

	return "Insertion for user %s succeded" % json["username"]

# running web app in local machine
if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000)