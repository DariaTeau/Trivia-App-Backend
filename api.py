from flask import Flask, request, jsonify
from urllib.parse import parse_qs
import pymysql
import json
import sqlalchemy
import os

db = sqlalchemy.create_engine(
    # Equivalent URL:
    # mysql+pymysql://<db_user>:<db_pass>@/<db_name>?unix_socket=/cloudsql/<cloud_sql_instance_name>
    sqlalchemy.engine.url.URL(
        drivername="mysql+pymysql",
        username="root",
        password="ip2020",
        database="trivia",
        query={"unix_socket": "/cloudsql/{}".format("firsttry-272817:europe-west3:first-instance")},
    ),
    # ... Specify additional properties here.
    # ...
)
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
@app.route('/api/has_user', methods=['GET'])
def has_user():
	username = request.args.get("username")
	with db.connect() as conn:
		sql = "SELECT * FROM `Users` WHERE `username` = '{}'".format(username)
		#sql = "SELECT * FROM `Users` WHERE `username` = '{}'".format(user)
		result = conn.execute(sql).fetchall()
		if result:
			return "%s exists" % username
			#return "%s already exists" % user
	return "%s not found" % username 
	#return "%s not found" % user

#POST
#folosit pt creare cont
@app.route('/api/create_account', methods=['POST'])
def create_account():
	s = (request.get_data().decode('utf-8'))
	j = json.loads(s)
	print(j)
	if len(j["username"]) == 0:
		return "Invalid input"

	with db.connect() as conn:
		sql = "SELECT * FROM `Users` WHERE `username` = '{}'".format(j['username'])
		result = conn.execute(sql).fetchall()
		if result:
			return "{} already exists".format(j['username'])
		
		sql = "INSERT INTO `Users` (`username`, `points`) VALUES ('{}', '{}')". format(j["username"], j["points"])
		conn.execute(sql)

	#db.commit()

	return "Insertion for user {} succeded".format(j["username"])

# running web app in local machine
if __name__ == '__main__':
	app.run(host='127.0.0.1', port=8080)