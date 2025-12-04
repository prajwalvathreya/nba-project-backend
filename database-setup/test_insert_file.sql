USE nba_db;

-- Unhashed password : Testcd CS5170

-- Insert test users
-- INSERT INTO User (username, email, password) VALUES
-- ('alice', 'alice@example.com', '$2b$12$QIo/95iW2yZ2ofNAtyJtkOdGnZ8S.zVpigUsuuBdbguPb1AyJFeqy'),
-- ('bob', 'bob@example.com', '$2b$12$QIo/95iW2yZ2ofNAtyJtkOdGnZ8S.zVpigUsuuBdbguPb1AyJFeqy'),
-- ('charlie', 'charlie@example.com', '$2b$12$QIo/95iW2yZ2ofNAtyJtkOdGnZ8S.zVpigUsuuBdbguPb1AyJFeqy'),
-- ('diana', 'diana@example.com', '$2b$12$QIo/95iW2yZ2ofNAtyJtkOdGnZ8S.zVpigUsuuBdbguPb1AyJFeqy'),
-- ('eve', 'eve@example.com', '$2b$12$QIo/95iW2yZ2ofNAtyJtkOdGnZ8S.zVpigUsuuBdbguPb1AyJFeqy'),
-- ('frank', 'frank@example.com', '$2b$12$QIo/95iW2yZ2ofNAtyJtkOdGnZ8S.zVpigUsuuBdbguPb1AyJFeqy'),
-- ('grace', 'grace@example.com', '$2b$12$QIo/95iW2yZ2ofNAtyJtkOdGnZ8S.zVpigUsuuBdbguPb1AyJFeqy'),
-- ('heidi', 'heidi@example.com', '$2b$12$QIo/95iW2yZ2ofNAtyJtkOdGnZ8S.zVpigUsuuBdbguPb1AyJFeqy');

-- SELECT * FROM User;
-- Create groups
-- INSERT INTO `Group` (group_name, creator_id) VALUES
-- ('Test League', 4),
-- ('Office Predictions', 5);

-- SELECT * FROM `Group`;
-- Add users to groups (user_id, group_id)
-- INSERT INTO UserGroups (user_id, group_id) VALUES
-- (5, 4),
-- (6, 4), 
-- (7, 4), 
-- (8, 4), 
-- (9, 4), 
-- (10, 4);

-- TO verify users in a group and when delete happens
-- SELECT username FROM User
-- JOIN UserGroups ON User.user_id = UserGroups.user_id
-- JOIN `Group` ON UserGroups.group_id = `Group`.group_id
-- WHERE group_code='Z6NH66';

-- SELECT * FROM Fixture;

SELECT * FROM Fixture WHERE start_time = '2025-12-04 19:00:00';

-- CALL get_next_fixtures();
-- SELECT * FROM Prediction WHERE locked=0;