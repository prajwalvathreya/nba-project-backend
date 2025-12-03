-- -- This script defines stored procedures for managing predictions

-- Drop existing procedures if they exist
DROP PROCEDURE IF EXISTS create_prediction;
DROP PROCEDURE IF EXISTS get_user_predictions;
DROP PROCEDURE IF EXISTS get_all_user_predictions;
DROP PROCEDURE IF EXISTS get_fixture_predictions;
DROP PROCEDURE IF EXISTS get_prediction_by_id;
DROP PROCEDURE IF EXISTS update_prediction;
DROP PROCEDURE IF EXISTS delete_prediction;
DROP PROCEDURE IF EXISTS get_user_predictions_by_match_range;

-- Create Prediction
DELIMITER $$

CREATE PROCEDURE create_prediction(
    IN p_user_id INT,
    IN p_group_id INT,
    IN p_fixture_id INT,
    IN p_pred_home_score INT,
    IN p_pred_away_score INT
)
BEGIN
    DECLARE game_started BOOLEAN;
    
    -- Check if game has already started
    SELECT start_time < NOW() INTO game_started
    FROM Fixture
    WHERE match_num = p_fixture_id;
    
    IF game_started THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot predict - game has already started';
    END IF;
    
    -- Check if prediction already exists for this user, group, and fixture
    IF EXISTS (
        SELECT 1 FROM Prediction 
        WHERE user_id = p_user_id 
        AND group_id = p_group_id 
        AND fixture_id = p_fixture_id
    ) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Prediction already exists for this game in this group';
    END IF;
    
    -- Insert prediction
    INSERT INTO Prediction (
        user_id, 
        group_id,
        fixture_id, 
        pred_home_score, 
        pred_away_score,
        prediction_time,
        locked,
        points_earned
    )
    VALUES (
        p_user_id,
        p_group_id,
        p_fixture_id, 
        p_pred_home_score, 
        p_pred_away_score,
        NOW(),
        0,
        NULL
    );
    
    -- Return the created prediction with fixture details
    SELECT 
        p.pid,
        p.user_id,
        p.group_id,
        p.fixture_id,
        p.pred_home_score,
        p.pred_away_score,
        p.prediction_time,
        p.locked,
        p.points_earned,
        f.home_team,
        f.away_team,
        f.start_time,
        f.completed,
        f.home_score AS actual_home_score,
        f.away_score AS actual_away_score,
        DATE(f.start_time) AS game_date,
        TIME(f.start_time) AS game_time
    FROM Prediction p
    INNER JOIN Fixture f ON p.fixture_id = f.match_num
    WHERE p.pid = LAST_INSERT_ID();
END$$

DELIMITER ;

-- Get User's Predictions in a Specific Group
DELIMITER $$

CREATE PROCEDURE get_user_predictions(
    IN p_user_id INT,
    IN p_group_id INT
)
BEGIN
    SELECT 
        p.pid,
        p.user_id,
        p.group_id,
        p.fixture_id,
        p.pred_home_score,
        p.pred_away_score,
        p.prediction_time,
        p.locked,
        p.points_earned,
        f.home_team,
        f.away_team,
        f.start_time,
        f.completed,
        f.home_score AS actual_home_score,
        f.away_score AS actual_away_score,
        DATE(f.start_time) AS game_date,
        TIME(f.start_time) AS game_time
    FROM Prediction p
    INNER JOIN Fixture f ON p.fixture_id = f.match_num
    WHERE p.user_id = p_user_id
    AND p.group_id = p_group_id
    ORDER BY f.start_time DESC;
END$$

DELIMITER ;

-- Get All User's Predictions (Across All Groups)
DELIMITER $$

CREATE PROCEDURE get_all_user_predictions(
    IN p_user_id INT
)
BEGIN
    SELECT 
        p.pid,
        p.user_id,
        p.group_id,
        p.fixture_id,
        p.pred_home_score,
        p.pred_away_score,
        p.prediction_time,
        p.locked,
        p.points_earned,
        f.home_team,
        f.away_team,
        f.start_time,
        f.completed,
        f.home_score AS actual_home_score,
        f.away_score AS actual_away_score,
        DATE(f.start_time) AS game_date,
        TIME(f.start_time) AS game_time
    FROM Prediction p
    INNER JOIN Fixture f ON p.fixture_id = f.match_num
    WHERE p.user_id = p_user_id
    ORDER BY f.start_time DESC;
END$$

DELIMITER ;

-- Get Predictions for a Fixture (in a specific group)
DELIMITER $$
CREATE PROCEDURE get_fixture_predictions(
    IN p_fixture_id INT,
    IN p_group_id INT
)
BEGIN
    SELECT 
        p.pid,
        p.user_id,
        u.username,
        p.pred_home_score,
        p.pred_away_score,
        p.prediction_time,
        p.locked,
        p.points_earned
    FROM Prediction p
    INNER JOIN User u ON p.user_id = u.user_id
    WHERE p.fixture_id = p_fixture_id
    AND p.group_id = p_group_id
    ORDER BY p.prediction_time ASC;
