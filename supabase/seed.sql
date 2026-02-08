-- Seed data for FightMatch MVP
-- Run this after migrations

-- Weight Classes
INSERT INTO weight_classes (slug, name, weight_limit_lbs) VALUES
  ('lightweight', 'Lightweight', 155),
  ('welterweight', 'Welterweight', 170),
  ('middleweight', 'Middleweight', 185)
ON CONFLICT (slug) DO NOTHING;

-- Fighters (sample data)
INSERT INTO fighters (slug, name, ufcstats_id, date_of_birth, height_inches, reach_inches, stance) VALUES
  ('islam-makhachev', 'Islam Makhachev', 'ufc_001', '1991-10-27', 70, 70, 'Orthodox'),
  ('charles-oliveira', 'Charles Oliveira', 'ufc_002', '1989-10-17', 70, 74, 'Orthodox'),
  ('justin-gaethje', 'Justin Gaethje', 'ufc_003', '1988-11-14', 70, 70, 'Orthodox'),
  ('dustin-poirier', 'Dustin Poirier', 'ufc_004', '1989-01-19', 69, 72, 'Orthodox'),
  ('beneil-dariush', 'Beneil Dariush', 'ufc_005', '1989-05-06', 70, 72, 'Orthodox'),
  ('leon-edwards', 'Leon Edwards', 'ufc_006', '1991-08-25', 74, 74, 'Orthodox'),
  ('colby-covington', 'Colby Covington', 'ufc_007', '1988-02-22', 71, 72, 'Orthodox'),
  ('kamaru-usman', 'Kamaru Usman', 'ufc_008', '1987-05-11', 72, 76, 'Orthodox'),
  ('khamzat-chimaev', 'Khamzat Chimaev', 'ufc_009', '1994-05-01', 75, 75, 'Orthodox'),
  ('shavkat-rakhmonov', 'Shavkat Rakhmonov', 'ufc_010', '1994-10-23', 73, 77, 'Orthodox')
ON CONFLICT (slug) DO NOTHING;

-- Fighter-Weight Class Associations
INSERT INTO fighter_weight_class (fighter_id, weight_class_id, is_primary)
SELECT f.id, wc.id, TRUE
FROM fighters f
CROSS JOIN weight_classes wc
WHERE (f.slug LIKE '%makhachev%' OR f.slug LIKE '%oliveira%' OR f.slug LIKE '%gaethje%' OR f.slug LIKE '%poirier%' OR f.slug LIKE '%dariush%')
  AND wc.slug = 'lightweight'
ON CONFLICT DO NOTHING;

INSERT INTO fighter_weight_class (fighter_id, weight_class_id, is_primary)
SELECT f.id, wc.id, TRUE
FROM fighters f
CROSS JOIN weight_classes wc
WHERE (f.slug LIKE '%edwards%' OR f.slug LIKE '%covington%' OR f.slug LIKE '%usman%' OR f.slug LIKE '%chimaev%' OR f.slug LIKE '%rakhmonov%')
  AND wc.slug = 'welterweight'
ON CONFLICT DO NOTHING;

-- Events
INSERT INTO events (name, date, location, ufcstats_id) VALUES
  ('UFC 294', '2023-10-21', 'Abu Dhabi, UAE', 'evt_001'),
  ('UFC 280', '2022-10-22', 'Abu Dhabi, UAE', 'evt_002'),
  ('UFC 286', '2023-03-18', 'London, England', 'evt_003'),
  ('UFC 296', '2023-12-16', 'Las Vegas, NV', 'evt_004')
ON CONFLICT (ufcstats_id) DO NOTHING;

-- Fights
INSERT INTO fights (event_id, date, weight_class_id, result_type, result_method, result_round, result_time, ufcstats_id)
SELECT 
  e.id,
  e.date,
  wc.id,
  CASE 
    WHEN e.name = 'UFC 294' THEN 'KO/TKO'
    WHEN e.name = 'UFC 280' THEN 'Submission'
    WHEN e.name = 'UFC 286' THEN 'Decision'
    WHEN e.name = 'UFC 296' THEN 'Decision'
    ELSE 'Decision'
  END,
  CASE 
    WHEN e.name = 'UFC 294' THEN 'Head Kick'
    WHEN e.name = 'UFC 280' THEN 'Arm Triangle'
    ELSE 'Unanimous'
  END,
  CASE 
    WHEN e.name = 'UFC 294' THEN 1
    WHEN e.name = 'UFC 280' THEN 2
    ELSE 5
  END,
  CASE 
    WHEN e.name = 'UFC 294' THEN '3:06'
    WHEN e.name = 'UFC 280' THEN '3:16'
    ELSE '5:00'
  END,
  'fight_' || e.ufcstats_id
