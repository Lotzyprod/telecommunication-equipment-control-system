from pydantic import BaseModel

class Token(BaseModel):
	message: str
	token: str
class Message(BaseModel):
	message: str

class Permission(BaseModel):
	id: int
	value: str
	description: str | None = None
class Permissions(BaseModel):
	items: list[Permission]

class Group(BaseModel):
	id: int
	name: str
	description: str | None
class Groups(BaseModel):
	items: list[Group]

class GroupsPermission(BaseModel):
	groups: int
	permission: int
class GroupsPermissions(BaseModel):
	items: list[GroupsPermission] 

class Member(BaseModel):
	id: int
	login: str
	password: str
	groups: int | None = None
	name: str | None = None
	surname: str | None = None
	patronymic: str | None = None
class Members(BaseModel):
	items: list[Member]

class Premise(BaseModel):
	id: int
	name: str
	description: str | None = None
class Premises(BaseModel):
	items: list[Premise]

class EquipmentType(BaseModel):
	id: int
	name: str
	description: str | None = None
class EquipmentTypes(BaseModel):
	items: list[EquipmentType]

class Equipment(BaseModel):
	id: int
	premise: int
	type: int
	date: int | None = None
	name: str
	description: str | None = None
	address: int | None = None
class Equipments(BaseModel):
	items: list[Equipment]

