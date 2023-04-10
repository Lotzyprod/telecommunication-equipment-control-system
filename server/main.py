from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse
import mariadb, yaml, models
from router import Router
from typing import Optional

class System(FastAPI):
	def __init__(self,config):
		super().__init__()
		self.config = config
		self.connection = mariadb.connect(**self.config['mariadb'], autocommit=True)

		with self.cursor() as cursor:
			login,password = self.config['admin']['login'],self.config['admin']['password']
			cursor.execute('CREATE TABLE IF NOT EXISTS permissions (id INT NOT NULL AUTO_INCREMENT, value TEXT NOT NULL UNIQUE, description TEXT, PRIMARY KEY (id))')
			cursor.execute("INSERT INTO permissions (value,description) VALUES('permissions.add','Добавить новое право'),('permissions.remove','Удалить право'),('permissions.change','Изменить право'),('permissions.view','Просмотр прав') ON DUPLICATE KEY UPDATE value = VALUES(value), description = VALUES(description)")
			cursor.execute("INSERT INTO permissions (value,description) VALUES('groups.add','Добавить новую группу'),('groups.remove','Удалить группу'),('groups.change','Изменить группу'),('groups.view','Просмотр групп') ON DUPLICATE KEY UPDATE value = VALUES(value), description = VALUES(description)")
			cursor.execute("INSERT INTO permissions (value,description) VALUES('members.add','Создать нового пользователя'),('members.remove','Удалить пользователя'),('members.change','Изменить пользователя'),('members.view','Просмотр пользователей') ON DUPLICATE KEY UPDATE value = VALUES(value), description = VALUES(description)")
			cursor.execute("INSERT INTO permissions (value,description) VALUES('premises.add','Добавить новое помещение'),('premises.remove','Удалить помещение'),('premises.change','Изменить помещение'),('premises.view','Просмотр помещений') ON DUPLICATE KEY UPDATE value = VALUES(value), description = VALUES(description)")
			cursor.execute("INSERT INTO permissions (value,description) VALUES('addresses.add','Добавить новый адрес'),('addresses.remove','Удалить адрес'),('addresses.change','Изменить адрес'),('addresses.view','Просмотр адресов') ON DUPLICATE KEY UPDATE value = VALUES(value), description = VALUES(description)")
			cursor.execute("INSERT INTO permissions (value,description) VALUES('equipment_types.add','Добавить новый тип оборудования'),('equipment_types.remove','Удалить тип оборудования'),('equipment_types.change','Изменить тип оборудования'),('equipment_types.view','Просмотр типов оборудования') ON DUPLICATE KEY UPDATE value = VALUES(value), description = VALUES(description)")
			cursor.execute("INSERT INTO permissions (value,description) VALUES('equipments.add','Добавить новые оборудование'),('equipments.remove','Удалить оборудование'),('equipments.change','Изменить оборудование'),('equipments.view','Просмотр оборудования') ON DUPLICATE KEY UPDATE value = VALUES(value), description = VALUES(description)")
			cursor.execute("INSERT INTO permissions (value,description) VALUES('equipment_firmwares.add','Добавить новую прошивку'),('equipment_firmwares.remove','Удалить прошивку'),('equipment_firmwares.change','Изменить прошивку'),('equipment_firmwares.view','Просмотр прошивок') ON DUPLICATE KEY UPDATE value = VALUES(value), description = VALUES(description)")
			cursor.execute("INSERT INTO permissions (value,description) VALUES('equipment_configurations.add','Добавить новую конфигурацию'),('equipment_configurations.remove','Удалить конфигурацию'),('equipment_configurations.change','Изменить конфигурацию'),('equipment_configurations.view','Просмотр конфигураций') ON DUPLICATE KEY UPDATE value = VALUES(value), description = VALUES(description)")
			cursor.execute("INSERT INTO permissions (value,description) VALUES('equipment_links.add','Добавить новую физическую связь'),('equipment_links.remove','Удалить физическую связь'),('equipment_links.change','Изменить физическую связь'),('equipment_links.view','Просмотр физических связей') ON DUPLICATE KEY UPDATE value = VALUES(value), description = VALUES(description)")
			cursor.execute("INSERT INTO permissions (value,description) VALUES('equipments_service.view','Просмотр изменений в оборудовании') ON DUPLICATE KEY UPDATE value = VALUES(value), description = VALUES(description)")

			cursor.execute('CREATE TABLE IF NOT EXISTS groups (id INT NOT NULL AUTO_INCREMENT, permissions BIGINT NOT NULL DEFAULT 0, name TEXT NOT NULL, description TEXT, PRIMARY KEY(id))')
			cursor.execute("INSERT INTO groups (id,name,description) VALUES(-1,'Superadmin','Все возможные права') ON DUPLICATE KEY UPDATE id = VALUES(id), name = VALUES(name), description = VALUES(description)")

			cursor.execute('CREATE TABLE if NOT EXISTS groups_permissions (groups INT NOT NULL, permission INT NOT NULL, PRIMARY KEY(groups,permission), FOREIGN KEY (groups) REFERENCES groups(id) ON DELETE CASCADE, FOREIGN KEY (permission) REFERENCES permissions(id) ON DELETE CASCADE)')
			cursor.execute('INSERT INTO groups_permissions (groups, permission) SELECT -1,p.id FROM permissions AS p WHERE p.id<5 ON DUPLICATE KEY UPDATE groups=VALUES(groups), permission=VALUES(permission)')
			cursor.execute('CREATE TABLE IF NOT EXISTS members (id INT NOT NULL AUTO_INCREMENT,login TEXT NOT NULL UNIQUE, password TEXT, groups INT, name TEXT, surname TEXT, patronymic TEXT, PRIMARY KEY (id), FOREIGN KEY (groups) REFERENCES groups(id) ON DELETE SET NULL)')
			cursor.execute("INSERT INTO members (id,password,login,groups) VALUES(-1,SHA2(CONCAT(?,?),256),?,-1) ON DUPLICATE KEY UPDATE id = VALUES(id), password = VALUES(password), login = VALUES(login), groups = VALUES(groups)",(login,password,login,))

			cursor.execute('CREATE TABLE IF NOT EXISTS premises (id INT NOT NULL AUTO_INCREMENT, name TEXT NOT NULL, description TEXT, PRIMARY KEY (id))')

			cursor.execute('CREATE TABLE IF NOT EXISTS public_addresses (id INT NOT NULL AUTO_INCREMENT, address CHAR(15) UNIQUE, PRIMARY KEY (id))')
			cursor.execute('CREATE TABLE IF NOT EXISTS local_addresses (id INT NOT NULL AUTO_INCREMENT, public_address INT NOT NULL, address CHAR(15) NOT NULL, PRIMARY KEY (id))')
			
			cursor.execute('CREATE TABLE IF NOT EXISTS equipment_types (id INT NOT NULL AUTO_INCREMENT, name TEXT NOT NULL, description TEXT, PRIMARY KEY (id))')
			cursor.execute('CREATE TABLE IF NOT EXISTS equipments (id INT NOT NULL AUTO_INCREMENT, premise INT NOT NULL, type INT NOT NULL, date INT(11) NOT NULL DEFAULT UNIX_TIMESTAMP(), name TEXT NOT NULL, description TEXT, address INT, PRIMARY KEY (id), FOREIGN KEY (premise) REFERENCES premises(id) ON DELETE CASCADE, FOREIGN KEY (type) REFERENCES equipment_types(id) ON DELETE CASCADE, FOREIGN KEY (address) REFERENCES local_addresses(id) ON DELETE SET NULL)')

			cursor.execute('CREATE TABLE IF NOT EXISTS equipment_service (equipment INT NOT NULL, member INT, date INT(11) NOT NULL DEFAULT UNIX_TIMESTAMP(), commit TEXT NOT NULL, PRIMARY KEY (equipment,date), FOREIGN KEY (member) REFERENCES members(id) ON DELETE SET NULL, FOREIGN KEY (equipment) REFERENCES equipments(id) ON DELETE CASCADE)')
			cursor.execute('CREATE TABLE IF NOT EXISTS equipment_firmwares (equipment INT NOT NULL, date INT(11) NOT NULL DEFAULT UNIX_TIMESTAMP(), path TEXT NOT NULL, commit TEXT NOT NULL, CONSTRAINT firmware PRIMARY KEY (equipment,date), FOREIGN KEY (equipment) REFERENCES equipments(id) ON DELETE CASCADE)')
			cursor.execute('CREATE TABLE IF NOT EXISTS equipment_configurations (equipment INT NOT NULL, date INT(11) NOT NULL DEFAULT UNIX_TIMESTAMP(), path TEXT NOT NULL, commit TEXT NOT NULL, PRIMARY KEY (equipment,date), FOREIGN KEY (equipment) REFERENCES equipments(id) ON DELETE CASCADE)')

			cursor.execute('CREATE TABLE IF NOT EXISTS equipment_links (equipment_from INT NOT NULL, equipment_to INT NOT NULL, PRIMARY KEY (equipment_from,equipment_to), FOREIGN KEY (equipment_from) REFERENCES equipments(id) ON DELETE CASCADE, FOREIGN KEY (equipment_to) REFERENCES equipments(id) ON DELETE CASCADE)')
		#self.router = Router(self)
		
		# делаем авторизацию, воруем хэш если подошло
		@self.get("/auth", response_model=models.Token, responses={401:{"model": models.Message}})
		async def auth(login: str, password: str):
		    with self.cursor() as cursor:
		    	cursor.execute("SELECT password FROM members WHERE login=? AND password=SHA2(CONCAT(?,?),256)",(login,login,password,))
		    	if token:=cursor.fetchone():
		    		return {'message':'Успешная авторизация','token':token[0]}
		    	return JSONResponse(status_code=401, content={"message": "Неверный логин или пароль"})
		
		@self.get("/me/permissions",response_model=models.Permissions, responses={401:{"model": models.Message}})
		async def me_permissions(token: str = Header(None)):
			if not (id:=self.check_login(token)):
				return JSONResponse(status_code=401, content={"message": "Неверный токен"})
			return self.get_permissions(id)

		@self.get("/me/profile",response_model=models.Member, responses={401:{"model": models.Message},404:{"model": models.Message}})
		async def me_profile(token: str = Header(None)):
			if not (id:=self.check_login(token)):
				return JSONResponse(status_code=401, content={"message": "Неверный токен"})
			if not (member:=self.get_member(id)):
				return JSONResponse(status_code=404, content={"message": "Профиль не найден"})
			return member
	def check_login(self, token: str):
		with self.cursor() as cursor:
			cursor.execute('SELECT id FROM members WHERE password=?',(token,))
			if id:=cursor.fetchone():
				return id[0]
		return False

	def check_permissions(self,id: int, permissions: [str,...]) -> bool:
		with self.cursor() as cursor:
			count = len(permissions)
			permissions = "('"+"','".join(permissions)+"')"
			cursor.execute(f'SELECT COUNT(p.value) FROM members AS m JOIN groups_permissions AS gp ON gp.groups=m.groups JOIN permissions AS p WHERE p.id=gp.permission AND m.id=? AND p.value IN {permissions}',(id,))
			return count==cursor.fetchone()[0]

	def get_permissions(self, id: int):
		with self.cursor() as cursor:
			cursor.execute("SELECT p.id,p.value,p.description FROM members AS m JOIN groups_permissions AS gp ON gp.groups=m.groups JOIN permissions AS p WHERE p.id=gp.permission AND m.id=?",(id,))
			return {'permissions':[{'id':i[0],'value':i[1],'description':i[2]} for i in cursor.fetchall()]}

	def get_member(self, id: int):
		with self.cursor() as cursor:
			cursor.execute("SELECT id,login,name,surname,patronymic FROM members WHERE id=?",(id,))
			if member:=cursor.fetchone():
				return {'id':member[0],'login':member[1],'name':member[2],'surname':member[3],'patronymic':member[4]}
		return None


	def cursor(self):
		return self.connection.cursor()
	def reconnect(self):
		self.connection = mariadb.connect(**self.config['mariadb'], autocommit=True)

with open("config.yml") as f:
	config = yaml.load(f, Loader=yaml.FullLoader)
app = System(config)
