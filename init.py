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
	cursor.execute('CREATE TABLE IF NOT EXISTS companies (c_id INT NOT NULL AUTO_INCREMENT, address TEXT NOT NULL, name TEXT NOT NULL, description TEXT, CONSTRAINT c_id PRIMARY KEY (c_id))')
	cursor.execute('CREATE TABLE IF NOT EXISTS company_premises (p_id INT NOT NULL AUTO_INCREMENT, company INT NOT NULL, name TEXT NOT NULL, description TEXT, CONSTRAINT p_id PRIMARY KEY (p_id), FOREIGN KEY (company) REFERENCES companies(c_id) ON DELETE CASCADE)')
	cursor.execute('CREATE TABLE IF NOT EXISTS company_members (m_id INT NOT NULL AUTO_INCREMENT, company INT NOT NULL, name TEXT NOT NULL, surname TEXT NOT NULL, patronymic TEXT, password TEXT, permissions INT, CONSTRAINT m_id PRIMARY KEY (m_id), FOREIGN KEY (company) REFERENCES companies(c_id) ON DELETE CASCADE, FOREIGN KEY (permissions) REFERENCES company_permissions(cp_id) ON DELETE SET NULL)')
	cursor.execute('CREATE TABLE IF NOT EXISTS company_permissions (cp_id INT NOT NULL AUTO_INCREMENT, company INT NOT NULL, name TEXT NOT NULL, description TEXT, CONSTRAINT permission PRIMARY KEY (cp_id,company), FOREIGN KEY (company) REFERENCES companies(c_id) ON DELETE CASCADE)')
	cursor.execute('CREATE TABLE IF NOT EXISTS equipment_types (t_id INT NOT NULL AUTO_INCREMENT, name TEXT NOT NULL, description TEXT, CONSTRAINT t_id PRIMARY KEY (t_id))')

	cursor.execute('CREATE TABLE IF NOT EXISTS local_addresses (la_id INT NOT NULL AUTO_INCREMENT, public_address INT NOT NULL, address CHAR(15) NOT NULL, CONSTRAINT local_address PRIMARY KEY (la_id))')
	cursor.execute('CREATE TABLE IF NOT EXISTS public_addresses (pa_id INT NOT NULL AUTO_INCREMENT, address CHAR(15) UNIQUE, CONSTRAINT pa_id PRIMARY KEY (pa_id))')

	cursor.execute('CREATE TABLE IF NOT EXISTS equipments (e_id INT NOT NULL AUTO_INCREMENT, premise INT NOT NULL, type INT NOT NULL, date INT(11) NOT NULL DEFAULT UNIX_TIMESTAMP(), name TEXT NOT NULL, description TEXT, address INT, CONSTRAINT e_id PRIMARY KEY (e_id), FOREIGN KEY (premise) REFERENCES company_premises(p_id) ON DELETE CASCADE, FOREIGN KEY (type) REFERENCES equipment_types(t_id) ON DELETE CASCADE, FOREIGN KEY (address) REFERENCES local_addresses(la_id) ON DELETE SET NULL)')

	cursor.execute('CREATE TABLE IF NOT EXISTS equipment_service (equipment INT NOT NULL, member INT, date INT(11) NOT NULL DEFAULT UNIX_TIMESTAMP(), commit TEXT NOT NULL, CONSTRAINT service PRIMARY KEY (equipment,date), FOREIGN KEY (member) REFERENCES company_members(m_id) ON DELETE SET NULL, FOREIGN KEY (equipment) REFERENCES equipments(e_id) ON DELETE CASCADE)')
	cursor.execute('CREATE TABLE IF NOT EXISTS equipment_firmwares (equipment INT NOT NULL, date INT(11) NOT NULL DEFAULT UNIX_TIMESTAMP(), path TEXT NOT NULL, commit TEXT NOT NULL, CONSTRAINT firmware PRIMARY KEY (equipment,date), FOREIGN KEY (equipment) REFERENCES equipments(e_id) ON DELETE CASCADE)')
	cursor.execute('CREATE TABLE IF NOT EXISTS equipment_configurations (equipment INT NOT NULL, date INT(11) NOT NULL DEFAULT UNIX_TIMESTAMP(), path TEXT NOT NULL, commit TEXT NOT NULL, CONSTRAINT configuration PRIMARY KEY (equipment,date), FOREIGN KEY (equipment) REFERENCES equipments(e_id) ON DELETE CASCADE)')

	cursor.execute('CREATE TABLE IF NOT EXISTS equipment_links (equipment_from INT NOT NULL, equipment_to INT NOT NULL, CONSTRAINT link PRIMARY KEY (equipment_from,equipment_to), FOREIGN KEY (equipment_from) REFERENCES equipments(e_id) ON DELETE CASCADE, FOREIGN KEY (equipment_to) REFERENCES equipments(e_id) ON DELETE CASCADE)')

	cursor.execute('CREATE OR REPLACE PROCEDURE pushFirmware (equipment_p INT, member_p INT, path_p TEXT, commit_p TEXT) BEGIN DECLARE utime INT; SET utime = UNIX_TIMESTAMP(); INSERT INTO equipment_service (equipment, member, date, commit) VALUES (equipment_p, member_p, utime, \'Update firmware\'); INSERT INTO equipment_firmwares (equipment, date, path, commit) VALUES (equipment_p, utime, path_p, commit_p); END;')


	cursor.execute('CREATE OR REPLACE PROCEDURE pushConfiguration (equipment_p INT, member_p INT, path_p TEXT, commit_p TEXT) BEGIN DECLARE utime INT; SET utime = UNIX_TIMESTAMP(); INSERT INTO equipment_service (equipment, member, date, commit) VALUES (equipment_p, member_p, utime, \'Update Configuration\'); INSERT INTO equipment_firmwares (equipment, date, path, commit) VALUES (equipment_p, utime, path_p, commit_p); END;')

	cursor.execute('CREATE OR REPLACE PROCEDURE addEquipment (premise_p INT, type_p INT, name_p TEXT, description_p TEXT, address_p INT, member_p INT) BEGIN DECLARE utime INT; DECLARE equipment_p INT; SET utime = UNIX_TIMESTAMP(); SELECT AUTO_INCREMENT+1 INTO equipment_p FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=\'equipments\'; INSERT INTO equipments (e_id, premise, type, date, name, description, address) VALUES (equipment_p, premise_p, type_p, utime, name_p, description_p, address_p); INSERT INTO equipment_service (equipment, member, date, commit) VALUES (equipment_p, member_p, utime, \'Install equipment\'); END;')
		
		