-- This SQL script defines stored procedures for managing and retrieving leaderboard data
USE nba_db;

-- Drop existing procedures if they exist
DROP PROCEDURE IF EXISTS get_group_leaderboard;
DROP PROCEDURE IF EXISTS get_user_rank_in_group;
DROP PROCEDURE IF EXISTS complete_fixture;
DROP PROCEDURE IF EXISTS update_fixture_scores;
DROP PROCEDURE IF EXISTS recalculate_all_leaderboards;

-- Get Group Leaderboard
DELIMITER $$

CREATE PROCEDURE get_group_leaderboard(
    IN p_group_id INT
)
BEGIN
    SELECT 
        l.user_id,
        u.username,
        u.email,
        l.total_points,
        l.rank_position,
        l.last_updated,
        COUNT(p.pid) as total_predictions,
        SUM(CASE WHEN p.points_earned IS NOT NULL THEN 1 ELSE 0 END) as scored_predictions,
        SUM(CASE WHEN p.points_earned = 10 THEN 1 ELSE 0 END) as exact_predictions,
        ROUND(AVG(CASE WHEN p.points_earned IS NOT NULL THEN p.points_earned END), 2) as avg_points_per_prediction
    FROM Leaderboard l
    INNER JOIN User u ON l.user_id = u.user_id
    LEFT JOIN Prediction p ON l.user_id = p.user_id AND l.group_id = p.group_id
    WHERE l.group_id = p_group_id
    GROUP BY l.user_id, u.username, u.email, l.total_points, l.rank_position, l.last_updated
    ORDER BY l.rank_position ASC, l.total_points DESC;
END$$

DELIMITER ;

-- Get User's Rank in Group
DELIMITER $$

CREATE PROCEDURE get_user_rank_in_group(
    IN p_user_id INT,
    IN p_group_id INT
)
BEGIN
    SELECT 
        l.user_id,
        u.username,
        l.total_points,
        l.rank_position,
        l.last_updated,
        COUNT(p.pid) as total_predictions,
        SUM(CASE WHEN p.points_earned IS NOT NULL THEN 1 ELSE 0 END) as scored_predictions,
        SUM(CASE WHEN p.points_earned = 10 THEN 1 ELSE 0 END) as exact_predictions,
        ROUND(AVG(CASE WHEN p.points_earned IS NOT NULL THEN p.points_earned END), 2) as avg_points_per_prediction,
        (SELECT COUNT(*) FROM Leaderboard WHERE group_id = p_group_id) as total_players
    FROM Leaderboard l
    INNER JOIN User u ON l.user_id = u.user_id
    LEFT JOIN Prediction p ON l.user_id = p.user_id AND l.group_id = p.group_id
    WHERE l.user_id = p_user_id
    AND l.group_id = p_group_id
    GROUP BY l.user_id, u.username, l.total_points, l.rank_position, l.last_updated;
END$$

DELIMITER ;

-- Complete Fixture (Admin Only - First Time)
DELIMITER $$

CREATE PROCEDURE complete_fixture(
    IN p_fixture_id INT,
    IN p_home_score INT,
    IN p_away_score INT
)
BEGIN
    DECLARE v_already_completed BOOLEAN;
    
    -- Check if fixture exists and if already completed
    SELECT completed INTO v_already_completed
    FROM Fixture
    WHERE match_num = p_fixture_id;
    
    IF v_already_completed IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Fixture not found';
    END IF;
    
    IF v_already_completed = 1 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Fixture is already completed. Use update_fixture_scores to correct scores.';
    END IF;
    
    -- Update fixture with final scores and mark as completed
    -- This will trigger after_fixture_complete which handles scoring and leaderboard updates
    UPDATE Fixture
    SET 
        home_score = p_home_score,
        away_score = p_away_score,
        completed = 1
    WHERE match_num = p_fixture_id;
    
    -- Return the updated fixture
    SELECT 
        match_num,
        home_team,
        away_team,
        home_score,
        away_score,
        completed,
        start_time,
        (SELECT COUNT(*) FROM Prediction WHERE fixture_id = p_fixture_id) as total_predictions,
        (SELECT COUNT(*) FROM Prediction WHERE fixture_id = p_fixture_id AND points_earned IS NOT NULL) as predictions_scored
    FROM Fixture
    WHERE match_num = p_fixture_id;
END$$

DELIMITER ;

-- Update Fixture Scores (Admin Only - Correction After Completion)
DELIMITER $$

CREATE PROCEDURE update_fixture_scores(
    IN p_fixture_id INT,
    IN p_home_score INT,
    IN p_away_score INT
)
BEGIN
    DECLARE v_completed BOOLEAN;
    DECLARE v_old_home_score INT;
    DECLARE v_old_away_score INT;
    
    -- Check if fixture exists and get current scores
    SELECT completed, home_score, away_score 
    INTO v_completed, v_old_home_score, v_old_away_score
    FROM Fixture
    WHERE match_num = p_fixture_id;
    
    IF v_completed IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Fixture not found';
    END IF;
    
    IF v_completed = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Fixture is not completed yet. Use complete_fixture instead.';
    END IF;
    
    -- Check if scores are actually different
    IF v_old_home_score = p_home_score AND v_old_away_score = p_away_score THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'New scores are the same as current scores. No update needed.';
    END IF;
    
    -- Reset points for this fixture (will be recalculated by trigger)
    UPDATE Prediction
    SET points_earned = NULL
    WHERE fixture_id = p_fixture_id;
    
    -- Update fixture scores (this will trigger after_fixture_complete to recalculate)
    UPDATE Fixture
    SET 
        home_score = p_home_score,
        away_score = p_away_score,
        completed = 1
    WHERE match_num = p_fixture_id;
    
    -- The trigger automatically recalculates points and updates leaderboards
    
    -- Return updated fixture info
    SELECT 
        match_num,
        home_team,
        away_team,
        home_score,
        away_score,
        completed,
        start_time,
        (SELECT COUNT(*) FROM Prediction WHERE fixture_id = p_fixture_id) as total_predictions,
        (SELECT COUNT(*) FROM Prediction WHERE fixture_id = p_fixture_id AND points_earned IS NOT NULL) as predictions_scored
    FROM Fixture
    WHERE match_num = p_fixture_id;
END$$

DELIMITER ;

-- Recalculate All Leaderboards (Utility function for maintenance)
DELIMITER $$

CREATE PROCEDURE recalculate_all_leaderboards()
BEGIN
    -- Recalculate total points for all users in all groups
    UPDATE Leaderboard l
    SET l.total_points = (
        SELECT COALESCE(SUM(p.points_earned), 0)
        FROM Prediction p
        WHERE p.user_id = l.user_id
        AND p.group_id = l.group_id
        AND p.points_earned IS NOT NULL
    ),
    l.last_updated = NOW();
    
    -- Recalculate rankings for all groups
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
    ) ranked ON l.user_id = ranked.user_id AND l.group_id = ranked.group_id
    SET l.rank_position = ranked.new_rank;
    
    SELECT 
        COUNT(DISTINCT group_id) as groups_updated,
        COUNT(*) as users_updated,
        SUM(total_points) as total_points_awarded
    FROM Leaderboard;
END$$

DELIMITER ;