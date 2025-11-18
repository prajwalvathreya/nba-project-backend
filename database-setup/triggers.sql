-- -- This SQL script contains triggers for the NBA database setup
USE nba_db;

-- Drop existing triggers to avoid conflicts
DROP TRIGGER IF EXISTS before_group_insert;
DROP TRIGGER IF EXISTS after_group_insert;
DROP TRIGGER IF EXISTS after_usergroups_insert;

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