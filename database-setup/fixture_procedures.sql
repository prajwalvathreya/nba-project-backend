-- -- This file contains stored procedures for managing fixtures

-- Drop existing procedures to avoid conflicts
DROP PROCEDURE IF EXISTS insert_fixture;
DROP PROCEDURE IF EXISTS clear_season_fixtures;
DROP PROCEDURE IF EXISTS get_season_stats;
DROP PROCEDURE IF EXISTS get_next_fixtures;
DROP PROCEDURE IF EXISTS get_upcoming_fixtures;
DROP PROCEDURE IF EXISTS get_fixture_by_id;
DROP PROCEDURE IF EXISTS get_fixtures_up_to_date;

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

-- Procedure to get upcoming fixtures at next immediate game date
DELIMITER $$

CREATE PROCEDURE get_next_fixtures()
BEGIN
    SELECT 
        match_num,
        home_team,
        away_team,
        home_score,
        away_score,
        completed,
        start_time,
        DATE(start_time) AS game_date,
        TIME(start_time) AS game_time
    FROM Fixture
    WHERE DATE(start_time) = (
        -- Find the next date with games
        SELECT MIN(DATE(start_time))
        FROM Fixture
        WHERE DATE(start_time) >= CURDATE()
    )
    ORDER BY start_time ASC;
END$$

DELIMITER ;

-- Procedure to get upcoming fixtures for the next N days
DELIMITER $$

CREATE PROCEDURE get_upcoming_fixtures(
    IN days_ahead INT
)
BEGIN
    SELECT 
        match_num,
        home_team,
        away_team,
        home_score,
        away_score,
        completed,
        start_time,
        DATE(start_time) AS game_date,
        TIME(start_time) AS game_time
    FROM Fixture
    WHERE DATE(start_time) BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL days_ahead DAY)
    ORDER BY start_time ASC;
END$$

DELIMITER ;

-- Procedure to get fixture by ID
DELIMITER $$

CREATE PROCEDURE get_fixture_by_id(
    IN p_match_num INT
)
BEGIN
    SELECT 
        match_num,
        home_team,
        away_team,
        home_score,
        away_score,
        completed,
        start_time,
        DATE(start_time) AS game_date,
        TIME(start_time) AS game_time
    FROM Fixture
    WHERE match_num = p_match_num;
END$$

DELIMITER ;

-- Procedure to get fixtures up to a specific date
DELIMITER $$

CREATE PROCEDURE get_fixtures_up_to_date(IN in_to_date DATE)
BEGIN
    SELECT *
    FROM Fixture
    WHERE DATE(start_time) <= in_to_date
    ORDER BY DATE(start_time) ASC, TIME(start_time) ASC;
END $$

DELIMITER ;