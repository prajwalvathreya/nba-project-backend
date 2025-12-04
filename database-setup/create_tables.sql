CREATE DATABASE IF NOT EXISTS nba_db;
USE nba_db;

-- 1. User Table
CREATE TABLE IF NOT EXISTS User (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 2. Group Table
CREATE TABLE IF NOT EXISTS `Group` (
    group_id INT PRIMARY KEY AUTO_INCREMENT,
    group_code VARCHAR(6) NOT NULL UNIQUE,
    group_name VARCHAR(100) NOT NULL,
    creator_id INT NOT NULL,
    creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (creator_id) REFERENCES User(user_id) ON DELETE CASCADE,
    INDEX idx_group_code (group_code),
    INDEX idx_creator (creator_id)
);

-- 3. UserGroups Table
CREATE TABLE IF NOT EXISTS UserGroups (
    entry_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    group_id INT NOT NULL,
    joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES `Group`(group_id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_group (user_id, group_id),
    INDEX idx_user (user_id),
    INDEX idx_group (group_id)
);

-- 4. Fixture Table
CREATE TABLE IF NOT EXISTS Fixture (
    match_num INT PRIMARY KEY AUTO_INCREMENT,
    home_team VARCHAR(50) NOT NULL,
    away_team VARCHAR(50) NOT NULL,
    home_score INT DEFAULT NULL,
    away_score INT DEFAULT NULL,
    completed BOOLEAN DEFAULT FALSE,
    start_time DATETIME NOT NULL,
    api_game_id INT UNIQUE,
    season VARCHAR(10) DEFAULT '2025-26',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_start_time (start_time),
    INDEX idx_completed (completed),
    INDEX idx_api_game (api_game_id),
    INDEX idx_season (season),
    INDEX idx_fixture_completion (completed, start_time)
);

-- 5. Prediction Table
CREATE TABLE IF NOT EXISTS Prediction (
    pid INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    group_id INT NOT NULL,
    fixture_id INT NOT NULL,
    pred_home_score INT NOT NULL,
    pred_away_score INT NOT NULL,
    prediction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    locked BOOLEAN DEFAULT FALSE,
    points_earned INT DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES `Group`(group_id) ON DELETE CASCADE,
    FOREIGN KEY (fixture_id) REFERENCES Fixture(match_num) ON DELETE CASCADE,
    UNIQUE KEY unique_user_group_fixture (user_id, group_id, fixture_id),
    INDEX idx_user_group (user_id, group_id),
    INDEX idx_fixture (fixture_id),
    INDEX idx_prediction_time (prediction_time)
);

-- 6. Leaderboard Table
CREATE TABLE IF NOT EXISTS Leaderboard (
    user_id INT NOT NULL,
    group_id INT NOT NULL,
    total_points INT DEFAULT 0,
    rank_position INT DEFAULT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, group_id),
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES `Group`(group_id) ON DELETE CASCADE,
    INDEX idx_group_points (group_id, total_points DESC),
    INDEX idx_user (user_id)
);