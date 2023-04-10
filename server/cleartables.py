import yaml
import mariadb

with open("config.yml") as f:
	config = yaml.load(f, Loader=yaml.FullLoader)
connection = mariadb.connect(**config['mariadb'], autocommit=True)
with connection.cursor() as cursor:
	cursor.execute('DROP TABLE IF EXISTS equipment_configurations')
	cursor.execute('DROP TABLE IF EXISTS equipment_firmwares')
	cursor.execute('DROP TABLE IF EXISTS equipment_links')
	cursor.execute('DROP TABLE IF EXISTS equipment_service')
	cursor.execute('DROP TABLE IF EXISTS equipments')
	cursor.execute('DROP TABLE IF EXISTS equipment_types')
	cursor.execute('DROP TABLE IF EXISTS members')
	cursor.execute('DROP TABLE IF EXISTS groups_permissions')
	cursor.execute('DROP TABLE IF EXISTS groups')
	cursor.execute('DROP TABLE IF EXISTS public_addresses')
	cursor.execute('DROP TABLE IF EXISTS local_addresses')
	cursor.execute('DROP TABLE IF EXISTS permissions')
	cursor.execute('DROP TABLE IF EXISTS premises')
	