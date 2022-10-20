import mariadb


config = configparser.ConfigParser()
config.read("config.ini")

try:
	connection = mariadb.connect(host=config['database']['host'],user=config['database']['user'], password=config['database']['password'],database=config['database']['database'],port=config['database']['port'], autocommit=True)
	now = datetime.now().strftime("[%d/%m/%Y %H:%M:%S]")
	print(f'{now} Connected to the database')
except mariadb.Error as e:
	now = datetime.now().strftime("[%d/%m/%Y %H:%M:%S]")
	print(f'{now} Cant connect to the database with reason: {e}')
	sys.exit(1)


with connection.cursor() as cursor:
	cursor.execute('CREATE TABLE IF NOT EXISTS companies (c_id INT NOT NULL AUTO_INCREMENT, address VARCHAR NOT NULL, name VARCHAR NOT NULL, description VARCHAR, CONSTRAINT c_id PRIMARY KEY (c_id))')
	cursor.execute('CREATE TABLE IF NOT EXISTS company_premises (p_id INT NOT NULL AUTO_INCREMENT, company INT NOT NULL, name VARCHAR NOT NULL, description VARCHAR, CONSTRAINT p_id PRIMARY KEY (p_id), FOREIGN KEY (company) REFERENCES companies(c_id) ON DELETE CASCADE)')
	cursor.execute('CREATE TABLE IF NOT EXISTS company_members (m_id INT NOT NULL AUTO_INCREMENT, company INT NOT NULL, name VARCHAR NOT NULL, surname VARCHAR NOT NULL, patronymic VARCHAR, password VARCHAR, permissions INT NOT NULL, CONSTRAINT p_id PRIMARY KEY (p_id), FOREIGN KEY (company) REFERENCES companies(c_id) ON DELETE CASCADE)')

	cursor.execute('CREATE TABLE IF NOT EXISTS equipments (e_id INT NOT NULL AUTO_INCREMENT, premise INT NOT NULL, type INT NOT NULL, date INT(11) NOT NULL DEFAULT UNIX_TIMESTAMP(), name VARCHAR NOT NULL, description VARCHAR, address INT, CONSTRAINT e_id PRIMARY KEY (e_id), FOREIGN KEY (premise) REFERENCES company_premises(p_id) ON DELETE CASCADE, FOREIGN KEY (type) REFERENCES equipment_types(t_id) ON DELETE CASCADE, FOREIGN KEY (address) REFERENCES local_addresses(la_id) ON DELETE NULL)')

	cursor.execute('CREATE TABLE IF NOT EXISTS equipment_types (t_id INT NOT NULL AUTO_INCREMENT, name VARCHAR NOT NULL, description VARCHAR, CONSTRAINT t_id PRIMARY KEY (t_id))')
	cursor.execute('CREATE TABLE IF NOT EXISTS equipment_service (equipment INT NOT NULL, member INT, date INT(11) NOT NULL DEFAULT UNIX_TIMESTAMP(), commit VARCHAR NOT NULL, CONSTRAINT service PRIMARY KEY (equipment,date), FOREIGN KEY (member) REFERENCES company_members(m_id) ON DELETE NULL, FOREIGN KEY (equipment) REFERENCES equipments(e_id) ON DELETE CASCADE)')
	cursor.execute('CREATE TABLE IF NOT EXISTS equipment_firmwares (equipment INT NOT NULL, date INT(11) NOT NULL DEFAULT UNIX_TIMESTAMP(), path VARCHAR NOT NULL, commit VARCHAR NOT NULL, CONSTRAINT firmware PRIMARY KEY (equipment,date), FOREIGN KEY (equipment) REFERENCES equipments(e_id) ON DELETE CASCADE)')
	cursor.execute('CREATE TABLE IF NOT EXISTS equipment_configurations (equipment INT NOT NULL, date INT(11) NOT NULL DEFAULT UNIX_TIMESTAMP(), path VARCHAR NOT NULL, commit VARCHAR NOT NULL, CONSTRAINT configuration PRIMARY KEY (equipment,date), FOREIGN KEY (equipment) REFERENCES equipments(e_id) ON DELETE CASCADE)')
	
	cursor.execute('CREATE TABLE IF NOT EXISTS local_addresses (la_id INT NOT NULL AUTO_INCREMENT, public_address INT, address CHAR(15) NOT NULL, CONSTRAINT local_address PRIMARY KEY (public_address,address))')
	cursor.execute('CREATE TABLE IF NOT EXISTS public_addresses (pa_id INT NOT NULL AUTO_INCREMENT, address CHAR(15) UNIQUE, CONSTRAINT pa_id PRIMARY KEY (pa_id))')
	
	cursor.execute('CREATE TABLE IF NOT EXISTS equipment_links (equipment_from INT NOT NULL, equipment_to INT NOT NULL, CONSTRAINT link PRIMARY KEY (equipment_from,equipment_to), FOREIGN KEY (equipment_from) REFERENCES equipments(e_id) ON DELETE CASCADE, FOREIGN KEY (equipment_to) REFERENCES equipments(e_id) ON DELETE CASCADE)')
