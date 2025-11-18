-- -- This SQL script contains triggers for certain database operations
USE nba_db;

-- Drop existing triggers to avoid conflicts
DROP TRIGGER IF EXISTS before_group_insert;
DROP TRIGGER IF EXISTS after_group_insert;
DROP TRIGGER IF EXISTS after_usergroups_insert;
DROP TRIGGER IF EXISTS before_prediction_update;
DROP TRIGGER IF EXISTS before_prediction_delete;
DROP TRIGGER IF EXISTS before_fixture_update;

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

-- Trigger to prevent updates to locked predictions
DELIMITER $$
CREATE TRIGGER before_prediction_update 
BEFORE UPDATE ON Prediction
FOR EACH ROW
BEGIN
    DECLARE game_started BOOLEAN;
    
    -- Check if prediction is already locked
    IF OLD.locked = 1 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot update - prediction is locked';
    END IF;
    
    -- Check if game has started (auto-lock)
    SELECT start_time < NOW() INTO game_started
    FROM Fixture
    WHERE match_num = NEW.fixture_id;
    
    IF game_started THEN
        -- Auto-lock the prediction
        SET NEW.locked = 1;
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot update - game has already started';
    END IF;
END$$
DELIMITER ;

-- Trigger to prevent deletion of locked predictions
DELIMITER $$
CREATE TRIGGER before_prediction_delete 
BEFORE DELETE ON Prediction
FOR EACH ROW
BEGIN
    DECLARE game_started BOOLEAN;
    
    -- Check if prediction is locked
    IF OLD.locked = 1 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot delete - prediction is locked';
    END IF;
    
    -- Check if game has started
    SELECT start_time < NOW() INTO game_started
    FROM Fixture
    WHERE match_num = OLD.fixture_id;
    
    IF game_started THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot delete - game has already started';
    END IF;
END$$
DELIMITER ;

-- Trigger to auto-lock predictions when game starts or is marked completed
DELIMITER $$
CREATE TRIGGER before_fixture_update 
BEFORE UPDATE ON Fixture
FOR EACH ROW
BEGIN
    -- If game is being marked as started or completed, lock all predictions
    IF NEW.start_time <= NOW() OR NEW.completed = 1 THEN
        UPDATE Prediction
        SET locked = 1
        WHERE fixture_id = NEW.match_num AND locked = 0;
    END IF;
END$$
DELIMITER ;