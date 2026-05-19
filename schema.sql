
CREATE TABLE cisterns (
	id SERIAL NOT NULL, 
	name VARCHAR(80) NOT NULL, 
	capacity_liters FLOAT NOT NULL, 
	current_liters FLOAT NOT NULL, 
	min_threshold FLOAT NOT NULL, 
	max_threshold FLOAT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)




CREATE TABLE distribution_plans (
	id SERIAL NOT NULL, 
	service_date DATE NOT NULL, 
	start_time TIME WITHOUT TIME ZONE NOT NULL, 
	end_time TIME WITHOUT TIME ZONE NOT NULL, 
	notes VARCHAR(255), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)




CREATE TABLE houses (
	id SERIAL NOT NULL, 
	house_number VARCHAR(30) NOT NULL, 
	owner_name VARCHAR(120) NOT NULL, 
	address VARCHAR(180) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)



CREATE UNIQUE INDEX ix_houses_house_number ON houses (house_number)


CREATE TABLE maintenance_orders (
	id SERIAL NOT NULL, 
	order_date DATE NOT NULL, 
	maintenance_type VARCHAR(80) NOT NULL, 
	description TEXT NOT NULL, 
	responsible VARCHAR(120) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	observations TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)




CREATE TABLE notifications (
	id SERIAL NOT NULL, 
	title VARCHAR(120) NOT NULL, 
	message VARCHAR(255) NOT NULL, 
	notification_type VARCHAR(40) NOT NULL, 
	recipient_role VARCHAR(30), 
	is_read BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)




CREATE TABLE users (
	id SERIAL NOT NULL, 
	first_name VARCHAR(80) NOT NULL, 
	last_name VARCHAR(80) NOT NULL, 
	address VARCHAR(180) NOT NULL, 
	dpi VARCHAR(20) NOT NULL, 
	role VARCHAR(30) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	failed_attempts INTEGER NOT NULL, 
	is_blocked BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)



CREATE UNIQUE INDEX ix_users_dpi ON users (dpi)


CREATE TABLE maintenance_interventions (
	id SERIAL NOT NULL, 
	order_id INTEGER NOT NULL, 
	intervention_date DATE NOT NULL, 
	intervention_type VARCHAR(80) NOT NULL, 
	observations TEXT, 
	status VARCHAR(30) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_id) REFERENCES maintenance_orders (id)
)




CREATE TABLE monthly_consumptions (
	id SERIAL NOT NULL, 
	house_id INTEGER NOT NULL, 
	period VARCHAR(7) NOT NULL, 
	liters FLOAT NOT NULL, 
	observation VARCHAR(255), 
	is_anomalous BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_consumption_house_period UNIQUE (house_id, period), 
	FOREIGN KEY(house_id) REFERENCES houses (id)
)




CREATE TABLE payments (
	id SERIAL NOT NULL, 
	house_id INTEGER NOT NULL, 
	period VARCHAR(7) NOT NULL, 
	amount NUMERIC(10, 2) NOT NULL, 
	paid BOOLEAN NOT NULL, 
	receipt_number VARCHAR(50), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_payment_house_period UNIQUE (house_id, period), 
	FOREIGN KEY(house_id) REFERENCES houses (id)
)




CREATE TABLE residents (
	id SERIAL NOT NULL, 
	house_id INTEGER NOT NULL, 
	first_name VARCHAR(80) NOT NULL, 
	last_name VARCHAR(80) NOT NULL, 
	identification VARCHAR(30), 
	is_minor BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(house_id) REFERENCES houses (id)
)




CREATE TABLE water_readings (
	id SERIAL NOT NULL, 
	cistern_id INTEGER NOT NULL, 
	liters FLOAT NOT NULL, 
	source VARCHAR(30) NOT NULL, 
	observation VARCHAR(255), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(cistern_id) REFERENCES cisterns (id)
)

