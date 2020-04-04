import requests

new_user = {"username" : "testUser", "points": "100"}
res = requests.post('http://0.0.0.0:5000/api/create_account', data=new_user)
print(res.text)