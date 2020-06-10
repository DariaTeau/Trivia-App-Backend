from flask import Flask, request, jsonify
from urllib.parse import parse_qs
import pymysql
import json
import re
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
		self.questions = {}
		self.count = 0
class Room:
	def __init__(self, username, domain):
		self.creator = username
		self.friend = ""
		self.domain = domain
		self.questions = {}
		self.count_f = 0
		self.count_c = 0
		self.players_done = 0
		self.max_points = 0
		self.loser_points = 0
		self.winner = ""
		self.accept = 0
		self.sent = 0

games = {}
rooms = {}
invites = {}
next_id = 0
pattern = "[A-Za-z0-9\-]+"


# root
@app.route("/")
def index():
	"""
	this is a root dir of my server
	:return: str
	"""
	return "This is root!!!!"

@app.route('/api/count_invites', methods=['GET'])
def count_invites():
	return "{}".format(len(invites))

# GET
#folosit pt verificarea autentificarii
@app.route('/api/has_user', methods=['GET'])
def has_user():
	username = request.args.get("username")
	password = request.args.get("password")
	if re.fullmatch(pattern, username) and re.fullmatch(pattern, password):
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
	if not re.fullmatch(pattern, j["username"]) or not re.fullmatch(pattern, j["password"]):
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
	j_tmp = json.loads(s)
	print(j_tmp)
	j = j_tmp["nameValuePairs"]
	# if len(j["username"]) == 0:
	# 	return "Invalid input"
	global next_id
	m = 0
	inv = 0
	if j["multi"] == "0":
		games[next_id] = Game(j["username"], j["domain"])
	else:
		if "friend" in j:
			invites[next_id] = Room(j["username"], j["domain"])
			invites[next_id].friend = j["friend"]
			inv = 1
		else:
			rooms[next_id] = Room(j["username"], j["domain"])
		m = 1
	with db.connect() as conn:
	#with db.cursor() as conn:
		sql = "SELECT id, question FROM `Questions` WHERE `domain_id` = {} ORDER BY RAND() LIMIT 5".format(j["domain"])
		result = conn.execute(sql).fetchall()
		# conn.execute(sql)
		# result = conn.fetchall()
		for res in result:
			response = {}
			response["question"] = res["question"]
			sql = "SELECT * FROM `Answers` WHERE `question_id` = {}".format(res["id"])
			ans = conn.execute(sql).fetchall()
			# conn.execute(sql)
			# ans = conn.fetchall()
			count = 0
			for a in ans:
				if a["is_right"]:
					response["right"] = a["answer"]
				
				response["answer{}".format(count)] = a["answer"]
				count = count + 1
			if m:
				if inv:
					invites[next_id].questions[invites[next_id].count_c] = response
					invites[next_id].count_c += 1
				else:
					rooms[next_id].questions[rooms[next_id].count_c] = response
					rooms[next_id].count_c += 1
			else:
				games[next_id].questions[games[next_id].count] = response
				games[next_id].count += 1
	next_id += 1
	return "{}".format(next_id - 1)

@app.route('/api/get_rooms', methods=['GET'])
def get_rooms():
	username = request.args.get("username")
	final = {}
	count = 0
	for key in rooms:
		room = rooms[key]
		r = {}
		if room.friend == "" and room.creator != username:
			r["creator"] = room.creator
			r["domain"] = room.domain
			r["id"] = key
			final["{}".format(count)] = r
			count += 1
	final["no_rooms"] = "{}".format(count)
	return jsonify(final)

@app.route('/api/has_new_invites', methods=['GET'])
def has_new_invites():
	username = request.args.get("username")
	for key in invites:
		room = invites[key]
		if room.friend == username and room.sent == 0:
			return "Yes"
	return "No"

@app.route('/api/get_invites', methods=['GET'])
def get_invites():
	username = request.args.get("username")
	final = {}
	count = 0
	for key in invites:
		room = invites[key]
		r = {}
		if room.friend == username:
			r["creator"] = room.creator
			r["domain"] = room.domain
			r["id"] = key
			final["{}".format(count)] = r
			room.sent = 1
			count += 1
	final["no_rooms"] = "{}".format(count)
	return jsonify(final)

@app.route('/api/choose_room', methods=['POST'])
def choose_room():
	s = (request.get_data().decode('utf-8'))
	j_tmp = json.loads(s)
	print(j_tmp)
	j = j_tmp["nameValuePairs"]
	if int(j["id"]) in invites:
		invites[int(j["id"])].accept = 1
		return "done"
	else:
		if rooms[int(j["id"])].friend == "":
			rooms[int(j["id"])].friend = j["username"]
			return "done"
		else:
			return "room taken"

