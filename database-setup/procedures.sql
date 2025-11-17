-- This file contains stored procedures for managing fixtures and database utilities
-- Fixed with DROP IF EXISTS and reserved word issues

-- Drop existing procedures to avoid conflicts
DROP PROCEDURE IF EXISTS test_database_connection;
DROP PROCEDURE IF EXISTS get_database_stats;
DROP PROCEDURE IF EXISTS get_database_health;
DROP PROCEDURE IF EXISTS insert_fixture;
DROP PROCEDURE IF EXISTS clear_season_fixtures;
DROP PROCEDURE IF EXISTS get_season_stats;
DROP PROCEDURE IF EXISTS check_required_tables;
DROP PROCEDURE IF EXISTS create_user;
DROP PROCEDURE IF EXISTS get_user_for_login;
DROP PROCEDURE IF EXISTS get_user_by_id;
DROP PROCEDURE IF EXISTS get_user_by_username;
DROP PROCEDURE IF EXISTS check_username_exists;
DROP PROCEDURE IF EXISTS check_email_exists;
DROP PROCEDURE IF EXISTS get_user_stats;

-- Procedure to test database connectivity
DELIMITER $$
CREATE PROCEDURE test_database_connection()
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Database connectivity test failed', 
            MYSQL_ERRNO = 1001;
    END;
    
    SELECT 
        1 as test,
        VERSION() as version,
        DATABASE() as current_db;
END$$
DELIMITER ;

-- Procedure to get database statistics (FIXED: escaped 'groups' reserved word)
DELIMITER $$
CREATE PROCEDURE get_database_stats()
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Failed to retrieve database statistics', 
            MYSQL_ERRNO = 1002;
    END;
    
    SELECT 
        (SELECT COUNT(*) FROM User) as users,
        (SELECT COUNT(*) FROM `Group`) as `groups`,  -- FIXED: escaped reserved word
        (SELECT COUNT(*) FROM Fixture) as fixtures,
        (SELECT COUNT(*) FROM Prediction) as predictions;
END$$
DELIMITER ;

-- Procedure to get detailed database health information
DELIMITER $$
CREATE PROCEDURE get_database_health()
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Failed to retrieve database health information', 
            MYSQL_ERRNO = 1003;
    END;
    
    SELECT 
        'connected' as status,
        VERSION() as mysql_version,
        DATABASE() as current_db,
        (SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
         WHERE TABLE_SCHEMA = DATABASE() 
         AND TABLE_NAME IN ('User', 'Group', 'UserGroups', 'Fixture', 'Prediction', 'Leaderboard')
        ) as tables_count;
END$$
DELIMITER ;

