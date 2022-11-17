import mariadb
import configparser
from datetime import datetime
import sys

config = configparser.ConfigParser()
config.read("config.ini")

try:
	connection = mariadb.connect(host=config['database']['host'],user=config['database']['user'], password=config['database']['password'],database=config['database']['database'],port=int(config['database']['port']), autocommit=True)
	now = datetime.now().strftime("[%d/%m/%Y %H:%M:%S]")
	print(f'{now} Connected to the database')
except mariadb.Error as e:
	now = datetime.now().strftime("[%d/%m/%Y %H:%M:%S]")
	print(f'{now} Cant connect to the database with reason: {e}')
	sys.exit(1)

with connection.cursor() as cursor:
	cursor.execute('DROP TABLE companies')
	cursor.execute('DROP TABLE company_premises')
	cursor.execute('DROP TABLE company_members')
	cursor.execute('DROP TABLE company_permissions')
	cursor.execute('DROP TABLE equipment_types')
	cursor.execute('DROP TABLE local_addresses')
	cursor.execute('DROP TABLE public_addresses')
	cursor.execute('DROP TABLE equipments')
	cursor.execute('DROP TABLE equipment_service')
	cursor.execute('DROP TABLE equipment_firmwares')
	cursor.execute('DROP TABLE equipment_configurations')
	cursor.execute('DROP TABLE equipment_links')
		