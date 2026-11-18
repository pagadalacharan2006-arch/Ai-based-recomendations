-- Remove the public demo accounts and their dependent data before deployment.
DELETE FROM users
WHERE email IN (
  'maya.chen@example.test',
  'noah.patel@example.test',
  'sofia.reyes@example.test',
  'liam.brooks@example.test',
  'ava.kim@example.test'
);
