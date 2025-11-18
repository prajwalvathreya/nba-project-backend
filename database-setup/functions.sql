-- -- This SQL script contains functions for doing various operations regarding groups, predictions and scoring
USE nba_db;

-- Drop existing functions to avoid conflicts
DROP FUNCTION IF EXISTS generate_group_code;
DROP FUNCTION IF EXISTS calculate_prediction_points;

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