@app.route('/api/found_opponent', methods=['GET'])
def found_opponent():
	idx_tmp = request.args.get("id")
	idx = int(idx_tmp)
	if idx in invites:
		if invites[idx].accept == 1:
			return "Yes"
		if invites[idx].accept == -1:
			del invites[idx]
			global next_id
			if len(games) == 0 and len(rooms) == 0 and len(invites):
				next_id = 0
			return "Declined"
	else:
		if rooms[idx].friend != "":
			return "Yes"
	return "No"

@app.route('/api/decline_invite', methods=['POST'])
def decline_invite():
	s = (request.get_data().decode('utf-8'))
	j_tmp = json.loads(s)
	print(j_tmp)
	j = j_tmp["nameValuePairs"]
	idx_tmp = j["id"]
	idx = int(idx_tmp)
	if idx in invites:
		invites[idx].accept = -1
		return "done"
	return "invite not found"

@app.route('/api/decline_all', methods=['POST'])
def decline_all():
	s = (request.get_data().decode('utf-8'))
	j_tmp = json.loads(s)
	print(j_tmp)
	j = j_tmp["nameValuePairs"]
	user = j["username"]

	for inv in invites:
		if invites[inv].friend == user:
			invites[inv].accept = -1
	return "done"

@app.route('/api/get_question', methods=['GET'])
def get_question():
	idx_tmp = request.args.get("id")
	idx = int(idx_tmp)
	if idx in games:
		curr = games[idx]
	else:
		if idx in rooms:
			curr = rooms[idx]
		else:
			curr = invites[idx]
	result = {}
	for i in range(5):
		result["{}".format(i)] = curr.questions[i]
	return jsonify(result)

@app.route('/api/game_done', methods=['POST'])
def game_done():
	s = (request.get_data().decode('utf-8'))
	j_tmp = json.loads(s)
	print(j_tmp)
	j = j_tmp["nameValuePairs"]
	idx_tmp = j["id"]
	idx = int(idx_tmp)
	with db.connect() as conn:
	#with db.cursor() as conn:
		if idx in games:
			sql = "SELECT points FROM `Users` WHERE `username` = '{}'".format(games[idx].username)
			result = conn.execute(sql).fetchall()
			if not result:
				return "Not a user"
			res = result[0]
			points = int(res["points"]) + int(j["points"])
			sql = "UPDATE `Users` SET `points` = {} WHERE `username` = '{}'".format(points, games[idx].username)
			conn.execute(sql)
			del games[idx]
		else:
			if idx in invites:
				curr = invites[idx]
			else:
				curr = rooms[idx]
			sql = "SELECT points FROM `Users` WHERE `username` = '{}'".format(j["username"])
			result = conn.execute(sql).fetchall()
			# conn.execute(sql)
			# result = conn.fetchall()
			if not result:
				return "Not a user"
			res = result[0]
			points = int(res["points"]) + int(j["points"])
			sql = "UPDATE `Users` SET `points` = {} WHERE `username` = '{}'".format(points, j["username"])
			conn.execute(sql)
			if int(j["points"]) >= curr.max_points:
				curr.loser_points = curr.max_points
				curr.max_points = int(j["points"])
				curr.winner = j["username"]
			else:
				curr.loser_points = int(j["points"])
			if curr.players_done:
				if curr.loser_points != curr.max_points:
					sql = "UPDATE `Users` SET `points` = `points` + {} WHERE `username` = '{}'".format(5, curr.winner)
					conn.execute(sql)
			curr.players_done += 1

	global next_id
	if len(games) == 0 and len(rooms) == 0 and len(invites):
		next_id = 0
	return "Updated game {}".format(idx)

@app.route('/api/get_winner', methods=['GET'])
def get_winner():
	idx_tmp = request.args.get("id")
	idx = int(idx_tmp)
	inv = 0
	if idx in invites:
		curr = invites[idx]
		inv = 1
	else:
		curr = rooms[idx]
	if curr.players_done == 2:
		j = {}
		if curr.max_points == curr.loser_points:
			j["winner"] = "equal scores"
		else:
			j["winner"] = curr.winner
		j["points"] = curr.max_points
		j["loser_points"] = curr.loser_points
		if curr.creator == curr.winner:
			j["loser"] = curr.friend
		else:
			j["loser"] = curr.creator
		curr.players_done = -1
		return jsonify(j)
	else:
		if curr.players_done == -1:
			j = {}
			if curr.max_points == curr.loser_points:
				j["winner"] = "equal scores"
			else:
				j["winner"] = curr.winner
			j["points"] = curr.max_points
			j["loser_points"] = curr.loser_points
			if curr.creator == curr.winner:
				j["loser"] = curr.friend
			else:
				j["loser"] = curr.creator
			if inv:
				del invites[idx]
			else:
				del rooms[idx]
			global next_id
			if len(games) == 0 and len(rooms) == 0 and len(invites):
				next_id = 0
			return jsonify(j)
		else:
			return "Game not done"