-- Procedure to insert or update fixtures
DELIMITER $$
CREATE PROCEDURE insert_fixture(
    IN p_home_team VARCHAR(50),
    IN p_away_team VARCHAR(50),
    IN p_start_time DATETIME,
    IN p_home_score INT,
    IN p_away_score INT,
    IN p_completed BOOLEAN,
    IN p_api_game_id INT,
    IN p_season VARCHAR(10)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Failed to insert or update fixture', 
            MYSQL_ERRNO = 2001;
    END;
    
    -- Input validation
    IF p_home_team IS NULL OR p_home_team = '' THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Home team name cannot be empty', 
            MYSQL_ERRNO = 2002;
    END IF;
    
    IF p_away_team IS NULL OR p_away_team = '' THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Away team name cannot be empty', 
            MYSQL_ERRNO = 2003;
    END IF;
    
    IF p_start_time IS NULL THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Start time cannot be null', 
            MYSQL_ERRNO = 2004;
    END IF;
    
    IF p_api_game_id IS NULL THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'API game ID cannot be null', 
            MYSQL_ERRNO = 2005;
    END IF;
    
    START TRANSACTION;
    
    INSERT INTO Fixture (
        home_team, 
        away_team, 
        start_time, 
        home_score, 
        away_score, 
        completed, 
        api_game_id, 
        season
    ) VALUES (
        p_home_team, 
        p_away_team, 
        p_start_time, 
        p_home_score, 
        p_away_score, 
        p_completed, 
        p_api_game_id, 
        p_season
    )
    ON DUPLICATE KEY UPDATE
        home_team = VALUES(home_team),
        away_team = VALUES(away_team),
        start_time = VALUES(start_time),
        home_score = VALUES(home_score),
        away_score = VALUES(away_score),
        completed = VALUES(completed),
        season = VALUES(season);
    
    COMMIT;
END$$
DELIMITER ;

-- Procedure to bulk clear fixtures for a season
DELIMITER $$
CREATE PROCEDURE clear_season_fixtures(
    IN p_season VARCHAR(10)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Failed to clear season fixtures', 
            MYSQL_ERRNO = 3001;
    END;
    
    -- Input validation
    IF p_season IS NULL OR p_season = '' THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Season parameter cannot be empty', 
            MYSQL_ERRNO = 3002;
    END IF;
    
    START TRANSACTION;
    
    DELETE FROM Fixture WHERE season = p_season;
    
    SELECT ROW_COUNT() as deleted_count;
    
    COMMIT;
END$$
DELIMITER ;

-- Procedure to get fixture statistics for a season
DELIMITER $$
CREATE PROCEDURE get_season_stats(
    IN p_season VARCHAR(10)
)
BEGIN
    DECLARE fixture_count INT DEFAULT 0;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Failed to retrieve season statistics', 
            MYSQL_ERRNO = 4001;
    END;
    
    -- Input validation
    IF p_season IS NULL OR p_season = '' THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Season parameter cannot be empty', 
            MYSQL_ERRNO = 4002;
    END IF;
    
    -- Check if season exists
    SELECT COUNT(*) INTO fixture_count 
    FROM Fixture 
    WHERE season = p_season;
    
    IF fixture_count = 0 THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'No fixtures found for the specified season', 
            MYSQL_ERRNO = 4003;
    END IF;
    
    SELECT 
        COUNT(*) as total_fixtures,
        SUM(CASE WHEN completed = TRUE THEN 1 ELSE 0 END) as completed_games,
        SUM(CASE WHEN completed = FALSE THEN 1 ELSE 0 END) as upcoming_games,
        MIN(start_time) as first_game,
        MAX(start_time) as last_game
    FROM Fixture 
    WHERE season = p_season;
END$$
DELIMITER ;

-- Procedure to check if required tables exist
DELIMITER $$
CREATE PROCEDURE check_required_tables()
BEGIN
    DECLARE table_count INT DEFAULT 0;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Failed to check required tables', 
            MYSQL_ERRNO = 5001;
    END;
    
    -- Check if database exists
    IF DATABASE() IS NULL THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'No database selected', 
            MYSQL_ERRNO = 5002;
    END IF;
    
    SELECT TABLE_NAME 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME IN ('User', 'Group', 'UserGroups', 'Fixture', 'Prediction', 'Leaderboard');
END$$
DELIMITER ;

-- Procedure to create a new user
DELIMITER $$
CREATE PROCEDURE create_user(
    IN p_username VARCHAR(50),
    IN p_email VARCHAR(100),
    IN p_password VARCHAR(255)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    -- Input validation
    IF p_username IS NULL OR p_username = '' THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Username cannot be empty', 
            MYSQL_ERRNO = 3000;
    END IF;
    
    IF p_email IS NULL OR p_email = '' THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Email cannot be empty', 
            MYSQL_ERRNO = 3000;
    END IF;
    
    IF p_password IS NULL OR p_password = '' THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Password cannot be empty', 
            MYSQL_ERRNO = 3000;
    END IF;
    
    -- Check for duplicate username
    IF EXISTS (SELECT 1 FROM User WHERE username = p_username) THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Username already exists', 
            MYSQL_ERRNO = 3001;
    END IF;
    
    -- Check for duplicate email
    IF EXISTS (SELECT 1 FROM User WHERE email = p_email) THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Email already exists', 
            MYSQL_ERRNO = 3002;
    END IF;
    
    START TRANSACTION;
    
    INSERT INTO User (username, email, password) 
    VALUES (p_username, p_email, p_password);
    
    -- Return the created user
    SELECT 
        user_id,
        username,
        email,
        created_at
    FROM User 
    WHERE user_id = LAST_INSERT_ID();
    
    COMMIT;
END$$
DELIMITER ;

-- Procedure to get user for login (includes password)
DELIMITER $$
CREATE PROCEDURE get_user_for_login(
    IN p_username_or_email VARCHAR(100)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Failed to retrieve user for login', 
            MYSQL_ERRNO = 3003;
    END;
    
    SELECT 
        user_id,
        username,
        email,
        password,
        created_at
    FROM User 
    WHERE username = p_username_or_email 
       OR email = p_username_or_email
    LIMIT 1;
END$$
DELIMITER ;

-- Procedure to get user by ID (without password)
DELIMITER $$
CREATE PROCEDURE get_user_by_id(
    IN p_user_id INT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Failed to retrieve user by ID', 
            MYSQL_ERRNO = 3004;
    END;
    
    IF p_user_id IS NULL OR p_user_id <= 0 THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Invalid user ID', 
            MYSQL_ERRNO = 3005;
    END IF;
    
    SELECT 
        user_id,
        username,
        email,
        created_at
    FROM User 
    WHERE user_id = p_user_id;
END$$
DELIMITER ;

-- Procedure to get user by username (without password)
DELIMITER $$
CREATE PROCEDURE get_user_by_username(
    IN p_username VARCHAR(50)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Failed to retrieve user by username', 
            MYSQL_ERRNO = 3006;
    END;
    
    IF p_username IS NULL OR p_username = '' THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Username cannot be empty', 
            MYSQL_ERRNO = 3000;
    END IF;
    
    SELECT 
        user_id,
        username,
        email,
        created_at
    FROM User 
    WHERE username = p_username;
END$$
DELIMITER ;

-- Procedure to check if username exists
DELIMITER $$
CREATE PROCEDURE check_username_exists(
    IN p_username VARCHAR(50)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Failed to check username existence', 
            MYSQL_ERRNO = 3007;
    END;
    
    SELECT COUNT(*) as `exists`  -- FIXED: escaped reserved word
    FROM User 
    WHERE username = p_username;
END$$
DELIMITER ;

-- Procedure to check if email exists
DELIMITER $$
CREATE PROCEDURE check_email_exists(
    IN p_email VARCHAR(100)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Failed to check email existence', 
            MYSQL_ERRNO = 3008;
    END;
    
    SELECT COUNT(*) as `exists`  -- FIXED: escaped reserved word
    FROM User 
    WHERE email = p_email;
END$$
DELIMITER ;

-- Procedure to get user statistics
DELIMITER $$
CREATE PROCEDURE get_user_stats(
    IN p_user_id INT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Failed to retrieve user statistics', 
            MYSQL_ERRNO = 3009;
    END;
    
    IF p_user_id IS NULL OR p_user_id <= 0 THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Invalid user ID', 
            MYSQL_ERRNO = 3005;
    END IF;
    
    SELECT 
        COALESCE(COUNT(p.pid), 0) as total_predictions,
        COALESCE(SUM(p.points_earned), 0) as total_points,
        COALESCE(COUNT(DISTINCT ug.group_id), 0) as groups_count,
        CASE 
            WHEN COUNT(p.pid) > 0 THEN 
                ROUND((SUM(CASE WHEN p.points_earned > 0 THEN 1 ELSE 0 END) * 100.0) / COUNT(p.pid), 2)
            ELSE 0.0 
        END as accuracy_percentage
    FROM User u
    LEFT JOIN UserGroups ug ON u.user_id = ug.user_id
    LEFT JOIN Prediction p ON u.user_id = p.user_id
    WHERE u.user_id = p_user_id
    GROUP BY u.user_id;
END$$
DELIMITER ;

-- End of procedures.sql