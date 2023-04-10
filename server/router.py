from fastapi import Response

class Router():
	instance = None
	route = None
	def __init__(self, app):
		self.app = app
		Router.route = app
		Router.instance = self
	
		@self.app.get('/')
		async def home(self):	
			return {'hello':'world'}

		@self.app.get("/auth", status_code=200)
		async def auth(self,response: Response,login: str, password: str):
		    with self.app.cursor() as cursor:
		    	cursor.select("SELECT password FROM members WHERE login=? AND password=SHA2(?,256)",(login,password,))
		    	if hash:=cursor.fetchone()[0]:
		    		return {'response':'Успешная авторизация','hash':hash}
		    	response.status_code = 401
		    	return {'response':'Неверный логин или пароль'}