@app.route('/api/delete_game', methods=['POST'])
def delete_game():
	s = (request.get_data().decode('utf-8'))
	j_tmp = json.loads(s)
	j = j_tmp["nameValuePairs"]
	found = 0
	
	if int(j["id"]) in rooms:
		del rooms[int(j["id"])]
		found = 1
	if int(j["id"]) in invites:
		del invites[int(j["id"])]
		found = 1

	if found:
		global next_id
		if len(games) == 0 and len(rooms) == 0 and len(invites):
			next_id = 0
		return "Room deleted"
		
	return "Room not found"

@app.route('/api/add_question', methods=['POST'])
def add_question():
	s = (request.get_data().decode('utf-8'))
	j = json.loads(s)
	with db.connect() as conn:
	#with db.cursor() as conn:
		sql = "INSERT INTO `UserQ` (`question`, `domain_id`, `rate`) VALUES ('{}', {}, {})".format(j["question"], int(j["domain"]), 0)
		conn.execute(sql)
		sql = "SELECT id from `UserQ` WHERE `question` = '{}'".format(j["question"])
		result = conn.execute(sql).fetchall()
		# conn.execute(sql)
		# result = conn.fetchall()
		res = result[0]
		id_q = res["id"]
		sql = "INSERT INTO `UserA` (`answer`, `q_id`, `is_right`) VALUES ('{}', {}, {})".format(j["answer0"], id_q, 0)
		conn.execute(sql)
		sql = "INSERT INTO `UserA` (`answer`, `q_id`, `is_right`) VALUES ('{}', {}, {})".format(j["answer1"], id_q, 0)
		conn.execute(sql)
		sql = "INSERT INTO `UserA` (`answer`, `q_id`, `is_right`) VALUES ('{}', {}, {})".format(j["answer2"], id_q, 0)
		conn.execute(sql)
		sql = "INSERT INTO `UserA` (`answer`, `q_id`, `is_right`) VALUES ('{}', {}, {})".format(j["right"], id_q, 1)
		conn.execute(sql)

	return "done"

@app.route('/api/get_suggested_questions', methods=['GET'])
def get_suggested_questions():
	with db.connect() as conn:
	#with db.cursor() as conn:
		sql = "SELECT id, question, domain_id FROM `UserQ` WHERE `rate` < 100"
		result = conn.execute(sql).fetchall()
		# conn.execute(sql)
		# result = conn.fetchall()
		no_q = 0
		questions = {}
		for res in result:
			response = {}
			response["question"] = res["question"]
			sql = "SELECT * FROM `UserA` WHERE `q_id` = {}".format(res["id"])
			ans = conn.execute(sql).fetchall()
			# conn.execute(sql)
			# ans = conn.fetchall()
			for a in ans:
				if a["is_right"] == 1:
					response["rightAns"] = a["answer"]
			response["domain"] = res["domain_id"]
			questions["{}".format(no_q)] = response
			no_q += 1
	
	return jsonify(questions)

@app.route('/api/rate_question', methods=['POST'])
def rate_questions():
	s = (request.get_data().decode('utf-8'))
	j = json.loads(s)
	with db.connect() as conn:
	#with db.cursor() as conn:
		sql = "UPDATE `UserQ` SET `rate` = `rate` + 1 WHERE `question` = '{}'".format(j["question"])
		conn.execute(sql)
		sql = "SELECT rate from `UserQ` WHERE `question` = '{}'".format(j["question"])
		result = conn.execute(sql).fetchall()
		# conn.execute(sql)
		# result = conn.fetchall()
		res = result[0]
		print(result)
		if res["rate"] == 100:
			sql = "SELECT (question, domain_id) from `UserQ` WHERE `question` = '{}'".format(j["question"])
			quest = conn.execute(sql).fetchall()
			# conn.execute(sql)
			# quest = conn.fetchall()
			q = quest[0]
			sql = "INSERT INTO `Questions` (`question`, `domain_id`) VALUES ('{}', {})".format(j["question"], int(q["domain_id"]))
			conn.execute(sql)
			sql = "SELECT answer, is_right FROM `UserA` WHERE `q_id` = {}".format(int(q["domain_id"]))
			ans = conn.execute(sql).fetchall()
			# conn.execute(sql)
			# ans = conn.fetchall()
			sql = "SELECT id from `Questions` WHERE `question` = '{}'".format(j["question"])
			result2 = conn.execute(sql).fetchall()
			# conn.execute(sql)
			# result2 = conn.fetchall()
			# conn.execute(sql)
			# result = conn.fetchall()
			res2 = result2[0]
			id_q = res2["id"]
			sql = "INSERT INTO `Answers` (`answer`, `question_id`, `is_right`) VALUES ('{}', {}, {})".format(ans[0]["answer"], id_q, ans[0]["is_right"])
			conn.execute(sql)
			sql = "INSERT INTO `Answers` (`answer`, `question_id`, `is_right`) VALUES ('{}', {}, {})".format(ans[1]["answer"], id_q, ans[1]["is_right"])
			conn.execute(sql)
			sql = "INSERT INTO `Answers` (`answer`, `question_id`, `is_right`) VALUES ('{}', {}, {})".format(ans[2]["answer"], id_q, ans[2]["is_right"])
			conn.execute(sql)
			sql = "INSERT INTO `Answers` (`answer`, `question_id`, `is_right`) VALUES ('{}', {}, {})".format(ans[3]["answer"], id_q, ans[3]["is_right"])
			conn.execute(sql)
			return "Added to game"
	return "Rated"
	
