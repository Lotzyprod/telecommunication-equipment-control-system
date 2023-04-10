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
	permissions: list[Permission]

class Member(BaseModel):
	id: int
	login: str
	name: str | None = None
	surname: str | None = None
	patronymic: str | None = None