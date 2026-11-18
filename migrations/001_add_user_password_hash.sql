-- Apply once to databases created with the earlier users table.
-- Sample users can sign in with the demo password documented in README.md.
-- Other existing accounts remain unclaimed (NULL password_hash) until an
-- administrator assigns a new password with `python -m backend.set_password`.

USE ai_graph_recommendation;

ALTER TABLE users
  ADD COLUMN password_hash VARCHAR(255) NULL AFTER display_name;

UPDATE users
SET password_hash = CASE email
  WHEN 'maya.chen@example.test' THEN 'scrypt:32768:8:1$LiJyzK4UJL3P5zD1$fd05dbca1ad830fd5e89dbc8c8369e5107b4311bb858e441eae399d2353cf087499202b5a819145d8ed9187f90c020ebcec732817136eec60402afa27c8ca7af'
  WHEN 'noah.patel@example.test' THEN 'scrypt:32768:8:1$c5rjbbjnbF3Mh0Up$108a77ca99bd3119c21468a8538a49a7ca6e482c8a07cfa2636f7046e31d42a85c116c010e235afa0f72d9f932fac3be916a8fc81c2c520ba1eb01f4b485c986'
  WHEN 'sofia.reyes@example.test' THEN 'scrypt:32768:8:1$9skx5IONJ1HMDQIC$9ecfb31098c1b136233a08a3d2d6a31381b3d3d05907092f4203e196234de67e8c56ddd4bfdc5402510257bb643e19ef8ed1d86cb525fe44f81fa4da21d50e95'
  WHEN 'liam.brooks@example.test' THEN 'scrypt:32768:8:1$rq4ka7J9JAwB91Qh$ad476ca65a620b49f27a92ca899517cacd71e54a13900a9d189cc3d066c786ca258f8ba5053af23e40d45132a371974e8c12ce0ec6da7673382a7b9f33af8c4'
  WHEN 'ava.kim@example.test' THEN 'scrypt:32768:8:1$5Uo80cKkmsgCANNh$5e35d8e25b2f99d846d9cfaff93860154a9754394cb026ffaeeb7f5175ccbd3960d85a9ad0b95faddff4ad4fa41bf8c6136e52e35133934ceba040e3af01845c'
  ELSE NULL
END
WHERE password_hash IS NULL;