FROM events e
CROSS JOIN weight_classes wc
WHERE wc.slug IN ('lightweight', 'welterweight')
ON CONFLICT (ufcstats_id) DO NOTHING;

-- Fight Participants
INSERT INTO fight_participants (fight_id, fighter_id, is_winner, is_champion, weight_lbs)
SELECT 
  f.id,
  fighter.id,
  CASE 
    WHEN fighter.slug = 'islam-makhachev' AND f.date = '2023-10-21' THEN TRUE
    WHEN fighter.slug = 'charles-oliveira' AND f.date = '2022-10-22' THEN FALSE
    WHEN fighter.slug = 'islam-makhachev' AND f.date = '2022-10-22' THEN TRUE
    WHEN fighter.slug = 'leon-edwards' AND f.date = '2023-03-18' THEN TRUE
    WHEN fighter.slug = 'colby-covington' AND f.date = '2023-12-16' THEN FALSE
    WHEN fighter.slug = 'leon-edwards' AND f.date = '2023-12-16' THEN TRUE
    ELSE FALSE
  END,
  CASE 
    WHEN fighter.slug = 'islam-makhachev' AND f.date >= '2022-10-22' THEN TRUE
    WHEN fighter.slug = 'leon-edwards' AND f.date >= '2023-03-18' THEN TRUE
    ELSE FALSE
  END,
  wc.weight_limit_lbs
FROM fights f
CROSS JOIN fighters fighter
CROSS JOIN weight_classes wc
WHERE (
  (fighter.slug IN ('islam-makhachev', 'charles-oliveira', 'justin-gaethje') AND f.date IN ('2022-10-22', '2023-10-21'))
  OR (fighter.slug IN ('leon-edwards', 'colby-covington', 'kamaru-usman') AND f.date IN ('2023-03-18', '2023-12-16'))
)
AND wc.slug IN ('lightweight', 'welterweight')
ON CONFLICT DO NOTHING;

-- Rankings (latest snapshot for each weight class)
INSERT INTO rankings (weight_class_id, snapshot_date)
SELECT id, CURRENT_DATE
FROM weight_classes
WHERE slug IN ('lightweight', 'welterweight')
ON CONFLICT (weight_class_id, snapshot_date) DO NOTHING;

-- Ranking Entries (Lightweight)
INSERT INTO ranking_entries (ranking_id, fighter_id, rank, tier)
SELECT 
  r.id,
  f.id,
  CASE f.slug
    WHEN 'islam-makhachev' THEN 1
    WHEN 'charles-oliveira' THEN 2
    WHEN 'justin-gaethje' THEN 3
    WHEN 'dustin-poirier' THEN 4
    WHEN 'beneil-dariush' THEN 5
    ELSE 6
  END,
  CASE f.slug
    WHEN 'islam-makhachev' THEN 'Champion'
    WHEN 'charles-oliveira' THEN 'Contender'
    WHEN 'justin-gaethje' THEN 'Contender'
    WHEN 'dustin-poirier' THEN 'Contender'
    ELSE 'Prospect'
  END
FROM rankings r
CROSS JOIN fighters f
CROSS JOIN weight_classes wc
WHERE wc.slug = 'lightweight'
  AND r.weight_class_id = wc.id
  AND f.slug IN ('islam-makhachev', 'charles-oliveira', 'justin-gaethje', 'dustin-poirier', 'beneil-dariush')
ON CONFLICT (ranking_id, fighter_id) DO NOTHING;

-- Ranking Entries (Welterweight)
INSERT INTO ranking_entries (ranking_id, fighter_id, rank, tier)
SELECT 
  r.id,
  f.id,
  CASE f.slug
    WHEN 'leon-edwards' THEN 1
    WHEN 'colby-covington' THEN 2
    WHEN 'kamaru-usman' THEN 3
    WHEN 'khamzat-chimaev' THEN 4
    WHEN 'shavkat-rakhmonov' THEN 5
    ELSE 6
  END,
  CASE f.slug
    WHEN 'leon-edwards' THEN 'Champion'
    WHEN 'colby-covington' THEN 'Contender'
    WHEN 'kamaru-usman' THEN 'Contender'
    WHEN 'khamzat-chimaev' THEN 'Contender'
    ELSE 'Prospect'
  END
FROM rankings r
CROSS JOIN fighters f
CROSS JOIN weight_classes wc
WHERE wc.slug = 'welterweight'
  AND r.weight_class_id = wc.id
  AND f.slug IN ('leon-edwards', 'colby-covington', 'kamaru-usman', 'khamzat-chimaev', 'shavkat-rakhmonov')
