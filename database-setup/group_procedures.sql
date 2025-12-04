-- -- This script contains stored procedures for managing groups

-- Drop existing procedures if they exist
DROP PROCEDURE IF EXISTS create_group;
DROP PROCEDURE IF EXISTS get_group_by_id;
DROP PROCEDURE IF EXISTS get_group_by_code;
DROP PROCEDURE IF EXISTS get_user_groups;
DROP PROCEDURE IF EXISTS join_group;
DROP PROCEDURE IF EXISTS leave_group;
DROP PROCEDURE IF EXISTS get_group_members;
DROP PROCEDURE IF EXISTS delete_group;

-- Create Group
DELIMITER $$

CREATE PROCEDURE create_group(
    IN p_group_name VARCHAR(100),
    IN p_creator_id INT
)
BEGIN
    -- Insert group (trigger will auto-generate code and add creator to UserGroups)
    INSERT INTO `Group` (group_name, creator_id)
    VALUES (p_group_name, p_creator_id);
    
    -- Return the created group
    SELECT 
        group_id,
        group_code,
        group_name,
        creator_id,
        creation_date
    FROM `Group`
    WHERE group_id = LAST_INSERT_ID();
END$$

DELIMITER ;

-- Get Group by ID
DELIMITER $$

CREATE PROCEDURE get_group_by_id(
    IN p_group_id INT
)
BEGIN
    SELECT 
        g.group_id,
        g.group_code,
        g.group_name,
        g.creator_id,
        g.creation_date,
        u.username AS creator_username,
        (SELECT COUNT(*) FROM UserGroups WHERE group_id = p_group_id) AS member_count
    FROM `Group` g
    INNER JOIN User u ON g.creator_id = u.user_id
    WHERE g.group_id = p_group_id;
END$$

DELIMITER ;

-- Get Group by Code
DELIMITER $$

CREATE PROCEDURE get_group_by_code(
    IN p_group_code VARCHAR(6)
)
BEGIN
    SELECT 
        g.group_id,
        g.group_code,
        g.group_name,
        g.creator_id,
        g.creation_date,
        u.username AS creator_username,
        (SELECT COUNT(*) FROM UserGroups WHERE group_id = g.group_id) AS member_count
    FROM `Group` g
    INNER JOIN User u ON g.creator_id = u.user_id
    WHERE g.group_code = p_group_code;
END$$

DELIMITER ;

-- Get All Groups for a User
DELIMITER $$

CREATE PROCEDURE get_user_groups(
    IN p_user_id INT
)
BEGIN
    SELECT 
        g.group_id,
        g.group_code,
        g.group_name,
        g.creator_id,
        g.creation_date,
        ug.joined_date,
        u.username AS creator_username,
        (g.creator_id = p_user_id) AS is_creator,
        (SELECT COUNT(*) FROM UserGroups WHERE group_id = g.group_id) AS member_count
    FROM `Group` g
    INNER JOIN UserGroups ug ON g.group_id = ug.group_id
    INNER JOIN User u ON g.creator_id = u.user_id
    WHERE ug.user_id = p_user_id
    ORDER BY ug.joined_date DESC;
END$$

DELIMITER ;

-- Join Group (by group code)
DELIMITER $$


CREATE PROCEDURE join_group(
    IN p_user_id INT,
    IN p_group_code VARCHAR(6)
)
BEGIN
    DECLARE v_group_id INT;

    -- Find group by code
    SELECT group_id INTO v_group_id
    FROM `Group`
    WHERE group_code = p_group_code;

    -- Check if group exists
    IF v_group_id IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Group not found with that code';
    END IF;

    -- Check if user is already in the group
    IF EXISTS (
        SELECT 1 FROM UserGroups 
        WHERE user_id = p_user_id AND group_id = v_group_id
    ) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'User is already a member of this group';
    END IF;

    -- Add user to group (trigger will create leaderboard entry)
    INSERT INTO UserGroups (user_id, group_id)
    VALUES (p_user_id, v_group_id);

    -- Recalculate all leaderboards to update points and ranks
    CALL recalculate_all_leaderboards();

    -- Return the group info as the LAST statement
    SELECT 
        g.group_id,
        g.group_code,
        g.group_name,
        g.creator_id,
        g.creation_date,
        ug.joined_date
    FROM `Group` g
    INNER JOIN UserGroups ug ON g.group_id = ug.group_id
    WHERE g.group_id = v_group_id AND ug.user_id = p_user_id;
END$$

DELIMITER ;

-- Leave Group
DELIMITER $$

CREATE PROCEDURE leave_group(
    IN p_user_id INT,
    IN p_group_id INT
)
BEGIN
    DECLARE v_creator_id INT;
    
    -- Check if user is the creator
    SELECT creator_id INTO v_creator_id
    FROM `Group`
    WHERE group_id = p_group_id;
    
    IF v_creator_id = p_user_id THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Group creator cannot leave the group. Delete the group instead.';
    END IF;
    
    -- Check if user is in the group
    IF NOT EXISTS (
        SELECT 1 FROM UserGroups 
        WHERE user_id = p_user_id AND group_id = p_group_id
    ) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'User is not a member of this group';
    END IF;
    
    -- Remove user from group (CASCADE will delete leaderboard entry)
    DELETE FROM UserGroups
    WHERE user_id = p_user_id AND group_id = p_group_id;
    
    SELECT ROW_COUNT() as left_group;
END$$

DELIMITER ;

-- Get Group Members
DELIMITER $$

CREATE PROCEDURE get_group_members(
    IN p_group_id INT
)
BEGIN
    SELECT 
        u.user_id,
        u.username,
        u.email,
        ug.joined_date,
        (u.user_id = g.creator_id) AS is_creator,
        COALESCE(l.total_points, 0) AS total_points,
        l.rank_position
    FROM UserGroups ug
    INNER JOIN User u ON ug.user_id = u.user_id
    INNER JOIN `Group` g ON ug.group_id = g.group_id
    LEFT JOIN Leaderboard l ON ug.user_id = l.user_id AND ug.group_id = l.group_id
    WHERE ug.group_id = p_group_id
    ORDER BY ug.joined_date ASC;
END$$

DELIMITER ;

-- Delete Group (only by creator)
DELIMITER $$

CREATE PROCEDURE delete_group(
    IN p_group_id INT,
    IN p_user_id INT
)
BEGIN
    DECLARE v_creator_id INT;
    
    -- Check if user is the creator
    SELECT creator_id INTO v_creator_id
    FROM `Group`
    WHERE group_id = p_group_id;
    
    IF v_creator_id IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Group not found';
    END IF;
    
    IF v_creator_id != p_user_id THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Only the group creator can delete the group';
    END IF;
    
    -- Delete group (CASCADE will delete UserGroups and Leaderboard entries)
    DELETE FROM `Group`
    WHERE group_id = p_group_id;
    
    SELECT ROW_COUNT() as deleted_count;
END$$

DELIMITER ;