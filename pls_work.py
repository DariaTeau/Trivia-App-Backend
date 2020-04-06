import pymysql
import os

mydb = pymysql.connect(host='35.234.119.123',
                       user='root',
                       password='ip2020',
                       db='trivia',
                       cursorclass=pymysql.cursors.DictCursor)

try:
    # with mydb.cursor() as cursor:
    # # Create a new record
    # 	sql = "ALTER TABLE `Answers` MODIFY `id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT"
    # 	cursor.execute(sql)
    #
    # # connection is not autocommit by default. So you must commit to save
    # # your changes.
    # mydb.commit()
    mycursor = mydb.cursor()

    # mycursor.execute("DESC Answers")
    # UPDATE Answers SET answer = '1988' where id = 11
    # query = "INSERT INTO Answers (answer, question_id, is_right) " \
    #         "VALUES ('German', 25, 0), " \
    #         "('Italian', 25, 0), " \
    #         "('Spanish', 25, 1), " \
    #         "('French', 25, 0) "

    # mycursor.execute(query)
    mycursor.execute("SELECT * FROM  Users")

    myresult = mycursor.fetchall()

    for x in myresult:
        print(x)

    mydb.commit()
# with connection.cursor() as cursor:
# 	# Read a single record
# 	sql = "SELECT * FROM `Questions` WHERE `username` = '{}'".format("secondUser")
# 	cursor.execute(sql)
# 	# result = cursor.fetchone()
# 	result = [x for x in cursor]
# 	print(result)
finally:
    mydb.close()