@app.route('/api/unrate_question', methods=['POST'])
def unrate_questions():
	s = (request.get_data().decode('utf-8'))
	j = json.loads(s)
	with db.connect() as conn:
	#with db.cursor() as conn:
		sql = "UPDATE `UserQ` SET `rate` = `rate` - 1 WHERE `question` = '{}'".format(j["question"])
		conn.execute(sql)
	return "Unrated"

@app.route('/api/add_friend', methods=['POST'])
def add_friend():
	s = (request.get_data().decode('utf-8'))
	j = json.loads(s)
	if re.fullmatch(pattern, j["friend"]):
		with db.connect() as conn:
		#with db.cursor() as conn:
			sql = "SELECT * FROM `Users` WHERE `username` = '{}'".format(j["friend"])
			result = conn.execute(sql).fetchall()
			if result:
				sql = "SELECT * FROM `Friends` WHERE `user_name` = '{}' and `friend_name` = '{}'".format(j["username"], j["friend"])
				exists = conn.execute(sql).fetchall()
				if not exists:
					# conn.execute(sql)
					# result = conn.fetchall()
					sql = "INSERT INTO `Friends` (`user_name`, `friend_name`) VALUES ('{}', '{}')".format(j["username"], j["friend"])
					conn.execute(sql)
					sql = "INSERT INTO `Friends` (`user_name`, `friend_name`) VALUES ('{}', '{}')".format(j["friend"], j["username"])
					conn.execute(sql)
					return "Friend added"
				else:
					return "You are already friends"
	return "{} is not a user".format(j["friend"])

@app.route('/api/get_friends', methods=['GET'])
def get_friends():
	username = request.args.get("username")
	with db.connect() as conn:
	#with db.cursor() as conn:
		sql = "SELECT friend_name, points FROM `Friends`, `Users` WHERE `user_name` = '{}' and `friend_name` = Users.`username` ORDER BY points".format(username)
		result = conn.execute(sql).fetchall()
		# conn.execute(sql)
		# result = conn.fetchall()
		fr_list = {}
		count = 0
		for r in result:
			print(r["friend_name"])
			fr_list["{}".format(count)] = r["friend_name"]
			fr_list["points{}".format(count)] = r["points"]
			count += 1

	return fr_list

@app.route('/api/delete_friend', methods=['POST'])
def delete_friend():
	s = (request.get_data().decode('utf-8'))
	j = json.loads(s)
	with db.connect() as conn:
		sql = "DELETE FROM `Friends` WHERE `user_name` = '{}' and `friend_name` = '{}'".format(j["username"], j["friend"])
		conn.execute(sql)
		sql = "DELETE FROM `Friends` WHERE `user_name` = '{}' and `friend_name` = '{}'".format(j["friend"], j["username"])
		conn.execute(sql)
	return "Friend deleted"

@app.route('/api/profile', methods=['GET'])
def profile():
	username = request.args.get("username")
	with db.connect() as conn:
	#with db.cursor() as conn:
		sql = "SELECT points FROM `Users` WHERE `username` = '{}'".format(username)
		#sql = "SELECT * FROM `Users` WHERE `username` = '{}'".format(user)
		result = conn.execute(sql).fetchall()
		user_profile = {}
		if result:
			res = result[0]
			user_profile["points"] = res["points"]
			sql = "SELECT COUNT(*) FROM `Friends` WHERE `user_name` = '{}'".format(username)
			result_2 = conn.execute(sql).fetchall()
			res2 = result_2[0]
			user_profile["friends"] = res2["COUNT(*)"]
	return jsonify(user_profile)


# running web app in local machine
if __name__ == '__main__':
	app.run(host='127.0.0.1', port=8080)