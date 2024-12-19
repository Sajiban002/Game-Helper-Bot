CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,
    username VARCHAR(255),
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',
    email VARCHAR(255) UNIQUE,
    password BYTEA,
    CONSTRAINT chk_email_format CHECK (Email LIKE '%@%')
);

CREATE TABLE games (
    game_id SERIAL PRIMARY KEY,
    game_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE mods (
    mod_id SERIAL PRIMARY KEY,
    mod_name VARCHAR(100) NOT NULL,
    mod_version VARCHAR(20) NOT NULL,
    game_id INT NOT NULL,
    mod_file_path TEXT, 
	platform VARCHAR(20),
    FOREIGN KEY (game_id) REFERENCES games (game_id)
);

CREATE TABLE user_downloads (
    download_id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    mod_id INT NOT NULL,
    mod_version VARCHAR(20) NOT NULL,
    download_date DATE NOT NULL DEFAULT CURRENT_DATE,
    FOREIGN KEY (user_id) REFERENCES users (user_id),
    FOREIGN KEY (mod_id) REFERENCES mods (mod_id)
);

CREATE TABLE complaints (
    complaint_id SERIAL PRIMARY KEY, 
    user_id BIGINT NOT NULL,            
    username VARCHAR(50) NOT NULL, 
    message TEXT NOT NULL,           
    category VARCHAR(100) NOT NULL,
    complaint_text TEXT,    
    complaint_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, 
    FOREIGN KEY (user_id) REFERENCES users (user_id) 
);


CREATE TABLE IF NOT EXISTS user_computers (
    user_id BIGINT PRIMARY KEY,
    cpu_model VARCHAR(100),
    gpu_model VARCHAR(100),
    performance_level VARCHAR(50),
    ram INT DEFAULT 16,
    storage INT DEFAULT 100,
    os VARCHAR(50) DEFAULT 'Windows 10'
);

CREATE TABLE IF NOT EXISTS mod_requirements (
    mod_id INT NOT NULL,
    cpu_gpu_combination VARCHAR(50) NOT NULL, 
    min_cpu VARCHAR(100) NOT NULL,
    min_gpu VARCHAR(100) NOT NULL,
    min_ram INT NOT NULL,
    min_storage INT NOT NULL,
    supported_os VARCHAR(50) NOT NULL,
	performance_level VARCHAR(50),
    PRIMARY KEY (mod_id, cpu_gpu_combination)
);


CREATE TABLE IF NOT EXISTS hardware_components (
    component_id SERIAL PRIMARY KEY,
    cpu_manufacturer VARCHAR(50) NOT NULL,
    gpu_manufacturer VARCHAR(50) NOT NULL, 
    cpu_model VARCHAR(100) NOT NULL,
    gpu_model VARCHAR(100) NOT NULL,
    performance_level VARCHAR(50) NOT NULL, 
    description TEXT
);

CREATE VIEW view_games AS
SELECT game_id, game_name FROM games;

DROP TABLE IF EXISTS mod_compatibility CASCADE;
DROP TABLE IF EXISTS user_downloads CASCADE; 
DROP TABLE IF EXISTS complaints CASCADE;  
DROP TABLE IF EXISTS mods CASCADE; 
DROP TABLE IF EXISTS games CASCADE; 
DROP TABLE IF EXISTS user_computers CASCADE; 
DROP TABLE IF EXISTS mod_requirements CASCADE; 
DROP TABLE IF EXISTS users CASCADE; 
DROP TABLE IF EXISTS hardware_components CASCADE;

SELECT * FROM mods
SELECT * FROM games
SELECT * FROM complaints
SELECT * FROM users
SELECT * FROM user_downloads
SELECT * FROM user_computers
SELECT * FROM mod_requirements
SELECT * FROM hardware_components


TRUNCATE TABLE users CASCADE;
TRUNCATE TABLE hardware_components CASCADE;
TRUNCATE TABLE mod_requirements CASCADE;



INSERT INTO hardware_components (cpu_manufacturer, gpu_manufacturer, cpu_model, gpu_model, performance_level, description)
VALUES
-- Intel + Nvidia
('Intel', 'Nvidia', 'Intel Core i3-10100', 'Nvidia GeForce GTX 1050', 'Minimum', 'Процессор и видеокарта для базового уровня.'),
('Intel', 'Nvidia', 'Intel Core i5-10400', 'Nvidia GeForce GTX 1660', 'Medium', 'Процессор и видеокарта для комфортной работы.'),
('Intel', 'Nvidia', 'Intel Core i7-11700', 'Nvidia GeForce RTX 3080', 'Maximum', 'Процессор и видеокарта для максимальной производительности.'),

-- Intel + AMD
('Intel', 'AMD', 'Intel Core i3-10100', 'AMD Radeon RX 560', 'Minimum', 'Процессор и видеокарта для базового уровня.'),
('Intel', 'AMD', 'Intel Core i5-10400', 'AMD Radeon RX 580', 'Medium', 'Процессор и видеокарта для комфортной работы.'),
('Intel', 'AMD', 'Intel Core i7-11700', 'AMD Radeon RX 6900 XT', 'Maximum', 'Процессор и видеокарта для максимальной производительности.'),

-- AMD + Nvidia
('AMD', 'Nvidia', 'AMD Ryzen 3 3100', 'Nvidia GeForce GTX 1050', 'Minimum', 'Процессор и видеокарта для базового уровня.'),
('AMD', 'Nvidia', 'AMD Ryzen 5 3600', 'Nvidia GeForce GTX 1660', 'Medium', 'Процессор и видеокарта для комфортной работы.'),
('AMD', 'Nvidia', 'AMD Ryzen 7 5800X', 'Nvidia GeForce RTX 3080', 'Maximum', 'Процессор и видеокарта для максимальной производительности.'),

-- AMD + AMD
('AMD', 'AMD', 'AMD Ryzen 3 3100', 'AMD Radeon RX 560', 'Minimum', 'Процессор и видеокарта для базового уровня.'),
('AMD', 'AMD', 'AMD Ryzen 5 3600', 'AMD Radeon RX 580', 'Medium', 'Процессор и видеокарта для комфортной работы.'),
('AMD', 'AMD', 'AMD Ryzen 7 5800X', 'AMD Radeon RX 6900 XT', 'Maximum', 'Процессор и видеокарта для максимальной производительности.');



INSERT INTO mod_requirements (mod_id, cpu_gpu_combination, min_cpu, min_gpu, min_ram, min_storage, supported_os, performance_level)
VALUES
(3, 'Intel+Nvidia', 'Intel Core i3-10100', 'Nvidia GeForce GTX 1050', 4, 20, 'Windows 10', 'Minimum'),
(3, 'Intel+AMD', 'Intel Core i3-10100', 'AMD Radeon RX 560', 4, 20, 'Windows 10', 'Minimum'),
(3, 'AMD+AMD', 'AMD Ryzen 3 3100', 'AMD Radeon RX 560', 4, 20, 'Windows 10', 'Minimum'),
(3, 'AMD+Nvidia', 'AMD Ryzen 3 3100', 'Nvidia GeForce GTX 1050', 4, 20, 'Windows 10', 'Minimum'),

(4, 'Intel+Nvidia', 'Intel Core i3-10100', 'Nvidia GeForce GTX 1050', 4, 20, 'Windows 10', 'Minimum'),
(4, 'Intel+AMD', 'Intel Core i3-10100', 'AMD Radeon RX 560', 4, 20, 'Windows 10', 'Minimum'),
(4, 'AMD+AMD', 'AMD Ryzen 3 3100', 'AMD Radeon RX 560', 4, 20, 'Windows 10', 'Minimum'),
(4, 'AMD+Nvidia', 'AMD Ryzen 3 3100', 'Nvidia GeForce GTX 1050', 4, 20, 'Windows 10', 'Minimum'),

(5, 'Intel+Nvidia', 'Intel Core i3-10100', 'Nvidia GeForce GTX 1050', 4, 20, 'Windows 10', 'Minimum'),
(5, 'Intel+AMD', 'Intel Core i3-10100', 'AMD Radeon RX 560', 4, 20, 'Windows 10', 'Minimum'),
(5, 'AMD+AMD', 'AMD Ryzen 3 3100', 'AMD Radeon RX 560', 4, 20, 'Windows 10', 'Minimum'),
(5, 'AMD+Nvidia', 'AMD Ryzen 3 3100', 'Nvidia GeForce GTX 1050', 4, 20, 'Windows 10', 'Minimum'),

(6, 'Intel+Nvidia', 'Intel Core i3-10100', 'Nvidia GeForce GTX 1050', 4, 20, 'Windows 10', 'Minimum'),
(6, 'Intel+AMD', 'Intel Core i3-10100', 'AMD Radeon RX 560', 4, 20, 'Windows 10', 'Minimum'),
(6, 'AMD+AMD', 'AMD Ryzen 3 3100', 'AMD Radeon RX 560', 4, 20, 'Windows 10', 'Minimum'),
(6, 'AMD+Nvidia', 'AMD Ryzen 3 3100', 'Nvidia GeForce GTX 1050', 4, 20, 'Windows 10', 'Minimum'),

(9, 'Intel+Nvidia', 'Intel Core i3-10100', 'Nvidia GeForce GTX 1050', 4, 20, 'Windows 10', 'Minimum'),
(9, 'Intel+AMD', 'Intel Core i3-10100', 'AMD Radeon RX 560', 4, 20, 'Windows 10', 'Minimum'),
(9, 'AMD+AMD', 'AMD Ryzen 3 3100', 'AMD Radeon RX 560', 4, 20, 'Windows 10', 'Minimum'),
(9, 'AMD+Nvidia', 'AMD Ryzen 3 3100', 'Nvidia GeForce GTX 1050', 4, 20, 'Windows 10', 'Minimum'),

(10, 'Intel+Nvidia', 'Intel Core i3-10100', 'Nvidia GeForce GTX 1050', 4, 20, 'Windows 10', 'Minimum'),
(10, 'Intel+AMD', 'Intel Core i3-10100', 'AMD Radeon RX 560', 4, 20, 'Windows 10', 'Minimum'),
(10, 'AMD+AMD', 'AMD Ryzen 3 3100', 'AMD Radeon RX 560', 4, 20, 'Windows 10', 'Minimum'),
(10, 'AMD+Nvidia', 'AMD Ryzen 3 3100', 'Nvidia GeForce GTX 1050', 4, 20, 'Windows 10', 'Minimum'),

(11, 'Intel+Nvidia', 'Intel Core i3-10100', 'Nvidia GeForce GTX 1050', 4, 20, 'Windows 10', 'Minimum'),
(11, 'Intel+AMD', 'Intel Core i3-10100', 'AMD Radeon RX 560', 4, 20, 'Windows 10', 'Minimum'),
(11, 'AMD+AMD', 'AMD Ryzen 3 3100', 'AMD Radeon RX 560', 4, 20, 'Windows 10', 'Minimum'),
(11, 'AMD+Nvidia', 'AMD Ryzen 3 3100', 'Nvidia GeForce GTX 1050', 4, 20, 'Windows 10', 'Minimum'),

(12, 'Intel+Nvidia', 'Intel Core i3-10100', 'Nvidia GeForce GTX 1050', 4, 20, 'Windows 10', 'Minimum'),
(12, 'Intel+AMD', 'Intel Core i3-10100', 'AMD Radeon RX 560', 4, 20, 'Windows 10', 'Minimum'),
(12, 'AMD+AMD', 'AMD Ryzen 3 3100', 'AMD Radeon RX 560', 4, 20, 'Windows 10', 'Minimum'),
(12, 'AMD+Nvidia', 'AMD Ryzen 3 3100', 'Nvidia GeForce GTX 1050', 4, 20, 'Windows 10', 'Minimum'),

-- Средние требования для остальных модов
(1, 'Intel+Nvidia', 'Intel Core i5-10400', 'Nvidia GeForce GTX 1660', 8, 40, 'Windows 10', 'Medium'),
(1, 'Intel+AMD', 'Intel Core i5-10400', 'AMD Radeon RX 580', 8, 40, 'Windows 10', 'Medium'),
(1, 'AMD+AMD', 'AMD Ryzen 5 3600', 'AMD Radeon RX 580', 8, 40, 'Windows 10', 'Medium'),
(1, 'AMD+Nvidia', 'AMD Ryzen 5 3600', 'Nvidia GeForce GTX 1660', 8, 40, 'Windows 10', 'Medium'),

(2, 'Intel+Nvidia', 'Intel Core i5-10400', 'Nvidia GeForce GTX 1660', 8, 40, 'Windows 10', 'Medium'),
(2, 'Intel+AMD', 'Intel Core i5-10400', 'AMD Radeon RX 580', 8, 40, 'Windows 10', 'Medium'),
(2, 'AMD+AMD', 'AMD Ryzen 5 3600', 'AMD Radeon RX 580', 8, 40, 'Windows 10', 'Medium'),
(2, 'AMD+Nvidia', 'AMD Ryzen 5 3600', 'Nvidia GeForce GTX 1660', 8, 40, 'Windows 10', 'Medium'),

(7, 'Intel+Nvidia', 'Intel Core i5-10400', 'Nvidia GeForce GTX 1660', 8, 40, 'Windows 10', 'Medium'),
(7, 'Intel+AMD', 'Intel Core i5-10400', 'AMD Radeon RX 580', 8, 40, 'Windows 10', 'Medium'),
(7, 'AMD+AMD', 'AMD Ryzen 5 3600', 'AMD Radeon RX 580', 8, 40, 'Windows 10', 'Medium'),
(7, 'AMD+Nvidia', 'AMD Ryzen 5 3600', 'Nvidia GeForce GTX 1660', 8, 40, 'Windows 10', 'Medium'),

(8, 'Intel+Nvidia', 'Intel Core i5-10400', 'Nvidia GeForce GTX 1660', 8, 40, 'Windows 10', 'Medium'),
(8, 'Intel+AMD', 'Intel Core i5-10400', 'AMD Radeon RX 580', 8, 40, 'Windows 10', 'Medium'),
(8, 'AMD+AMD', 'AMD Ryzen 5 3600', 'AMD Radeon RX 580', 8, 40, 'Windows 10', 'Medium'),
(8, 'AMD+Nvidia', 'AMD Ryzen 5 3600', 'Nvidia GeForce GTX 1660', 8, 40, 'Windows 10', 'Medium'),

(13, 'Intel+Nvidia', 'Intel Core i5-10400', 'Nvidia GeForce GTX 1660', 8, 40, 'Windows 10', 'Medium'),
(13, 'Intel+AMD', 'Intel Core i5-10400', 'AMD Radeon RX 580', 8, 40, 'Windows 10', 'Medium'),
(13, 'AMD+AMD', 'AMD Ryzen 5 3600', 'AMD Radeon RX 580', 8, 40, 'Windows 10', 'Medium'),
(13, 'AMD+Nvidia', 'AMD Ryzen 5 3600', 'Nvidia GeForce GTX 1660', 8, 40, 'Windows 10', 'Medium'),

(14, 'Intel+Nvidia', 'Intel Core i5-10400', 'Nvidia GeForce GTX 1660', 8, 40, 'Windows 10', 'Medium'),
(14, 'Intel+AMD', 'Intel Core i5-10400', 'AMD Radeon RX 580', 8, 40, 'Windows 10', 'Medium'),
(14, 'AMD+AMD', 'AMD Ryzen 5 3600', 'AMD Radeon RX 580', 8, 40, 'Windows 10', 'Medium'),
(14, 'AMD+Nvidia', 'AMD Ryzen 5 3600', 'Nvidia GeForce GTX 1660', 8, 40, 'Windows 10', 'Medium'),

(15, 'Intel+Nvidia', 'Intel Core i5-10400', 'Nvidia GeForce GTX 1660', 8, 40, 'Windows 10', 'Medium'),
(15, 'Intel+AMD', 'Intel Core i5-10400', 'AMD Radeon RX 580', 8, 40, 'Windows 10', 'Medium'),
(15, 'AMD+AMD', 'AMD Ryzen 5 3600', 'AMD Radeon RX 580', 8, 40, 'Windows 10', 'Medium'),
(15, 'AMD+Nvidia', 'AMD Ryzen 5 3600', 'Nvidia GeForce GTX 1660', 8, 40, 'Windows 10', 'Medium'),

(16, 'Intel+Nvidia', 'Intel Core i5-10400', 'Nvidia GeForce GTX 1660', 8, 40, 'Windows 10', 'Medium'),
(16, 'Intel+AMD', 'Intel Core i5-10400', 'AMD Radeon RX 580', 8, 40, 'Windows 10', 'Medium'),
(16, 'AMD+AMD', 'AMD Ryzen 5 3600', 'AMD Radeon RX 580', 8, 40, 'Windows 10', 'Medium'),
(16, 'AMD+Nvidia', 'AMD Ryzen 5 3600', 'Nvidia GeForce GTX 1660', 8, 40, 'Windows 10', 'Medium'),

(17, 'Intel+Nvidia', 'Intel Core i5-10400', 'Nvidia GeForce GTX 1660', 8, 40, 'Windows 10', 'Medium'),
(17, 'Intel+AMD', 'Intel Core i5-10400', 'AMD Radeon RX 580', 8, 40, 'Windows 10', 'Medium'),
(17, 'AMD+AMD', 'AMD Ryzen 5 3600', 'AMD Radeon RX 580', 8, 40, 'Windows 10', 'Medium'),
(17, 'AMD+Nvidia', 'AMD Ryzen 5 3600', 'Nvidia GeForce GTX 1660', 8, 40, 'Windows 10', 'Medium'),

(18, 'Intel+Nvidia', 'Intel Core i5-10400', 'Nvidia GeForce GTX 1660', 8, 40, 'Windows 10', 'Medium'),
(18, 'Intel+AMD', 'Intel Core i5-10400', 'AMD Radeon RX 580', 8, 40, 'Windows 10', 'Medium'),
(18, 'AMD+AMD', 'AMD Ryzen 5 3600', 'AMD Radeon RX 580', 8, 40, 'Windows 10', 'Medium'),
(18, 'AMD+Nvidia', 'AMD Ryzen 5 3600', 'Nvidia GeForce GTX 1660', 8, 40, 'Windows 10', 'Medium');





INSERT INTO games (game_name) VALUES
('Minecraft'),
('Terraria'),
('Don`t Starve'),
('Lethal Company');

INSERT INTO mods (mod_name, mod_version, game_id, mod_file_path, platform) VALUES
-- Minecraft: Forge
('Optifine', '1.20.1', 1, './mods/OptiFine_1.20.1.jar', 'Forge'),
('JourneyMap', '1.20.1', 1, './mods/journeymap_1.20.1.jar', 'Forge'),
('Optifine', '1.16.5', 1, './mods/OptiFine_1.16.5.jar', 'Forge'),
('JourneyMap', '1.16.5', 1, './mods/journeymap_1.16.5.jar', 'Forge'),
('Optifine', '1.12.2', 1, './mods/OptiFine_1.12.2.jar', 'Forge'),
('JourneyMap', '1.12.2', 1, './mods/journeymap_1.12.2.jar', 'Forge'),

-- Minecraft: Fabric
('Sodium', '1.20.1', 1, './mods/sodium-fabric-0.5.11-mc1.20.1.jar', 'Fabric'),
('Lithium', '1.20.1', 1, './mods/lithium-fabric-mc1.20.1-0.11.2.jar', 'Fabric'),
('Sodium', '1.16.5', 1, '../mods/sodium-fabric-mc1.16.5-0.2.0build.4.jar', 'Fabric'),
('Lithium', '1.16.5', 1, './mods/lithium-fabric-mc1.16.5-0.6.6.jar', 'Fabric'),
('Sodium', '1.12.2', 1, 'NULL', 'Fabric'),
('Lithium', '1.12.2', 1, 'NULL', 'Fabric'),

-- Terraria
('Calamity Mod', '1.4.5', 2, 'https://example.com/calamity', NULL),
('Magic Storage', '1.4.5', 2, 'https://example.com/magicstorage', NULL),

-- Don’t Starve
('Shipwrecked', 'v1.0', 3, 'https://example.com/shipwrecked', NULL),
('Gorge Extended', 'v1.1', 3, 'https://example.com/gorge', NULL),

-- Lethal Company
('Lethal Lights', 'v1.0', 4, 'https://example.com/lethallights', NULL),
('Scary Sounds', 'v1.0', 4, 'https://example.com/scarysounds', NULL);

TRUNCATE TABLE mod_requirements CASCADE;

