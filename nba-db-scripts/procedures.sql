-- Stored procedure to insert or update fixtures
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
        RESIGNAL;
    END;
    
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
        RESIGNAL;
    END;
    
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