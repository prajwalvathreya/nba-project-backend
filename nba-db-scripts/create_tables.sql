CREATE DATABASE IF NOT EXISTS nba_db;
USE nba_db;

-- 1. User Table
CREATE TABLE User (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL, -- Store hashed passwords
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 2. Group Table
CREATE TABLE `Group` (
    group_id INT PRIMARY KEY AUTO_INCREMENT,
    group_code VARCHAR(6) NOT NULL UNIQUE,
    group_name VARCHAR(100) NOT NULL,
    creator_id INT NOT NULL,
    creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (creator_id) REFERENCES User(user_id) ON DELETE CASCADE,
    INDEX idx_group_code (group_code),
    INDEX idx_creator (creator_id)
);

-- 3. UserGroups Table (Junction table for many-to-many relationship)
CREATE TABLE UserGroups (
    entry_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    group_id INT NOT NULL,
    joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES `Group`(group_id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_group (user_id, group_id), -- Prevent duplicate memberships
    INDEX idx_user (user_id),
    INDEX idx_group (group_id)
);

-- 4. Fixture Table
CREATE TABLE Fixture (
    match_num INT PRIMARY KEY AUTO_INCREMENT,
    home_team VARCHAR(50) NOT NULL,
    away_team VARCHAR(50) NOT NULL,
    home_score INT DEFAULT NULL,
    away_score INT DEFAULT NULL,
    completed BOOLEAN DEFAULT FALSE,
    start_time DATETIME NOT NULL,
    api_game_id INT UNIQUE, -- For API integration
    season VARCHAR(10) DEFAULT '2025-26', -- Track different seasons
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_start_time (start_time),
    INDEX idx_completed (completed),
    INDEX idx_api_game (api_game_id),
    INDEX idx_season (season)
);

-- 5. Prediction Table (Fixed: consistent column naming)
CREATE TABLE Prediction (
    pid INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    group_id INT NOT NULL,
    fixture_id INT NOT NULL, -- References match_num from Fixture table
    pred_home_score INT NOT NULL,
    pred_away_score INT NOT NULL,
    prediction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    locked BOOLEAN DEFAULT FALSE, -- Changed from prediction_locked for consistency
    points_earned INT DEFAULT 0, -- Store calculated points for this prediction
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES `Group`(group_id) ON DELETE CASCADE,
    FOREIGN KEY (fixture_id) REFERENCES Fixture(match_num) ON DELETE CASCADE,
    -- Ensure one prediction per user per group per fixture
    UNIQUE KEY unique_user_group_fixture (user_id, group_id, fixture_id),
    INDEX idx_user_group (user_id, group_id),
    INDEX idx_fixture (fixture_id),
    INDEX idx_prediction_time (prediction_time)
);

-- 6. Leaderboard Table
CREATE TABLE Leaderboard (
    user_id INT NOT NULL,
    group_id INT NOT NULL,
    total_points INT DEFAULT 0,
    rank_position INT DEFAULT NULL, -- Store calculated rank
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, group_id), -- Composite primary key
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES `Group`(group_id) ON DELETE CASCADE,
    INDEX idx_group_points (group_id, total_points DESC),
    INDEX idx_user (user_id)
);

-- Additional helpful indexes for performance
CREATE INDEX idx_fixture_completion ON Fixture(completed, start_time);
CREATE INDEX idx_user_email ON User(email);
CREATE INDEX idx_group_creator ON `Group`(creator_id, creation_date);

-- Function to generate unique group codes with 6 characters
DELIMITER $$
CREATE FUNCTION generate_group_code() 
RETURNS VARCHAR(6)
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE code VARCHAR(6);
    DECLARE code_exists INT DEFAULT 1;
    DECLARE chars VARCHAR(36) DEFAULT 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    DECLARE i INT DEFAULT 1;
    DECLARE attempts INT DEFAULT 0;
    DECLARE max_attempts INT DEFAULT 1000; -- Prevent infinite loops
    
    WHILE code_exists > 0 AND attempts < max_attempts DO
        SET code = '';
        SET i = 1;
        
        -- Generate 6-character code
        WHILE i <= 6 DO
            SET code = CONCAT(code, SUBSTRING(chars, FLOOR(1 + RAND() * 36), 1));
            SET i = i + 1;
        END WHILE;
        
        -- Check if code already exists
        SELECT COUNT(*) INTO code_exists 
        FROM `Group` 
        WHERE group_code = code;
        
        SET attempts = attempts + 1;
    END WHILE;
    
    -- If we couldn't generate a unique code, return NULL
    IF attempts >= max_attempts THEN
        RETURN NULL;
    END IF;
    
    RETURN code;
END$$
DELIMITER ;

-- Trigger to automatically generate group codes
DELIMITER $$
CREATE TRIGGER before_group_insert 
BEFORE INSERT ON `Group`
FOR EACH ROW
BEGIN
    -- Only generate code if none provided (NULL or empty string)
    IF NEW.group_code IS NULL OR NEW.group_code = '' THEN
        SET NEW.group_code = generate_group_code();
    END IF;
END$$
DELIMITER ;

-- Trigger to automatically add user to UserGroups when they create a group
DELIMITER $$
CREATE TRIGGER after_group_insert 
AFTER INSERT ON `Group`
FOR EACH ROW
BEGIN
    INSERT INTO UserGroups (user_id, group_id) 
    VALUES (NEW.creator_id, NEW.group_id);
END$$
DELIMITER ;

-- Trigger to initialize leaderboard entry when user joins a group
DELIMITER $$
CREATE TRIGGER after_usergroups_insert 
AFTER INSERT ON UserGroups
FOR EACH ROW
BEGIN
    INSERT INTO Leaderboard (user_id, group_id, total_points) 
    VALUES (NEW.user_id, NEW.group_id, 0)
    ON DUPLICATE KEY UPDATE total_points = total_points;
END$$
DELIMITER ;

-- Function to calculate prediction points (example scoring system)
DELIMITER $$
CREATE FUNCTION calculate_prediction_points(
    pred_home INT, 
    pred_away INT, 
    actual_home INT, 
    actual_away INT
) 
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE points INT DEFAULT 0;
    DECLARE pred_winner VARCHAR(10);
    DECLARE actual_winner VARCHAR(10);
    
    -- Exact score match = 10 points
    IF pred_home = actual_home AND pred_away = actual_away THEN
        RETURN 10;
    END IF;
    
    -- Correct winner prediction = 3 points
    SET pred_winner = CASE 
        WHEN pred_home > pred_away THEN 'HOME'
        WHEN pred_away > pred_home THEN 'AWAY' 
        ELSE 'TIE' 
    END;
    
    SET actual_winner = CASE 
        WHEN actual_home > actual_away THEN 'HOME'
        WHEN actual_away > actual_home THEN 'AWAY' 
        ELSE 'TIE' 
    END;
    
    IF pred_winner = actual_winner THEN
        SET points = points + 3;
    END IF;
    
    -- Bonus points for close predictions (within 2 points)
    IF ABS(pred_home - actual_home) <= 2 THEN
        SET points = points + 1;
    END IF;
    
    IF ABS(pred_away - actual_away) <= 2 THEN
        SET points = points + 1;
    END IF;
    
    RETURN points;
END$$
DELIMITER ;

-- Sample data for testing (uncomment to use)
/*
INSERT INTO User (username, email, password) VALUES 
('john_doe', 'john@example.com', '$2b$12$hashed_password_here'),
('jane_smith', 'jane@example.com', '$2b$12$another_hashed_password');

-- Group codes will be auto-generated
INSERT INTO `Group` (group_name, creator_id) VALUES 
('Friends League', 1),
('Office Predictions', 2);

-- Sample fixtures (you'll populate these from NBA API)
INSERT INTO Fixture (home_team, away_team, start_time, api_game_id) VALUES 
('Lakers', 'Warriors', '2025-10-21 19:30:00', 12345),
('Celtics', 'Heat', '2025-10-21 20:00:00', 12346);
*/

-- Show all created tables
SHOW TABLES;