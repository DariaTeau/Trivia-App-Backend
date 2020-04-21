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

# db = pymysql.connect(host = 'localhost',
# 							user = 'root',
# 							password = 'ip2020',
# 							db = 'trivia',
# 							cursorclass = pymysql.cursors.DictCursor)
app = Flask(__name__)

class Game:
	def __init__(self, username, domain):
		self.username = username
		self.domain = domain
		self.last_q = -1

games = {}
next_id = 0

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
	password = request.args.get("password")
	with db.connect() as conn:
	#with db.cursor() as conn:
		sql = "SELECT * FROM `Users` WHERE `username` = '{}' AND `password` = '{}'".format(username, password)
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
	#with db.cursor() as conn:
		sql = "SELECT * FROM `Users` WHERE `username` = '{}'".format(j['username'])
		result = conn.execute(sql).fetchall()
		if result:
			return "{} already exists".format(j['username'])
		
		sql = "INSERT INTO `Users` (`username`, `password`, `points`) VALUES ('{}', '{}', '{}')". format(j["username"], j["password"], j["points"])
		conn.execute(sql)

	#db.commit()

	return "Insertion for user {} succeded".format(j["username"])

@app.route('/api/register_game', methods=['POST'])
def register_game():
	s = (request.get_data().decode('utf-8'))
	j = json.loads(s)
	print(j)
	if len(j["username"]) == 0:
		return "Invalid input"
	global next_id
	games[next_id] = Game(j["username"], j["domain"])
	next_id += 1
	return "{}".format(next_id - 1)

@app.route('/api/get_question', methods=['GET'])
def get_question():
	idx_tmp = request.args.get("id")
	idx = int(idx_tmp)
	curr_game = games[idx]
	with db.connect() as conn:
	#with db.cursor() as conn:
		sql = "SELECT id, question FROM `Questions` WHERE `domain_id` = {} AND `id` <> {} ORDER BY RAND() LIMIT 1".format(curr_game.domain, curr_game.last_q)
		result = conn.execute(sql).fetchall()
		# conn.execute(sql)
		# result = conn.fetchall()
		if result:
			print(result)
			res = result[0]
			games[idx].last_q = res["id"]
			#first_part = "question: {} ".format(res["question"])
			response = {}
			response["question"] = res["question"]
			sql = "SELECT * FROM `Answers` WHERE `question_id` = {}".format(res["id"])
			ans = conn.execute(sql).fetchall()
			# conn.execute(sql)
			# ans = conn.fetchall()
			count = 0
			for a in ans:
				if a["is_right"]:
					#tmp = "right: {} ".format(a["answer"])
					response["right"] = a["answer"]
				else:
					#tmp = "answer{}: {} ".format(count, a["answer"])
					response["answer{}".format(count)] = a["answer"]
					count = count + 1
				#first_part += tmp
			print(response)
			return jsonify(response)

		return "Question not found"

@app.route('/api/game_done', methods=['POST'])
def game_done():
	s = (request.get_data().decode('utf-8'))
	j = json.loads(s)
	idx_tmp = j["id"]
	idx = int(idx_tmp)
	with db.connect() as conn:
	#with db.cursor() as conn:
		sql = "UPDATE `Users` SET `points` = {} WHERE `username` = '{}'".format(j["points"], games[idx].username)
		conn.execute(sql)
	del games[idx]
	return "Updated game {}".format(idx)


# running web app in local machine
if __name__ == '__main__':
	app.run(host='127.0.0.1', port=8080)