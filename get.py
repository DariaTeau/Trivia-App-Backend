import requests

new_user = {"username" : "testUser"}
res = requests.get('http://0.0.0.0:5000/users/user', data=new_user)
print(res.text)