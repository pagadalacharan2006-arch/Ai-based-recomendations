-- AI-Based Recommendation System Using Graph Structures
-- MySQL 8.0.16+ (CHECK constraints are enforced from 8.0.16 onward).
-- Graph links are represented by user-item interactions/ratings/saves,
-- user-category interests, and item-category membership.

CREATE DATABASE IF NOT EXISTS ai_graph_recommendation
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

USE ai_graph_recommendation;

CREATE TABLE IF NOT EXISTS users (
  user_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  username VARCHAR(50) NOT NULL,
  email VARCHAR(254) NOT NULL,
  display_name VARCHAR(120) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id),
  UNIQUE KEY uq_users_username (username),
  UNIQUE KEY uq_users_email (email),
  KEY idx_users_active_created (is_active, created_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS categories (
  category_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  parent_category_id BIGINT UNSIGNED NULL,
  name VARCHAR(100) NOT NULL,
  slug VARCHAR(120) NOT NULL,
  description VARCHAR(500) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (category_id),
  UNIQUE KEY uq_categories_slug (slug),
  KEY idx_categories_parent (parent_category_id),
  CONSTRAINT fk_categories_parent
    FOREIGN KEY (parent_category_id) REFERENCES categories (category_id)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS items (
  item_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  category_id BIGINT UNSIGNED NOT NULL,
  item_type VARCHAR(40) NOT NULL DEFAULT 'product',
  title VARCHAR(200) NOT NULL,
  description TEXT NULL,
  item_url VARCHAR(2048) NULL,
  attributes JSON NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (item_id),
  KEY idx_items_category_active (category_id, is_active),
  KEY idx_items_type_active (item_type, is_active),
  KEY idx_items_created (created_at),
  CONSTRAINT fk_items_category
    FOREIGN KEY (category_id) REFERENCES categories (category_id)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS user_interests (
  user_id BIGINT UNSIGNED NOT NULL,
  category_id BIGINT UNSIGNED NOT NULL,
  interest_weight DECIMAL(6,5) NOT NULL DEFAULT 1.00000,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id, category_id),
  KEY idx_user_interests_category_weight (category_id, interest_weight),
  CONSTRAINT chk_user_interests_weight
    CHECK (interest_weight > 0 AND interest_weight <= 1),
  CONSTRAINT fk_user_interests_user
    FOREIGN KEY (user_id) REFERENCES users (user_id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_user_interests_category
    FOREIGN KEY (category_id) REFERENCES categories (category_id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS interactions (
  interaction_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  item_id BIGINT UNSIGNED NOT NULL,
  interaction_type ENUM('view', 'click', 'like', 'share', 'purchase', 'dismiss') NOT NULL,
  strength DECIMAL(7,3) NOT NULL DEFAULT 1.000,
  occurred_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (interaction_id),
  KEY idx_interactions_user_type_time (user_id, interaction_type, occurred_at),
  KEY idx_interactions_item_type_time (item_id, interaction_type, occurred_at),
  KEY idx_interactions_time (occurred_at),
  CONSTRAINT chk_interactions_strength CHECK (strength > 0),
  CONSTRAINT fk_interactions_user
    FOREIGN KEY (user_id) REFERENCES users (user_id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_interactions_item
    FOREIGN KEY (item_id) REFERENCES items (item_id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS ratings (
  rating_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  item_id BIGINT UNSIGNED NOT NULL,
  rating TINYINT UNSIGNED NOT NULL,
  review_text VARCHAR(1000) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (rating_id),
  UNIQUE KEY uq_ratings_user_item (user_id, item_id),
  KEY idx_ratings_item_rating (item_id, rating),
  CONSTRAINT chk_ratings_value CHECK (rating BETWEEN 1 AND 5),
  CONSTRAINT fk_ratings_user
    FOREIGN KEY (user_id) REFERENCES users (user_id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_ratings_item
    FOREIGN KEY (item_id) REFERENCES items (item_id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS saved_items (
  user_id BIGINT UNSIGNED NOT NULL,
  item_id BIGINT UNSIGNED NOT NULL,
  saved_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id, item_id),
  KEY idx_saved_items_item_time (item_id, saved_at),
  CONSTRAINT fk_saved_items_user
    FOREIGN KEY (user_id) REFERENCES users (user_id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_saved_items_item
    FOREIGN KEY (item_id) REFERENCES items (item_id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS recommendation_history (
  recommendation_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  run_id CHAR(36) NOT NULL,
  user_id BIGINT UNSIGNED NOT NULL,
  item_id BIGINT UNSIGNED NOT NULL,
  score DECIMAL(8,7) NOT NULL,
  rank_position INT UNSIGNED NOT NULL,
  algorithm_name VARCHAR(100) NOT NULL,
  generated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (recommendation_id),
  UNIQUE KEY uq_recommendations_run_user_item (run_id, user_id, item_id),
  UNIQUE KEY uq_recommendations_run_user_rank (run_id, user_id, rank_position),
  KEY idx_recommendations_user_time (user_id, generated_at),
  KEY idx_recommendations_item_time (item_id, generated_at),
  CONSTRAINT chk_recommendations_score CHECK (score >= 0 AND score <= 1),
  CONSTRAINT chk_recommendations_rank CHECK (rank_position > 0),
  CONSTRAINT fk_recommendations_user
    FOREIGN KEY (user_id) REFERENCES users (user_id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_recommendations_item
    FOREIGN KEY (item_id) REFERENCES items (item_id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Sample users
INSERT INTO users (user_id, username, email, display_name, password_hash) VALUES
  (1, 'maya_chen', 'maya.chen@example.test', 'Maya Chen', 'scrypt:32768:8:1$LiJyzK4UJL3P5zD1$fd05dbca1ad830fd5e89dbc8c8369e5107b4311bb858e441eae399d2353cf087499202b5a819145d8ed9187f90c020ebcec732817136eec60402afa27c8ca7af'),
  (2, 'noah_patel', 'noah.patel@example.test', 'Noah Patel', 'scrypt:32768:8:1$c5rjbbjnbF3Mh0Up$108a77ca99bd3119c21468a8538a49a7ca6e482c8a07cfa2636f7046e31d42a85c116c010e235afa0f72d9f932fac3be916a8fc81c2c520ba1eb01f4b485c986'),
  (3, 'sofia_reyes', 'sofia.reyes@example.test', 'Sofia Reyes', 'scrypt:32768:8:1$9skx5IONJ1HMDQIC$9ecfb31098c1b136233a08a3d2d6a31381b3d3d05907092f4203e196234de67e8c56ddd4bfdc5402510257bb643e19ef8ed1d86cb525fe44f81fa4da21d50e95'),
  (4, 'liam_brooks', 'liam.brooks@example.test', 'Liam Brooks', 'scrypt:32768:8:1$rq4ka7J9JAwB91Qh$ad476ca65a620b49f27a92ca899517cacd71e54a13900a9d189cc3d066c786ca258f8ba50543af23e40d45132a371974e8c12ce0ec6da7673382a7b9f33af8c4'),
  (5, 'ava_kim', 'ava.kim@example.test', 'Ava Kim', 'scrypt:32768:8:1$5Uo80cKkmsgCANNh$5e35d8e25b2f99d846d9cfaff93860154a9754394cb026ffaeeb7f5175ccbd3960d85a9ad0b95faddff4ad4fa41bf8c6136e52e35133934ceba040e3af01845c')
ON DUPLICATE KEY UPDATE
  username = VALUES(username),
  email = VALUES(email),
  display_name = VALUES(display_name),
  password_hash = VALUES(password_hash);

-- Sample category tree
INSERT INTO categories (category_id, parent_category_id, name, slug, description) VALUES
  (1, NULL, 'Books', 'books', 'Printed and digital books'),
  (2, NULL, 'Technology', 'technology', 'Computers and consumer electronics'),
  (3, NULL, 'Home and Garden', 'home-garden', 'Home improvement and gardening'),
  (4, NULL, 'Outdoor', 'outdoor', 'Outdoor recreation and travel'),
  (5, 1, 'Data Science', 'data-science', 'Data science and machine learning books'),
  (6, 2, 'Photography', 'photography', 'Photography equipment and accessories')
ON DUPLICATE KEY UPDATE
  parent_category_id = VALUES(parent_category_id),
  name = VALUES(name),
  slug = VALUES(slug),
  description = VALUES(description);

-- Sample catalog items
INSERT INTO items
  (item_id, category_id, item_type, title, description, item_url, attributes)
VALUES
  (1, 5, 'book', 'Graph Machine Learning', 'An introduction to learning with graph-structured data.', 'https://example.test/items/1', JSON_OBJECT('format', 'paperback', 'language', 'English')),
  (2, 5, 'book', 'Practical Recommender Systems', 'Methods for building and evaluating recommendation engines.', 'https://example.test/items/2', JSON_OBJECT('format', 'ebook', 'language', 'English')),
  (3, 5, 'course', 'Introduction to Python for Data Analysis', 'A hands-on course covering Python data analysis workflows.', 'https://example.test/items/3', JSON_OBJECT('level', 'beginner', 'duration_hours', 8)),
  (4, 2, 'product', 'Developer Laptop 14', 'A lightweight laptop suitable for programming and study.', 'https://example.test/items/4', JSON_OBJECT('memory_gb', 16, 'screen_inches', 14)),
  (5, 6, 'product', 'Mirrorless Camera X100', 'A compact mirrorless camera for everyday photography.', 'https://example.test/items/5', JSON_OBJECT('sensor', 'APS-C', 'color', 'black')),
  (6, 6, 'product', 'Portrait Lens 50mm', 'A fast prime lens for portraits and low-light photography.', 'https://example.test/items/6', JSON_OBJECT('focal_length_mm', 50, 'mount', 'X')),
  (7, 3, 'product', 'Indoor Herb Garden Kit', 'A starter kit for growing herbs in a sunny kitchen.', 'https://example.test/items/7', JSON_OBJECT('plant_count', 6, 'indoor', TRUE)),
  (8, 4, 'product', 'Trail Daypack 20L', 'A comfortable daypack for short hikes and day trips.', 'https://example.test/items/8', JSON_OBJECT('capacity_liters', 20, 'water_resistant', TRUE)),
  (9, 1, 'book', 'The Art of Clear Thinking', 'A practical guide to reasoning and decision-making.', 'https://example.test/items/9', JSON_OBJECT('format', 'hardcover', 'language', 'English')),
  (10, 2, 'product', 'Wireless Noise-Cancelling Headphones', 'Over-ear headphones for focused work and travel.', 'https://example.test/items/10', JSON_OBJECT('wireless', TRUE, 'noise_cancelling', TRUE))
ON DUPLICATE KEY UPDATE
  category_id = VALUES(category_id),
  item_type = VALUES(item_type),
  title = VALUES(title),
  description = VALUES(description),
  item_url = VALUES(item_url),
  attributes = VALUES(attributes);

-- User-to-category graph edges with normalized preference weights
INSERT INTO user_interests (user_id, category_id, interest_weight) VALUES
  (1, 5, 0.95000), (1, 6, 0.70000), (1, 2, 0.65000),
  (2, 4, 0.90000), (2, 3, 0.55000), (2, 2, 0.60000),
  (3, 1, 0.85000), (3, 5, 0.75000), (3, 3, 0.50000),
  (4, 6, 0.90000), (4, 2, 0.70000), (4, 4, 0.55000),
  (5, 3, 0.90000), (5, 1, 0.65000), (5, 5, 0.60000)
ON DUPLICATE KEY UPDATE
  interest_weight = VALUES(interest_weight);

-- Sample user-to-item interaction edges
INSERT INTO interactions
  (interaction_id, user_id, item_id, interaction_type, strength, occurred_at)
VALUES
  (1, 1, 1, 'view', 1.000, '2026-11-01 09:00:00'),
  (2, 1, 2, 'click', 2.000, '2026-11-01 09:05:00'),
  (3, 1, 4, 'like', 3.000, '2026-11-02 12:10:00'),
  (4, 2, 8, 'view', 1.000, '2026-11-02 08:30:00'),
  (5, 2, 7, 'purchase', 5.000, '2026-11-03 14:15:00'),
  (6, 2, 10, 'click', 2.000, '2026-11-04 18:20:00'),
  (7, 3, 9, 'like', 3.000, '2026-11-05 10:00:00'),
  (8, 3, 3, 'purchase', 5.000, '2026-11-05 10:30:00'),
  (9, 3, 1, 'click', 2.000, '2026-11-06 11:45:00'),
  (10, 4, 5, 'view', 1.000, '2026-11-07 16:00:00'),
  (11, 4, 6, 'purchase', 5.000, '2026-11-08 13:25:00'),
  (12, 4, 10, 'like', 3.000, '2026-11-08 15:10:00'),
  (13, 5, 7, 'click', 2.000, '2026-11-09 07:40:00'),
  (14, 5, 9, 'view', 1.000, '2026-11-09 20:05:00'),
  (15, 5, 2, 'share', 3.000, '2026-11-10 09:15:00')
ON DUPLICATE KEY UPDATE
  user_id = VALUES(user_id),
  item_id = VALUES(item_id),
  interaction_type = VALUES(interaction_type),
  strength = VALUES(strength),
  occurred_at = VALUES(occurred_at);

-- Sample ratings (one current rating per user/item pair)
INSERT INTO ratings (rating_id, user_id, item_id, rating, review_text) VALUES
  (1, 1, 1, 5, 'Clear introduction to graph-based learning.'),
  (2, 1, 2, 4, 'Useful overview with practical examples.'),
  (3, 2, 8, 5, 'A comfortable pack for day hikes.'),
  (4, 2, 7, 4, 'Easy to set up and enjoyable to use.'),
  (5, 3, 9, 5, 'Thoughtful and easy to follow.'),
  (6, 3, 3, 4, 'Good pace for a beginner course.'),
  (7, 4, 5, 5, 'Compact camera with excellent image quality.'),
  (8, 4, 6, 5, 'Sharp lens that works well for portraits.'),
  (9, 5, 7, 5, 'A fun addition to a small kitchen.'),
  (10, 5, 2, 4, 'A helpful resource for recommender systems.')
ON DUPLICATE KEY UPDATE
  rating = VALUES(rating),
  review_text = VALUES(review_text);

-- Sample saved items
INSERT INTO saved_items (user_id, item_id, saved_at) VALUES
  (1, 3, '2026-11-02 12:20:00'),
  (1, 5, '2026-11-03 09:10:00'),
  (2, 8, '2026-11-02 08:35:00'),
  (2, 10, '2026-11-04 18:25:00'),
  (3, 1, '2026-11-06 11:50:00'),
  (3, 9, '2026-11-05 10:05:00'),
  (4, 6, '2026-11-08 13:30:00'),
  (5, 2, '2026-11-10 09:20:00'),
  (5, 7, '2026-11-09 07:45:00')
ON DUPLICATE KEY UPDATE
  saved_at = VALUES(saved_at);

-- Sample recommendation runs; each run has a stable UUID and ranks per user.
INSERT INTO recommendation_history
  (recommendation_id, run_id, user_id, item_id, score, rank_position, algorithm_name, generated_at)
VALUES
  (1, 'a1111111-1111-4111-8111-111111111111', 1, 3, 0.9420000, 1, 'graph_hybrid_v1', '2026-11-11 08:00:00'),
  (2, 'a1111111-1111-4111-8111-111111111111', 1, 6, 0.8710000, 2, 'graph_hybrid_v1', '2026-11-11 08:00:00'),
  (3, 'a1111111-1111-4111-8111-111111111111', 1, 5, 0.8260000, 3, 'graph_hybrid_v1', '2026-11-11 08:00:00'),
  (4, 'b2222222-2222-4222-8222-222222222222', 2, 8, 0.9300000, 1, 'graph_hybrid_v1', '2026-11-11 08:05:00'),
  (5, 'b2222222-2222-4222-8222-222222222222', 2, 7, 0.8840000, 2, 'graph_hybrid_v1', '2026-11-11 08:05:00'),
  (6, 'b2222222-2222-4222-8222-222222222222', 2, 4, 0.7920000, 3, 'graph_hybrid_v1', '2026-11-11 08:05:00'),
  (7, 'c3333333-3333-4333-8333-333333333333', 3, 1, 0.9510000, 1, 'graph_hybrid_v1', '2026-11-11 08:10:00'),
  (8, 'c3333333-3333-4333-8333-333333333333', 3, 2, 0.9020000, 2, 'graph_hybrid_v1', '2026-11-11 08:10:00'),
  (9, 'c3333333-3333-4333-8333-333333333333', 3, 9, 0.8450000, 3, 'graph_hybrid_v1', '2026-11-11 08:10:00'),
  (10, 'd4444444-4444-4444-8444-444444444444', 4, 6, 0.9600000, 1, 'graph_hybrid_v1', '2026-11-11 08:15:00'),
  (11, 'd4444444-4444-4444-8444-444444444444', 4, 5, 0.9170000, 2, 'graph_hybrid_v1', '2026-11-11 08:15:00'),
  (12, 'd4444444-4444-4444-8444-444444444444', 4, 10, 0.8030000, 3, 'graph_hybrid_v1', '2026-11-11 08:15:00'),
  (13, 'e5555555-5555-4555-8555-555555555555', 5, 7, 0.9330000, 1, 'graph_hybrid_v1', '2026-11-11 08:20:00'),
  (14, 'e5555555-5555-4555-8555-555555555555', 5, 3, 0.8790000, 2, 'graph_hybrid_v1', '2026-11-11 08:20:00'),
  (15, 'e5555555-5555-4555-8555-555555555555', 5, 9, 0.8140000, 3, 'graph_hybrid_v1', '2026-11-11 08:20:00')
ON DUPLICATE KEY UPDATE
  run_id = VALUES(run_id),
  user_id = VALUES(user_id),
  item_id = VALUES(item_id),
  score = VALUES(score),
  rank_position = VALUES(rank_position),
  algorithm_name = VALUES(algorithm_name),
  generated_at = VALUES(generated_at);
