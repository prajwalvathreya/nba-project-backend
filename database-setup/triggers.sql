-- This SQL script contains triggers for certain database operations

-- Drop existing triggers to avoid conflicts
DROP TRIGGER IF EXISTS before_group_insert;
DROP TRIGGER IF EXISTS after_group_insert;
DROP TRIGGER IF EXISTS after_usergroups_insert;
DROP TRIGGER IF EXISTS before_prediction_update;
DROP TRIGGER IF EXISTS before_prediction_delete;
DROP TRIGGER IF EXISTS before_fixture_update;
DROP TRIGGER IF EXISTS after_fixture_complete;

-- ============================================================================
-- GROUP TRIGGERS
-- ============================================================================

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

-- ============================================================================
-- PREDICTION LOCKING TRIGGERS
-- ============================================================================

-- Trigger to prevent updates to locked predictions (but allow system scoring)
DELIMITER $$
CREATE TRIGGER before_prediction_update 
BEFORE UPDATE ON Prediction
FOR EACH ROW
BEGIN
    DECLARE game_started BOOLEAN;
    
    -- Check if prediction is already locked
    IF OLD.locked = 1 THEN
        -- Allow system to update points_earned even when locked
        -- Only block if user is trying to change predicted scores
        IF NEW.pred_home_score != OLD.pred_home_score OR NEW.pred_away_score != OLD.pred_away_score THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Cannot update - prediction is locked';
        END IF;
    END IF;
    
    -- Check if game has started (auto-lock)
    -- Only check this if user is trying to change predicted scores
    IF NEW.pred_home_score != OLD.pred_home_score OR NEW.pred_away_score != OLD.pred_away_score THEN
        SELECT start_time < NOW() INTO game_started
        FROM Fixture
        WHERE match_num = NEW.fixture_id;
        
        IF game_started THEN
            -- Auto-lock the prediction
            SET NEW.locked = 1;
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Cannot update - game has already started';
        END IF;
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

-- ============================================================================
-- FIXTURE AND SCORING TRIGGERS
-- ============================================================================

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

-- Trigger to auto-calculate scores and update leaderboards when fixture completes
DELIMITER $$
CREATE TRIGGER after_fixture_complete
AFTER UPDATE ON Fixture
FOR EACH ROW
BEGIN
    -- Trigger when fixture is completed OR when completed fixture scores change
    IF NEW.completed = 1 AND (
        OLD.completed = 0 OR 
        OLD.home_score != NEW.home_score OR 
        OLD.away_score != NEW.away_score
    ) THEN
        
        -- Calculate/recalculate points for all predictions for this fixture
        UPDATE Prediction p
        SET p.points_earned = calculate_prediction_points(
            p.pred_home_score,
            p.pred_away_score,
            NEW.home_score,
            NEW.away_score
        )
        WHERE p.fixture_id = NEW.match_num;
        
        -- Update leaderboard total_points for all affected groups
        UPDATE Leaderboard l
        SET l.total_points = (
            SELECT COALESCE(SUM(pred.points_earned), 0)
            FROM Prediction pred
            WHERE pred.user_id = l.user_id
            AND pred.group_id = l.group_id
            AND pred.points_earned IS NOT NULL
        ),
        l.last_updated = NOW()
        WHERE l.group_id IN (
            SELECT DISTINCT group_id 
            FROM Prediction 
            WHERE fixture_id = NEW.match_num
        );
        
        -- Update rankings for all affected groups
        UPDATE Leaderboard l
        INNER JOIN (
            SELECT 
                user_id,
                group_id,
                DENSE_RANK() OVER (
                    PARTITION BY group_id 
                    ORDER BY total_points DESC
                ) as new_rank
            FROM Leaderboard
            WHERE group_id IN (
                SELECT DISTINCT group_id 
                FROM Prediction 
                WHERE fixture_id = NEW.match_num
            )
        ) ranked ON l.user_id = ranked.user_id AND l.group_id = ranked.group_id
        SET l.rank_position = ranked.new_rank;
        
    END IF;
END$$
DELIMITER ;