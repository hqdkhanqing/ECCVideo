import requests
import yaml
# conn = psycopg2.connect(host="111.231.144.123", port='5432', database="edgeai", user="admin", password="admin")

# login
# login_url = 'http://127.0.0.1:8000/api/auth/login/'
# user = {'username': 'user04_m', 'password': 'user04'}

# r = requests.post(login_url, data = user)

# if(r.status_code==200):
# 	print('login successfully')
# 	token = r.json()['token']
# else:
# 	print(r.json())
# 	exit()
# print('')

# # get current user
# get_current_user_url = 'http://127.0.0.1:8000/api/users/get_current_user/'
# r = requests.get(get_current_user_url, cookies={'Authorization': token})
# print(r.json())
# print('')


#register
# register_url = 'http://127.0.0.1:8000/api/users/'
# user_info = {
# 	'username': 'user04',
# 	'password': 'user04',
# }
# r = requests.post(register_url, data = user_info)
# print(r.json())


#partial update
# partial_update_url = 'http://127.0.0.1:8000/api/users/6/'
# info = {'username':'user04_m', 'first_name':'Jhon', 'email': 'user04@test.com'}
# r = requests.patch(partial_update_url, data = info, cookies={'Authorization': token})
# print(r.json())


#change password
# change_password_url = 'http://127.0.0.1:8000/api/users/6/change_password/'
# info = {'password':'user04', 'new_password':'user04'}
# r = requests.post(change_password_url, data = info, cookies={'Authorization': token})
# print(r.json())



with open('./testapp.yaml') as f:
	res = yaml.load(f)

print(list(res['containers'].keys()))
print(res['devices'])