END$$

DELIMITER ;

-- Get Single Prediction by ID
DELIMITER $$
CREATE PROCEDURE get_prediction_by_id(
    IN p_pid INT
)
BEGIN
    SELECT 
        p.pid,
        p.user_id,
        p.group_id,
        p.fixture_id,
        p.pred_home_score,
        p.pred_away_score,
        p.prediction_time,
        p.locked,
        p.points_earned,
        f.home_team,
        f.away_team,
        f.start_time,
        f.completed,
        f.home_score AS actual_home_score,
        f.away_score AS actual_away_score,
        DATE(f.start_time) AS game_date,
        TIME(f.start_time) AS game_time
    FROM Prediction p
    INNER JOIN Fixture f ON p.fixture_id = f.match_num
    WHERE p.pid = p_pid;
END$$

DELIMITER ;

-- Update Prediction (Before Game Starts)
DELIMITER $$
CREATE PROCEDURE update_prediction(
    IN p_user_id INT,
    IN p_group_id INT,
    IN p_fixture_id INT,
    IN p_pred_home_score INT,
    IN p_pred_away_score INT
)
BEGIN
    DECLARE v_pid INT;
    
    -- Find the prediction using user_id, group_id, fixture_id
    SELECT pid INTO v_pid
    FROM Prediction
    WHERE user_id = p_user_id 
    AND group_id = p_group_id 
    AND fixture_id = p_fixture_id;
    
    -- Check if prediction exists
    IF v_pid IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Prediction not found for this user, group, and fixture';
    END IF;
    
    -- Update prediction (trigger will check if locked/game started)
    UPDATE Prediction
    SET 
        pred_home_score = p_pred_home_score,
        pred_away_score = p_pred_away_score,
        prediction_time = NOW()
    WHERE pid = v_pid;
    
    -- Return updated prediction
    SELECT 
        p.pid,
        p.user_id,
        p.group_id,
        p.fixture_id,
        p.pred_home_score,
        p.pred_away_score,
        p.prediction_time,
        p.locked,
        p.points_earned,
        f.home_team,
        f.away_team,
        f.start_time,
        f.completed,
        f.home_score AS actual_home_score,
        f.away_score AS actual_away_score,
        DATE(f.start_time) AS game_date,
        TIME(f.start_time) AS game_time
    FROM Prediction p
    INNER JOIN Fixture f ON p.fixture_id = f.match_num
    WHERE p.pid = v_pid;
END$$

DELIMITER ;

-- Delete Prediction (Before Game Starts)
DELIMITER $$
DROP PROCEDURE IF EXISTS delete_prediction$$

CREATE PROCEDURE delete_prediction(
    IN p_user_id INT,
    IN p_group_id INT,
    IN p_fixture_id INT
)
BEGIN
    DECLARE v_pid INT;
    
    -- Find the prediction using user_id, group_id, fixture_id
    SELECT pid INTO v_pid
    FROM Prediction
    WHERE user_id = p_user_id 
    AND group_id = p_group_id 
    AND fixture_id = p_fixture_id;
    
    -- Check if prediction exists
    IF v_pid IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Prediction not found for this user, group, and fixture';
    END IF;
    
    -- Delete prediction (trigger will check if locked/game started)
    DELETE FROM Prediction
    WHERE pid = v_pid;
    
    SELECT ROW_COUNT() as deleted_count;
END$$

DELIMITER ;

-- Get User's Predictions by Match Number Range (for pagination)
DELIMITER $$
CREATE PROCEDURE get_user_predictions_by_match_range(
    IN p_user_id INT,
    IN p_min_match_num INT,
    IN p_max_match_num INT
)
BEGIN
    SELECT 
        p.pid,
        p.user_id,
        p.group_id,
        p.fixture_id,
        p.pred_home_score,
        p.pred_away_score,
        p.prediction_time,
        p.locked,
        p.points_earned,
        f.home_team,
        f.away_team,
        f.start_time,
        f.completed,
        f.home_score AS actual_home_score,
        f.away_score AS actual_away_score,
        DATE(f.start_time) AS game_date,
        TIME(f.start_time) AS game_time
    FROM Prediction p
    INNER JOIN Fixture f ON p.fixture_id = f.match_num
    INNER JOIN (
        SELECT fixture_id, MAX(prediction_time) AS max_time
        FROM Prediction
        WHERE user_id = p_user_id
          AND fixture_id BETWEEN p_min_match_num AND p_max_match_num
        GROUP BY fixture_id
    ) latest ON p.fixture_id = latest.fixture_id AND p.prediction_time = latest.max_time
    WHERE p.user_id = p_user_id
      AND f.match_num >= p_min_match_num
      AND f.match_num <= p_max_match_num
    ORDER BY f.match_num DESC;
END$$
DELIMITER ;