ON CONFLICT (ranking_id, fighter_id) DO NOTHING;

-- Fighter Metrics
INSERT INTO fighter_metrics (fighter_id, weight_class_id, last_fight_date, days_since_fight, win_streak, loss_streak, finish_rate, total_fights, wins, losses)
SELECT 
  f.id,
  wc.id,
  CASE f.slug
    WHEN 'islam-makhachev' THEN '2023-10-21'
    WHEN 'charles-oliveira' THEN '2022-10-22'
    WHEN 'justin-gaethje' THEN '2023-07-29'
    WHEN 'dustin-poirier' THEN '2023-07-29'
    WHEN 'beneil-dariush' THEN '2023-05-06'
    WHEN 'leon-edwards' THEN '2023-12-16'
    WHEN 'colby-covington' THEN '2023-12-16'
    WHEN 'kamaru-usman' THEN '2023-03-18'
    WHEN 'khamzat-chimaev' THEN '2023-10-21'
    WHEN 'shavkat-rakhmonov' THEN '2023-09-16'
    ELSE CURRENT_DATE - INTERVAL '90 days'
  END,
  CASE f.slug
    WHEN 'islam-makhachev' THEN 120
    WHEN 'charles-oliveira' THEN 450
    WHEN 'justin-gaethje' THEN 180
    WHEN 'dustin-poirier' THEN 180
    WHEN 'beneil-dariush' THEN 270
    WHEN 'leon-edwards' THEN 30
    WHEN 'colby-covington' THEN 30
    WHEN 'kamaru-usman' THEN 300
    WHEN 'khamzat-chimaev' THEN 120
    WHEN 'shavkat-rakhmonov' THEN 150
    ELSE 90
  END,
  CASE f.slug
    WHEN 'islam-makhachev' THEN 3
    WHEN 'charles-oliveira' THEN 0
    WHEN 'justin-gaethje' THEN 1
    WHEN 'dustin-poirier' THEN 1
    WHEN 'beneil-dariush' THEN 0
    WHEN 'leon-edwards' THEN 2
    WHEN 'colby-covington' THEN 0
    WHEN 'kamaru-usman' THEN 0
    WHEN 'khamzat-chimaev' THEN 6
    WHEN 'shavkat-rakhmonov' THEN 6
    ELSE 0
  END,
  0,
  CASE f.slug
    WHEN 'islam-makhachev' THEN 0.75
    WHEN 'charles-oliveira' THEN 0.60
    WHEN 'justin-gaethje' THEN 0.85
    WHEN 'dustin-poirier' THEN 0.70
    WHEN 'beneil-dariush' THEN 0.50
    WHEN 'leon-edwards' THEN 0.55
    WHEN 'colby-covington' THEN 0.40
    WHEN 'kamaru-usman' THEN 0.50
    WHEN 'khamzat-chimaev' THEN 1.0
    WHEN 'shavkat-rakhmonov' THEN 1.0
    ELSE 0.50
  END,
  25,
  CASE f.slug
    WHEN 'islam-makhachev' THEN 25
    WHEN 'charles-oliveira' THEN 21
    WHEN 'justin-gaethje' THEN 27
    WHEN 'dustin-poirier' THEN 29
    WHEN 'beneil-dariush' THEN 22
    WHEN 'leon-edwards' THEN 23
    WHEN 'colby-covington' THEN 17
    WHEN 'kamaru-usman' THEN 20
    WHEN 'khamzat-chimaev' THEN 13
    WHEN 'shavkat-rakhmonov' THEN 18
    ELSE 10
  END,
  CASE f.slug
    WHEN 'islam-makhachev' THEN 1
    WHEN 'charles-oliveira' THEN 9
    WHEN 'justin-gaethje' THEN 4
    WHEN 'dustin-poirier' THEN 7
    WHEN 'beneil-dariush' THEN 5
    WHEN 'leon-edwards' THEN 3
    WHEN 'colby-covington' THEN 4
    WHEN 'kamaru-usman' THEN 3
    WHEN 'khamzat-chimaev' THEN 0
    WHEN 'shavkat-rakhmonov' THEN 0
    ELSE 5
  END
FROM fighters f
CROSS JOIN weight_classes wc
WHERE (
  (f.slug IN ('islam-makhachev', 'charles-oliveira', 'justin-gaethje', 'dustin-poirier', 'beneil-dariush') AND wc.slug = 'lightweight')
  OR (f.slug IN ('leon-edwards', 'colby-covington', 'kamaru-usman', 'khamzat-chimaev', 'shavkat-rakhmonov') AND wc.slug = 'welterweight')
)
ON CONFLICT (fighter_id, weight_class_id) DO NOTHING;

