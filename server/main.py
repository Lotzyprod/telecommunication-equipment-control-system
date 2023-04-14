from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse
import mariadb, yaml, models
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

class System(FastAPI):
	def __init__(self,config):
		super().__init__()
		self.config = config
		self.connection = mariadb.connect(**self.config['mariadb'], autocommit=True)
		
		self.add_middleware(
		    CORSMiddleware,
		    allow_origins=["*"],
		    allow_credentials=True,
		    allow_methods=["*"],
		    allow_headers=["*"],
		)
		self.init_tables()
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
			return self.get_member_permissions(id)

		@self.get("/me/profile",response_model=models.Member, responses={401:{"model": models.Message},404:{"model": models.Message}})
		async def me_profile(token: str = Header(None)):
			if not (id:=self.check_login(token)):
				return JSONResponse(status_code=401, content={"message": "Неверный токен"})
			if not (member:=self.get_member(id)):
				return JSONResponse(status_code=404, content={"message": "Профиль не найден"})
			return member

		
		@self.get("/permissions/{permission_id}", response_model=models.Permission, responses={401:{"model": models.Message},404:{"model": models.Message}})
		async def get_permission(permission_id: int, token: str = Header(None)):
			if not (id:=self.check_login(token)):
				return JSONResponse(status_code=401, content={"message": "Неверный токен"})
			if not (self.check_member_permissions(id,['permissions.view'])):
				return JSONResponse(status_code=401, content={"message": "Недостаточно прав"})
			if not (permission:=self.get_permission(permission_id)):
				return JSONResponse(status_code=404, content={"message": "Право не найдено"})
			return permission

		@self.get("/permissions/", response_model=models.Permissions, responses={401:{"model": models.Message},404:{"model": models.Message}})
		async def get_permissions(limit: int = 10, offset: int = 0, value: str = None, description: str = None, token: str = Header(None)):
			if not (id:=self.check_login(token)):
				return JSONResponse(status_code=401, content={"message": "Неверный токен"})
			if not (self.check_member_permissions(id,['permissions.view'])):
				return JSONResponse(status_code=401, content={"message": "Недостаточно прав"})
			if not (permissions:=self.get_permissions(limit,offset,value,description)):
				return JSONResponse(status_code=404, content={"message": "Право не найдено"})
			return permissions

		@self.delete("/permissions/{permission_id}", response_model=models.Message, responses={400:{"model": models.Message},401:{"model": models.Message},404:{"model": models.Message}})
		async def delete_permission(permission_id: int, token: str = Header(None)):
			if not (id:=self.check_login(token)):
				return JSONResponse(status_code=401, content={"message": "Неверный токен"})
			if not (self.check_member_permissions(id,['permissions.view','permissions.remove'])):
				return JSONResponse(status_code=401, content={"message": "Недостаточно прав"})
			if not (permission:=self.get_permission(permission_id)):
				return JSONResponse(status_code=404, content={"message": "Право не найдено"})
			if not (permission:=self.delete_permission(permission_id)):
				return JSONResponse(status_code=400, content={"message": "Невозможно удалить право"})
			return JSONResponse(status_code=200, content={"message": "Право удалено"})

		@self.patch("/permissions/", response_model=models.Message, responses={400:{"model": models.Message},401:{"model": models.Message},404:{"model": models.Message}})
		async def update_permission(permission: models.Permission, token: str = Header(None)):
			if not (id:=self.check_login(token)):
				return JSONResponse(status_code=401, content={"message": "Неверный токен"})
			if not (self.check_member_permissions(id,['permissions.view','permissions.change'])):
				return JSONResponse(status_code=401, content={"message": "Недостаточно прав"})
			resp=self.update_permission(permission.id,permission.value,permission.description)
			if resp==False:
				return JSONResponse(status_code=400, content={"message": "Право не найдено"})
			if resp==None:
				return JSONResponse(status_code=400, content={"message": "Право с таким значением уже существует"})
			return JSONResponse(status_code=200, content={"message": "Право изменено"})
		
		@self.post("/permissions/", response_model=models.Permission, responses={400:{"model": models.Message},401:{"model": models.Message},404:{"model": models.Message}})
		async def add_permission(permission: models.Permission,token: str = Header(None)):
			if not (id:=self.check_login(token)):
				return JSONResponse(status_code=401, content={"message": "Неверный токен"})
			if not (self.check_member_permissions(id,['permissions.view','permissions.add'])):
				return JSONResponse(status_code=401, content={"message": "Недостаточно прав"})
			if not (permission_id:=self.add_permission(permission.value,permission.description)):
				return JSONResponse(status_code=400, content={"message": "Право с таким значением уже существует"})
			permission.id = permission_id
			return permission

		
		@self.get("/groups/{group_id}", response_model=models.Group, responses={401:{"model": models.Message},404:{"model": models.Message}})
		async def get_group(group_id: int, token: str = Header(None)):
			if not (id:=self.check_login(token)):
				return JSONResponse(status_code=401, content={"message": "Неверный токен"})
			if not (self.check_member_permissions(id,['groups.view'])):
				return JSONResponse(status_code=401, content={"message": "Недостаточно прав"})
			if not (group:=self.get_group(group_id)):
				return JSONResponse(status_code=404, content={"message": "Группа не найдена"})
			return group

		@self.get("/groups/", response_model=models.Groups, responses={401:{"model": models.Message},404:{"model": models.Message}})
		async def get_groups(limit: int = 10, offset: int = 0, name: str = None, description: str = None, token: str = Header(None)):
			if not (id:=self.check_login(token)):
				return JSONResponse(status_code=401, content={"message": "Неверный токен"})
			if not (self.check_member_permissions(id,['groups.view'])):
				return JSONResponse(status_code=401, content={"message": "Недостаточно прав"})
			if not (groups:=self.get_groups(limit,offset,name,description)):
				return JSONResponse(status_code=404, content={"message": "Группа не найдена"})
			return groups

		@self.delete("/groups/{group_id}", response_model=models.Message, responses={400:{"model": models.Message},401:{"model": models.Message},404:{"model": models.Message}})
		async def delete_group(group_id: int, token: str = Header(None)):
			if not (id:=self.check_login(token)):
				return JSONResponse(status_code=401, content={"message": "Неверный токен"})
			if not (self.check_member_permissions(id,['groups.view','groups.remove'])):
				return JSONResponse(status_code=401, content={"message": "Недостаточно прав"})
			if not (group:=self.get_group(group_id)):
				return JSONResponse(status_code=404, content={"message": "Группа не найдена"})
			if not (group:=self.delete_group(group_id)):
				return JSONResponse(status_code=400, content={"message": "Невозможно удалить группу"})
			return JSONResponse(status_code=200, content={"message": "Группа удалена"})

		@self.patch("/groups/", response_model=models.Message, responses={400:{"model": models.Message},401:{"model": models.Message},404:{"model": models.Message}})
		async def update_group(group: models.Group, token: str = Header(None)):
			if not (id:=self.check_login(token)):
				return JSONResponse(status_code=401, content={"message": "Неверный токен"})
			if not (self.check_member_permissions(id,['groups.view','groups.change'])):
				return JSONResponse(status_code=401, content={"message": "Недостаточно прав"})
			if not (self.update_group(group.id,group.name,group.description)):
				return JSONResponse(status_code=400, content={"message": "Группа не найдена"})
			return JSONResponse(status_code=200, content={"message": "Право изменено"})
		
		@self.post("/groups/", response_model=models.Group, responses={400:{"model": models.Message},401:{"model": models.Message},404:{"model": models.Message}})
		async def add_group(group: models.Group,token: str = Header(None)):
			if not (id:=self.check_login(token)):
				return JSONResponse(status_code=401, content={"message": "Неверный токен"})
			if not (self.check_member_permissions(id,['groups.view','groups.add'])):
				return JSONResponse(status_code=401, content={"message": "Недостаточно прав"})
			group.id = self.add_group(group.name,group.description)
			return group


		@self.get("/members/{member_id}", response_model=models.Member, responses={401:{"model": models.Message},404:{"model": models.Message}})
		async def get_member(member_id: int, token: str = Header(None)):
			if not (id:=self.check_login(token)):
				return JSONResponse(status_code=401, content={"message": "Неверный токен"})
			if not (self.check_member_permissions(id,['members.view'])):
				return JSONResponse(status_code=401, content={"message": "Недостаточно прав"})
			if not (member:=self.get_member(member_id)):
				return JSONResponse(status_code=404, content={"message": "Пользователь не найден"})
			return member

		@self.get("/members/", response_model=models.Members, responses={401:{"model": models.Message},404:{"model": models.Message}})
		async def get_members(limit: int = 10, offset: int = 0, value: str = None, description: str = None, token: str = Header(None)):
			if not (id:=self.check_login(token)):
				return JSONResponse(status_code=401, content={"message": "Неверный токен"})
			if not (self.check_member_permissions(id,['members.view'])):
				return JSONResponse(status_code=401, content={"message": "Недостаточно прав"})
			if not (members:=self.get_members(limit,offset,value,description)):
				return JSONResponse(status_code=404, content={"message": "Профиль не найден"})
			return members

		@self.delete("/members/{member_id}", response_model=models.Message, responses={400:{"model": models.Message},401:{"model": models.Message},404:{"model": models.Message}})
		async def delete_member(member_id: int, token: str = Header(None)):
			if not (id:=self.check_login(token)):
				return JSONResponse(status_code=401, content={"message": "Неверный токен"})
			if not (self.check_member_permissions(id,['members.view','members.remove'])):
				return JSONResponse(status_code=401, content={"message": "Недостаточно прав"})
			if not (member:=self.get_member(member_id)):
				return JSONResponse(status_code=404, content={"message": "Пользователь не найден"})
			if not (member:=self.delete_member(member_id)):
				return JSONResponse(status_code=400, content={"message": "Невозможно удалить пользователя"})
			return JSONResponse(status_code=200, content={"message": "Право удалено"})

		@self.patch("/members/", response_model=models.Message, responses={400:{"model": models.Message},401:{"model": models.Message},404:{"model": models.Message}})
		async def update_member(member: models.Member, token: str = Header(None)):
			if not (id:=self.check_login(token)):
				return JSONResponse(status_code=401, content={"message": "Неверный токен"})
			if not (self.check_member_permissions(id,['members.view','members.change'])):
				return JSONResponse(status_code=401, content={"message": "Недостаточно прав"})
			resp=self.update_member(member.id,member.groups,member.name,member.surname,member.patronymic)
			if resp==False:
				return JSONResponse(status_code=400, content={"message": "Пользователь не найден"})
			if resp==None:
				return JSONResponse(status_code=400, content={"message": "Пользователь с таким логином уже существует"})
			return JSONResponse(status_code=200, content={"message": "Пользователь изменен"})
		
		@self.post("/members/", response_model=models.Member, responses={400:{"model": models.Message},401:{"model": models.Message},404:{"model": models.Message}})
		async def add_member(member: models.Member,token: str = Header(None)):
			if not (id:=self.check_login(token)):
				return JSONResponse(status_code=401, content={"message": "Неверный токен"})
			if not (self.check_member_permissions(id,['members.view','members.add'])):
				return JSONResponse(status_code=401, content={"message": "Недостаточно прав"})
			if not (member_id:=self.add_member(member.login,member.password,member.groups,member.name,member.surname,member.patronymic)):
				return JSONResponse(status_code=400, content={"message": "Пользователь с таким логином уже существует"})
			member.id = member_id
			return member


		@self.get("/premises/{premise_id}", response_model=models.Premise, responses={401:{"model": models.Message},404:{"model": models.Message}})
		async def get_premise(premise_id: int, token: str = Header(None)):
			if not (id:=self.check_login(token)):
				return JSONResponse(status_code=401, content={"message": "Неверный токен"})
			if not (self.check_member_permissions(id,['premises.view'])):
				return JSONResponse(status_code=401, content={"message": "Недостаточно прав"})
			if not (premise:=self.get_premise(premise_id)):
				return JSONResponse(status_code=404, content={"message": "Помещение не найдено"})
			return premise

		@self.get("/premises/", response_model=models.Premises, responses={401:{"model": models.Message},404:{"model": models.Message}})
		async def get_premises(limit: int = 10, offset: int = 0, name: str = None, description: str = None, token: str = Header(None)):
			if not (id:=self.check_login(token)):
				return JSONResponse(status_code=401, content={"message": "Неверный токен"})
			if not (self.check_member_permissions(id,['premises.view'])):
				return JSONResponse(status_code=401, content={"message": "Недостаточно прав"})
			if not (premises:=self.get_premises(limit,offset,name,description)):
				return JSONResponse(status_code=404, content={"message": "Помещение не найдено"})
			return premises

		@self.delete("/premises/{premise_id}", response_model=models.Message, responses={400:{"model": models.Message},401:{"model": models.Message},404:{"model": models.Message}})
		async def delete_premise(premise_id: int, token: str = Header(None)):
			if not (id:=self.check_login(token)):
				return JSONResponse(status_code=401, content={"message": "Неверный токен"})
			if not (self.check_member_permissions(id,['premises.view','premises.remove'])):
				return JSONResponse(status_code=401, content={"message": "Недостаточно прав"})
			if not (premise:=self.get_premise(premise_id)):
				return JSONResponse(status_code=404, content={"message": "Помещение не найдено"})
			if not (premise:=self.delete_premise(premise_id)):
				return JSONResponse(status_code=400, content={"message": "Невозможно удалить группу"})
			return JSONResponse(status_code=200, content={"message": "Группа удалена"})

		@self.patch("/premises/", response_model=models.Message, responses={400:{"model": models.Message},401:{"model": models.Message},404:{"model": models.Message}})
		async def update_premise(premise: models.Premise, token: str = Header(None)):
			if not (id:=self.check_login(token)):
				return JSONResponse(status_code=401, content={"message": "Неверный токен"})
			if not (self.check_member_permissions(id,['premises.view','premises.change'])):
				return JSONResponse(status_code=401, content={"message": "Недостаточно прав"})
			if not (self.update_premise(premise.id,premise.name,premise.description)):
				return JSONResponse(status_code=400, content={"message": "Помещение не найдено"})
			return JSONResponse(status_code=200, content={"message": "Помещение изменено"})
		
		@self.post("/premises/", response_model=models.Premise, responses={400:{"model": models.Message},401:{"model": models.Message},404:{"model": models.Message}})
		async def add_premise(premise: models.Premise,token: str = Header(None)):
			if not (id:=self.check_login(token)):
				return JSONResponse(status_code=401, content={"message": "Неверный токен"})
			if not (self.check_member_permissions(id,['premises.view','premises.add'])):
				return JSONResponse(status_code=401, content={"message": "Недостаточно прав"})
			premise.id = self.add_premise(premise.name,premise.description)
			return premise


		@self.get("/equipment/types/{equipmenttype_id}", response_model=models.EquipmentType, responses={401:{"model": models.Message},404:{"model": models.Message}})
		async def get_equipment_type(equipmenttype_id: int, token: str = Header(None)):
			if not (id:=self.check_login(token)):
				return JSONResponse(status_code=401, content={"message": "Неверный токен"})
			if not (self.check_member_permissions(id,['equipments.view'])):
				return JSONResponse(status_code=401, content={"message": "Недостаточно прав"})
			if not (equipmenttype:=self.get_equipment_type(equipmenttype_id)):
				return JSONResponse(status_code=404, content={"message": "Помещение не найдено"})
			return equipmenttype

		@self.get("/equipment/types/", response_model=models.EquipmentTypes, responses={401:{"model": models.Message},404:{"model": models.Message}})
		async def get_equipment_types(limit: int = 10, offset: int = 0, name: str = None, description: str = None, token: str = Header(None)):
			if not (id:=self.check_login(token)):
				return JSONResponse(status_code=401, content={"message": "Неверный токен"})
			if not (self.check_member_permissions(id,['equipments.view'])):
				return JSONResponse(status_code=401, content={"message": "Недостаточно прав"})
			if not (equipment_types:=self.get_equipment_types(limit,offset,name,description)):
				return JSONResponse(status_code=404, content={"message": "Помещение не найдено"})
			return equipment_types

		@self.delete("/equipment/types/{equipmenttype_id}", response_model=models.Message, responses={400:{"model": models.Message},401:{"model": models.Message},404:{"model": models.Message}})
		async def delete_equipment_type(equipmenttype_id: int, token: str = Header(None)):
			if not (id:=self.check_login(token)):
				return JSONResponse(status_code=401, content={"message": "Неверный токен"})
			if not (self.check_member_permissions(id,['equipments.view','equipments.remove'])):
				return JSONResponse(status_code=401, content={"message": "Недостаточно прав"})
			if not (equipmenttype:=self.get_equipment_type(equipmenttype_id)):
				return JSONResponse(status_code=404, content={"message": "Помещение не найдено"})
			if not (equipmenttype:=self.delete_equipment_type(equipmenttype_id)):
				return JSONResponse(status_code=400, content={"message": "Невозможно удалить группу"})
			return JSONResponse(status_code=200, content={"message": "Группа удалена"})

		@self.patch("/equipment/types/", response_model=models.Message, responses={400:{"model": models.Message},401:{"model": models.Message},404:{"model": models.Message}})
		async def update_equipment_type(equipmenttype: models.EquipmentType, token: str = Header(None)):
			if not (id:=self.check_login(token)):
				return JSONResponse(status_code=401, content={"message": "Неверный токен"})
			if not (self.check_member_permissions(id,['equipments.view','equipments.change'])):
				return JSONResponse(status_code=401, content={"message": "Недостаточно прав"})
			if not (self.update_equipment_type(equipmenttype.id,equipmenttype.name,equipmenttype.description)):
				return JSONResponse(status_code=400, content={"message": "Помещение не найдено"})
			return JSONResponse(status_code=200, content={"message": "Помещение изменено"})
		
		@self.post("/equipment/types/", response_model=models.EquipmentType, responses={400:{"model": models.Message},401:{"model": models.Message},404:{"model": models.Message}})
		async def add_equipment_type(equipmenttype: models.EquipmentType,token: str = Header(None)):
			if not (id:=self.check_login(token)):
				return JSONResponse(status_code=401, content={"message": "Неверный токен"})
			if not (self.check_member_permissions(id,['equipments.view','equipments.add'])):
				return JSONResponse(status_code=401, content={"message": "Недостаточно прав"})
			equipmenttype.id = self.add_equipment_type(equipmenttype.name,equipmenttype.description)
			return equipmenttype


		@self.get("/equipments/{equipment_id}", response_model=models.Equipment, responses={401:{"model": models.Message},404:{"model": models.Message}})
		async def get_equipment(equipment_id: int, token: str = Header(None)):
			if not (id:=self.check_login(token)):
				return JSONResponse(status_code=401, content={"message": "Неверный токен"})
			if not (self.check_member_permissions(id,['equipments.view'])):
				return JSONResponse(status_code=401, content={"message": "Недостаточно прав"})
			if not (equipment:=self.get_equipment(equipment_id)):
				return JSONResponse(status_code=404, content={"message": "Оборудование не найдено"})
			return equipment

		@self.get("/equipments/", response_model=models.Equipments, responses={401:{"model": models.Message},404:{"model": models.Message}})
		async def get_equipments(limit: int = 10, offset: int = 0, premise: int = None, type: int = None, date: int = None, name: str = None, description: str = None, address: int = None, token: str = Header(None)):
			if not (id:=self.check_login(token)):
				return JSONResponse(status_code=401, content={"message": "Неверный токен"})
			if not (self.check_member_permissions(id,['equipments.view'])):
				return JSONResponse(status_code=401, content={"message": "Недостаточно прав"})
			if not (equipments:=self.get_equipments(limit,offset,premise,type,date,name,description,address)):
				return JSONResponse(status_code=404, content={"message": "Оборудование не найдено"})
			return equipments

		@self.delete("/equipments/{equipment_id}", response_model=models.Message, responses={400:{"model": models.Message},401:{"model": models.Message},404:{"model": models.Message}})
		async def delete_equipment(equipment_id: int, token: str = Header(None)):
			if not (id:=self.check_login(token)):
				return JSONResponse(status_code=401, content={"message": "Неверный токен"})
			if not (self.check_member_permissions(id,['equipments.view','equipments.remove'])):
				return JSONResponse(status_code=401, content={"message": "Недостаточно прав"})
			if not (equipment:=self.get_equipment(equipment_id)):
				return JSONResponse(status_code=404, content={"message": "Оборудование не найдено"})
			if not (equipment:=self.delete_equipment(equipment_id)):
				return JSONResponse(status_code=400, content={"message": "Невозможно удалить оборудование"})
			return JSONResponse(status_code=200, content={"message": "Оборудование удалено"})

		@self.patch("/equipments/", response_model=models.Message, responses={400:{"model": models.Message},401:{"model": models.Message},404:{"model": models.Message}})
		async def update_equipment(equipment: models.Equipment, token: str = Header(None)):
			if not (id:=self.check_login(token)):
				return JSONResponse(status_code=401, content={"message": "Неверный токен"})
			if not (self.check_member_permissions(id,['equipments.view','equipments.change'])):
				return JSONResponse(status_code=401, content={"message": "Недостаточно прав"})
			if not (self.update_equipment(equipment.id,equipment.premise,equipment.type,equipment.name,equipment.description,equipment.address)):
				return JSONResponse(status_code=400, content={"message": "Оборудование не найдено"})
			return JSONResponse(status_code=200, content={"message": "Оборудование изменено"})
		
		@self.post("/equipments/", response_model=models.Equipment, responses={401:{"model": models.Message},404:{"model": models.Message}})
		async def add_equipment(equipment: models.Equipment,token: str = Header(None)):
			if not (id:=self.check_login(token)):
				return JSONResponse(status_code=401, content={"message": "Неверный токен"})
			if not (self.check_member_permissions(id,['equipments.view','equipments.add'])):
				return JSONResponse(status_code=401, content={"message": "Недостаточно прав"})
			equipment.id = self.add_equipment(equipment.premise,equipment.type,equipment.name,equipment.description,equipment.address)
			return equipment


	def check_login(self, token: str):
		with self.cursor() as cursor:
			cursor.execute('SELECT id FROM members WHERE password=?',(token,))
			if id:=cursor.fetchone():
				return id[0]
		return False
	def check_member_permissions(self,id: int, permissions: [str,...]) -> bool:
		with self.cursor() as cursor:
			count = len(permissions)
			permissions = "('"+"','".join(permissions)+"')"
			cursor.execute(f'SELECT COUNT(p.value) FROM members AS m JOIN groups_permissions AS gp ON gp.groups=m.groups JOIN permissions AS p WHERE p.id=gp.permission AND m.id=? AND p.value IN {permissions}',(id,))
			return count==cursor.fetchone()[0]
	def get_member_permissions(self, id: int):
		with self.cursor() as cursor:
			cursor.execute("SELECT p.id,p.value,p.description FROM members AS m JOIN groups_permissions AS gp ON gp.groups=m.groups JOIN permissions AS p WHERE p.id=gp.permission AND m.id=?",(id,))
			return {'items':[{'id':i[0],'value':i[1],'description':i[2]} for i in cursor.fetchall()]}


	def get_permission(self, id: int):
		with self.cursor() as cursor:
			cursor.execute("SELECT id,value,description  FROM permissions WHERE id=?",(id,))
			if permission:=cursor.fetchone():
				return {'id':permission[0],'value':permission[1],'description':permission[2]}
		return None
	def get_permissions(self, limit: int = 10,offset: int = 0, value: str = None, description: str = None):
		with self.cursor() as cursor:
			if value or description:
				cursor.execute("SELECT id,value,description FROM permissions WHERE LOWER(value)=LOWER(?) OR LOWER(description)=LOWER(?) ORDER BY id LIMIT ?,?",(value,description,offset,limit))
			else:
				cursor.execute("SELECT id,value,description FROM permissions ORDER BY id LIMIT ?,?",(offset,limit,))
			return {'items':[{'id':i[0],'value':i[1],'description':i[2]} for i in cursor.fetchall()]}
	def delete_permission(self, id: int):
		with self.cursor() as cursor:
			cursor.execute("DELETE FROM permissions WHERE id=?",(id,))
			return True
		return False
	def add_permission(self, value: str, description: str = None):
		with self.cursor() as cursor:
			try:
				cursor.execute("SELECT AUTO_INCREMENT FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'permissions'")
				id = cursor.fetchone()[0]
				cursor.execute("INSERT INTO permissions (value,description) VALUES(?,?)",(value,description,))
				return id
			except:
				pass
		return None
	def update_permission(self, id: int, value: str, description: str = None):
		with self.cursor() as cursor:
			try:
				cursor.execute("SELECT value,description FROM permissions WHERE id=?",(id,))
				if cursor.fetchone():
					cursor.execute("UPDATE permissions SET value=?, description=? WHERE id=?",(value,description,id,))
					return True
			except:
				return None
		return False


	def get_group(self, id: int):
		with self.cursor() as cursor:
			cursor.execute("SELECT id,name,description FROM groups WHERE id=?",(id,))
			if group:=cursor.fetchone():
				return {'id':group[0],'name':group[1],'description':group[2]}
		return None
	def get_groups(self, limit: int = 10,offset: int = 0, name: str = None, description: str = None):
		with self.cursor() as cursor:
			if name or description:
				cursor.execute("SELECT id,name,description FROM groups WHERE LOWER(name)=LOWER(?) OR LOWER(description)=LOWER(?) ORDER BY id LIMIT ?,?",(name,description,offset,limit))
			else:
				cursor.execute("SELECT id,name,description FROM groups ORDER BY id LIMIT ?,?",(offset,limit,))
			return {'items':[{'id':i[0],'name':i[1],'description':i[2]} for i in cursor.fetchall()]}
	def delete_group(self, id: int):
		with self.cursor() as cursor:
			cursor.execute("DELETE FROM groups WHERE id=?",(id,))
			return True
		return False
	def add_group(self, name: str, description: str = None):
		with self.cursor() as cursor:
			cursor.execute("SELECT AUTO_INCREMENT FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'groups'")
			id = cursor.fetchone()[0]
			cursor.execute("INSERT INTO groups (name,description) VALUES(?,?)",(name,description,))
			return id
	def update_group(self, id: int, name: str, description: str = None):
		with self.cursor() as cursor:
			cursor.execute("SELECT name,description FROM groups WHERE id=?",(id,))
			if cursor.fetchone():
				cursor.execute("UPDATE groups SET name=?, description=? WHERE id=?",(name,description,id,))
				return True
		return False


	def get_member(self, id: int):
		with self.cursor() as cursor:
			cursor.execute("SELECT id,login,password,groups, name, surname,patronymic FROM members WHERE id=?",(id,))
			if member:=cursor.fetchone():
				return {'id':member[0],'login':member[1],'password':member[2],'groups':member[3],'name':member[4],'surname':member[5],'patronymic':member[6]}
		return None
	def get_members(self, limit: int = 10,offset: int = 0, login: str = None,groups: int = None, name: str = None, surname: str = None, patronymic: str = None):
		with self.cursor() as cursor:
			if login or groups or name or surname or patronymic:
				cursor.execute("SELECT id,login,password,groups,name,surname,patronymic FROM members WHERE LOWER(login)=LOWER(?) OR groups=? OR LOWER(name)=LOWER(?) OR LOWER(surname)=LOWER(?) OR LOWER(patronymic)=LOWER(?) ORDER BY id LIMIT ?,?",(login,groups,name,surname,patronymic,offset,limit))
			else:
				cursor.execute("SELECT id,login,password,groups,name,surname,patronymic FROM members ORDER BY id LIMIT ?,?",(offset,limit,))
			return {'items':[{'id':member[0],'login':member[1],'password':member[2],'groups':member[3],'name':member[4],'surname':member[5],'patronymic':member[6]} for member in cursor.fetchall()]}
	def delete_member(self, id: int):
		with self.cursor() as cursor:
			cursor.execute("DELETE FROM members WHERE id=?",(id,))
			return True
		return False
	def add_member(self, login: str, password: str,groups: int = None, name: str = None, surname: str = None, patronymic: str = None):
		with self.cursor() as cursor:
			try:
				cursor.execute("SELECT AUTO_INCREMENT FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'members'")
				id = cursor.fetchone()[0]
				cursor.execute("INSERT INTO members (login,password,groups,name,surname,patronymic) VALUES(?,SHA2(CONCAT(?,?),256),?,?,?,?)",(login,login,password,groups,name,surname,patronymic,))
				return id
			except:
				return False
		return None
	def update_member(self, id: int, groups: int = None, name: str = None, surname: str = None, patronymic: str = None):
		with self.cursor() as cursor:
			try:
				cursor.execute("SELECT id FROM members WHERE id=?",(id,))
				if cursor.fetchone():
					cursor.execute("UPDATE members SET groups=?, name=?,surname=?,patronymic=? WHERE id=?",(groups,name,surname,patronymic,id,))
					return True
			except:
				return None
		return False

	
	def get_premise(self, id: int):
		with self.cursor() as cursor:
			cursor.execute("SELECT id,name,description FROM premises WHERE id=?",(id,))
			if premise:=cursor.fetchone():
				return {'id':premise[0],'name':premise[1],'description':premise[2]}
		return None
	def get_premises(self, limit: int = 10,offset: int = 0, name: str = None, description: str = None):
		with self.cursor() as cursor:
			if name or description:
				cursor.execute("SELECT id,name,description FROM premises WHERE LOWER(name)=LOWER(?) OR LOWER(description)=LOWER(?) ORDER BY id LIMIT ?,?",(name,description,offset,limit))
			else:
				cursor.execute("SELECT id,name,description FROM premises ORDER BY id LIMIT ?,?",(offset,limit,))
			return {'items':[{'id':i[0],'name':i[1],'description':i[2]} for i in cursor.fetchall()]}
	def delete_premise(self, id: int):
		with self.cursor() as cursor:
			cursor.execute("DELETE FROM premises WHERE id=?",(id,))
			return True
		return False
	def add_premise(self, name: str, description: str = None):
		with self.cursor() as cursor:
			cursor.execute("SELECT AUTO_INCREMENT FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'premises'")
			id = cursor.fetchone()[0]
			cursor.execute("INSERT INTO premises (name,description) VALUES(?,?)",(name,description,))
			return id
	def update_premise(self, id: int, name: str, description: str = None):
		with self.cursor() as cursor:
			cursor.execute("SELECT name,description FROM premises WHERE id=?",(id,))
			if cursor.fetchone():
				cursor.execute("UPDATE premises SET name=?, description=? WHERE id=?",(name,description,id,))
				return True
		return False
	

	def get_equipment_type(self, id: int):
		with self.cursor() as cursor:
			cursor.execute("SELECT id,name,description FROM equipment_types WHERE id=?",(id,))
			if equipmenttype:=cursor.fetchone():
				return {'id':equipmenttype[0],'name':equipmenttype[1],'description':equipmenttype[2]}
		return None
	def get_equipment_types(self, limit: int = 10,offset: int = 0, name: str = None, description: str = None):
		with self.cursor() as cursor:
			if name or description:
				cursor.execute("SELECT id,name,description FROM equipment_types WHERE LOWER(name)=LOWER(?) OR LOWER(description)=LOWER(?) ORDER BY id LIMIT ?,?",(name,description,offset,limit))
			else:
				cursor.execute("SELECT id,name,description FROM equipment_types ORDER BY id LIMIT ?,?",(offset,limit,))
			return {'items':[{'id':i[0],'name':i[1],'description':i[2]} for i in cursor.fetchall()]}
	def delete_equipment_type(self, id: int):
		with self.cursor() as cursor:
			cursor.execute("DELETE FROM equipment_types WHERE id=?",(id,))
			return True
		return False
	def add_equipment_type(self, name: str, description: str = None):
		with self.cursor() as cursor:
			cursor.execute("SELECT AUTO_INCREMENT FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'equipment_types'")
			id = cursor.fetchone()[0]
			cursor.execute("INSERT INTO equipment_types (name,description) VALUES(?,?)",(name,description,))
			return id
	def update_equipment_type(self, id: int, name: str, description: str = None):
		with self.cursor() as cursor:
			cursor.execute("SELECT name,description FROM equipment_types WHERE id=?",(id,))
			if cursor.fetchone():
				cursor.execute("UPDATE equipment_types SET name=?, description=? WHERE id=?",(name,description,id,))
				return True
		return False


	def get_equipment(self, id: int):
		with self.cursor() as cursor:
			cursor.execute("SELECT id,premise,type,date,name,description,address FROM equipments WHERE id=?",(id,))
			if equipment:=cursor.fetchone():
				return {'id':equipment[0],'premise':equipment[1],'type':equipment[2],'date':equipment[3],'name':equipment[4],'description':equipment[5],'address':equipment[6]}
		return None
	def get_equipments(self, limit: int = 10,offset: int = 0, premise: int = None,type: int = None, date: int = None, name: str = None, description: str = None, address: int = None):
		with self.cursor() as cursor:
			if premise or type or date or name or description or address:
				cursor.execute("SELECT id,premise,type,date,name,description,address FROM equipments WHERE premise=? OR type=? OR date<? OR LOWER(name)=LOWER(?) OR LOWER(description)=LOWER(?) OR address=? ORDER BY id LIMIT ?,?",(premise,type,date,name,description,address,offset,limit))
			else:
				cursor.execute("SELECT id,premise,type,date,name,description,address FROM equipments ORDER BY id LIMIT ?,?",(offset,limit,))
			return {'items':[{'id':equipment[0],'premise':equipment[1],'type':equipment[2],'date':equipment[3],'name':equipment[4],'description':equipment[5],'address':equipment[6]} for equipment in cursor.fetchall()]}
	def delete_equipment(self, id: int):
		with self.cursor() as cursor:
			cursor.execute("DELETE FROM equipments WHERE id=?",(id,))
			return True
		return False
	def add_equipment(self, premise: int, type: int,name: str, description: str = None, address: int = None):
		with self.cursor() as cursor:
			cursor.execute("SELECT AUTO_INCREMENT FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'equipments'")
			id = cursor.fetchone()[0]
			cursor.execute("INSERT INTO equipments (premise,type,name,description,address) VALUES(?,?,?,?,?)",(premise,type,name,description,address,))
			return id
		return None
	def update_equipment(self, id: int, premise: int, type: int,name: str, description: str = None, address: int = None):
		with self.cursor() as cursor:
			cursor.execute("SELECT id FROM equipments WHERE id=?",(id,))
			if cursor.fetchone():
				cursor.execute("UPDATE equipments SET premise=?, type=?, name=?, description=?,address=? WHERE id=?",(premise,type,name,description,address,id,))
				return True
		return False

	def cursor(self):
		return self.connection.cursor()
	def reconnect(self):
		self.connection = mariadb.connect(**self.config['mariadb'], autocommit=True)
	def init_tables(self, insert_values: bool = True):
		with self.cursor() as cursor:
			cursor.execute('show tables')
			tables = [table[0] for table in cursor.fetchall()]

			login,password = self.config['admin']['login'],self.config['admin']['password']
			if 'permissions' not in tables:
				cursor.execute('CREATE TABLE IF NOT EXISTS permissions (id INT NOT NULL AUTO_INCREMENT, value TEXT NOT NULL UNIQUE, description TEXT, PRIMARY KEY (id))')
				if insert_values:
					cursor.execute("INSERT INTO permissions (value,description) VALUES('permissions.add','Добавить новое право'),('permissions.remove','Удалить право'),('permissions.change','Изменить право'),('permissions.view','Просмотр прав') ON DUPLICATE KEY UPDATE value = VALUES(value), description = VALUES(description)")
					cursor.execute("INSERT INTO permissions (value,description) VALUES('groups.add','Добавить новую группу'),('groups.remove','Удалить группу'),('groups.change','Изменить группу'),('groups.view','Просмотр групп') ON DUPLICATE KEY UPDATE value = VALUES(value), description = VALUES(description)")
					cursor.execute("INSERT INTO permissions (value,description) VALUES('members.add','Создать нового пользователя'),('members.remove','Удалить пользователя'),('members.change','Изменить пользователя'),('members.view','Просмотр пользователей') ON DUPLICATE KEY UPDATE value = VALUES(value), description = VALUES(description)")
					cursor.execute("INSERT INTO permissions (value,description) VALUES('premises.add','Добавить новое помещение'),('premises.remove','Удалить помещение'),('premises.change','Изменить помещение'),('premises.view','Просмотр помещений') ON DUPLICATE KEY UPDATE value = VALUES(value), description = VALUES(description)")
					cursor.execute("INSERT INTO permissions (value,description) VALUES('addresses.add','Добавить новый адрес'),('addresses.remove','Удалить адрес'),('addresses.change','Изменить адрес'),('addresses.view','Просмотр адресов') ON DUPLICATE KEY UPDATE value = VALUES(value), description = VALUES(description)")
					cursor.execute("INSERT INTO permissions (value,description) VALUES('equipments.add','Добавить новые оборудование'),('equipments.remove','Удалить оборудование'),('equipments.change','Изменить оборудование'),('equipments.view','Просмотр оборудования') ON DUPLICATE KEY UPDATE value = VALUES(value), description = VALUES(description)")
					cursor.execute("INSERT INTO permissions (value,description) VALUES('equipment_firmwares.add','Добавить новую прошивку'),('equipment_firmwares.remove','Удалить прошивку'),('equipment_firmwares.change','Изменить прошивку'),('equipment_firmwares.view','Просмотр прошивок') ON DUPLICATE KEY UPDATE value = VALUES(value), description = VALUES(description)")
					cursor.execute("INSERT INTO permissions (value,description) VALUES('equipment_configurations.add','Добавить новую конфигурацию'),('equipment_configurations.remove','Удалить конфигурацию'),('equipment_configurations.change','Изменить конфигурацию'),('equipment_configurations.view','Просмотр конфигураций') ON DUPLICATE KEY UPDATE value = VALUES(value), description = VALUES(description)")
					cursor.execute("INSERT INTO permissions (value,description) VALUES('equipment_links.add','Добавить новую физическую связь'),('equipment_links.remove','Удалить физическую связь'),('equipment_links.change','Изменить физическую связь'),('equipment_links.view','Просмотр физических связей') ON DUPLICATE KEY UPDATE value = VALUES(value), description = VALUES(description)")
					cursor.execute("INSERT INTO permissions (value,description) VALUES('equipments_service.view','Просмотр изменений в оборудовании') ON DUPLICATE KEY UPDATE value = VALUES(value), description = VALUES(description)")
			if 'groups' not in tables:
				cursor.execute('CREATE TABLE IF NOT EXISTS groups (id INT NOT NULL AUTO_INCREMENT, name TEXT NOT NULL, description TEXT, PRIMARY KEY(id))')
				if insert_values:
					cursor.execute("INSERT INTO groups (id,name,description) VALUES(-1,'Администратор','Все возможные права') ON DUPLICATE KEY UPDATE id = VALUES(id), name = VALUES(name), description = VALUES(description)")
					cursor.execute("INSERT INTO groups (id,name,description) VALUES(1,'Техник','Возможность просмотра оборудования, добавления. Изменение конфигурации, прошивки, просмотр и создание физических связей') ON DUPLICATE KEY UPDATE id = VALUES(id), name = VALUES(name), description = VALUES(description)")
					cursor.execute("INSERT INTO groups (id,name,description) VALUES(2,'Системный админ','Возможность просмотра оборудования. Изменение конфигурации, просмотр и создание логических связей') ON DUPLICATE KEY UPDATE id = VALUES(id), name = VALUES(name), description = VALUES(description)")
					cursor.execute("INSERT INTO groups (id,name,description) VALUES(3,'Руководитель','Просмотр изменений в оборудовании') ON DUPLICATE KEY UPDATE id = VALUES(id), name = VALUES(name), description = VALUES(description)")
			if 'groups_permissions' not in tables:
				cursor.execute('CREATE TABLE if NOT EXISTS groups_permissions (groups INT NOT NULL, permission INT NOT NULL, PRIMARY KEY(groups,permission), FOREIGN KEY (groups) REFERENCES groups(id) ON DELETE CASCADE, FOREIGN KEY (permission) REFERENCES permissions(id) ON DELETE CASCADE)')
				if insert_values:
					cursor.execute('INSERT INTO groups_permissions (groups, permission) SELECT -1,p.id FROM permissions AS p ON DUPLICATE KEY UPDATE groups=VALUES(groups), permission=VALUES(permission)')
					cursor.execute("INSERT INTO groups_permissions (groups, permission) SELECT 1,p.id FROM permissions AS p WHERE p.value in ('equipments.view','equipments.add','equipments.remove','equipments.change','equipment_firmwares.view','equipment_firmwares.add','equipment_firmwares.remove','equipment_firmwares.change','equipment_links.view','equipment_links.add','equipment_links.remove','equipment_links.change','equipment_service.view') ON DUPLICATE KEY UPDATE groups=VALUES(groups), permission=VALUES(permission)")
					cursor.execute("INSERT INTO groups_permissions (groups, permission) SELECT 2,p.id FROM permissions AS p WHERE p.value in ('equipments.view','equipments.change','equipment_configurations.view','equipment_configurations.add','equipment_configurations.remove','equipment_configurations.change','addresses.view','addresses.add','addresses.remove','addresses.change','equipment_service.view') ON DUPLICATE KEY UPDATE groups=VALUES(groups), permission=VALUES(permission)")
					cursor.execute("INSERT INTO groups_permissions (groups, permission) SELECT 3,p.id FROM permissions AS p WHERE p.value in ('equipments.view','members.view','members.add','members.remove','members.change','groups.view','groups.add','groups.remove','groups.change','permissions.view','permissions.add','permissions.remove','permissions.change','premises.view','premises.add','premises.remove','premises.change','equipment_service.view') ON DUPLICATE KEY UPDATE groups=VALUES(groups), permission=VALUES(permission)")
			if 'members' not in tables:
				cursor.execute('CREATE TABLE IF NOT EXISTS members (id INT NOT NULL AUTO_INCREMENT,login TEXT NOT NULL UNIQUE, password TEXT, groups INT, name TEXT, surname TEXT, patronymic TEXT, PRIMARY KEY (id), FOREIGN KEY (groups) REFERENCES groups(id) ON DELETE SET NULL)')
				if insert_values:
					cursor.execute("INSERT INTO members (id,password,login,groups) VALUES(-1,SHA2(CONCAT(?,?),256),?,-1) ON DUPLICATE KEY UPDATE id = VALUES(id), password = VALUES(password), login = VALUES(login), groups = VALUES(groups)",(login,password,login,))
			if 'premises' not in tables:
				cursor.execute('CREATE TABLE IF NOT EXISTS premises (id INT NOT NULL AUTO_INCREMENT, name TEXT NOT NULL, description TEXT, PRIMARY KEY (id))')
			if 'public_addresses' not in tables:
				cursor.execute('CREATE TABLE IF NOT EXISTS public_addresses (id INT NOT NULL AUTO_INCREMENT, address CHAR(15) UNIQUE, PRIMARY KEY (id))')
			if 'local_addresses' not in tables:
				cursor.execute('CREATE TABLE IF NOT EXISTS local_addresses (id INT NOT NULL AUTO_INCREMENT, public_address INT NOT NULL, address CHAR(15) NOT NULL, PRIMARY KEY (id))')
			if 'equipment_types' not in tables:
				cursor.execute('CREATE TABLE IF NOT EXISTS equipment_types (id INT NOT NULL AUTO_INCREMENT, name TEXT NOT NULL, description TEXT, PRIMARY KEY (id))')
			if 'equipments' not in tables:
				cursor.execute('CREATE TABLE IF NOT EXISTS equipments (id INT NOT NULL AUTO_INCREMENT, premise INT NOT NULL, type INT NOT NULL, date INT(11) NOT NULL DEFAULT UNIX_TIMESTAMP(), name TEXT NOT NULL, description TEXT, address INT, PRIMARY KEY (id), FOREIGN KEY (premise) REFERENCES premises(id) ON DELETE CASCADE, FOREIGN KEY (type) REFERENCES equipment_types(id) ON DELETE CASCADE, FOREIGN KEY (address) REFERENCES local_addresses(id) ON DELETE SET NULL)')
			if 'equipment_service' not in tables:
				cursor.execute('CREATE TABLE IF NOT EXISTS equipment_service (equipment INT NOT NULL, member INT, date INT(11) NOT NULL DEFAULT UNIX_TIMESTAMP(), commit TEXT NOT NULL, PRIMARY KEY (equipment,date), FOREIGN KEY (member) REFERENCES members(id) ON DELETE SET NULL, FOREIGN KEY (equipment) REFERENCES equipments(id) ON DELETE CASCADE)')
			if 'equipment_firmwares' not in tables:
				cursor.execute('CREATE TABLE IF NOT EXISTS equipment_firmwares (equipment INT NOT NULL, date INT(11) NOT NULL DEFAULT UNIX_TIMESTAMP(), path TEXT NOT NULL, commit TEXT NOT NULL, CONSTRAINT firmware PRIMARY KEY (equipment,date), FOREIGN KEY (equipment) REFERENCES equipments(id) ON DELETE CASCADE)')
			if 'equipment_configurations' not in tables:
				cursor.execute('CREATE TABLE IF NOT EXISTS equipment_configurations (equipment INT NOT NULL, date INT(11) NOT NULL DEFAULT UNIX_TIMESTAMP(), path TEXT NOT NULL, commit TEXT NOT NULL, PRIMARY KEY (equipment,date), FOREIGN KEY (equipment) REFERENCES equipments(id) ON DELETE CASCADE)')
			if 'equipment_links' not in tables:
				cursor.execute('CREATE TABLE IF NOT EXISTS equipment_links (equipment_from INT NOT NULL, equipment_to INT NOT NULL, PRIMARY KEY (equipment_from,equipment_to), FOREIGN KEY (equipment_from) REFERENCES equipments(id) ON DELETE CASCADE, FOREIGN KEY (equipment_to) REFERENCES equipments(id) ON DELETE CASCADE)')
	
	def make_dump(self):
		path = self.config['dumps']['path']
		tables = ['permissions', 'groups', 'groups_permissions', 'members', 'premises', 'public_addresses', 'local_addresses', 'equipment_types', 'equipments', 'equipment_service', 'equipment_firmwares', 'equipment_configurations', 'equipment_links']
		date = datetime.today().strftime('%Y-%m-%d_%H:%M:%S')
		with open(path+'dump_'+date+'.sql', 'w') as f:
			with self.cursor() as cursor:
				for table in tables:
					cursor.execute(f'SELECT * FROM {table}')
					rows = cursor.fetchall()
					for row in rows:
						fields = ['null' if field is None else repr(field) for field in row]
						f.write(f"INSERT INTO {table} VALUES ({','.join(fields)});\n")
	
	def install_dump(self, dump_file):
		path = self.config['dumps']['path']
		with open(path+dump_file,'r') as f:
			lines = f.readlines()
		tables = ['permissions', 'groups', 'groups_permissions', 'members', 'premises', 'public_addresses', 'local_addresses', 'equipment_types', 'equipments', 'equipment_service', 'equipment_firmwares', 'equipment_configurations', 'equipment_links']
		with self.cursor() as cursor:
			for table in reversed(tables):
				cursor.execute(f'DROP TABLE IF EXISTS {table}')	
		self.init_tables(insert_values=False)
		with self.cursor() as cursor:
			for line in lines:
				cursor.execute(line)

with open("config.yml") as f:
	config = yaml.load(f, Loader=yaml.FullLoader)
app = System(config)
