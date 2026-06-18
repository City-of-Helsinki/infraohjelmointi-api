-- IO-863: phase index/order after the taxonomy restructure (migration 0109).
-- The three planning phases (draftInitiation/draftApproval/constructionPlan) were
-- merged into a single `designPlanning` ("Suunnittelu") phase. This is the manual
-- fallback for migration 0109's step 8; the source of truth is
-- phase_taxonomy.TARGET_PHASE_ORDER. Keep both files in sync.

UPDATE infraohjelmointi_api_projectphase
SET index = 0, "order" = 0
WHERE value = 'proposal';

UPDATE infraohjelmointi_api_projectphase
SET index = 1, "order" = 1
WHERE value = 'design';

UPDATE infraohjelmointi_api_projectphase
SET index = 2, "order" = 2
WHERE value = 'programming';

UPDATE infraohjelmointi_api_projectphase
SET index = 3, "order" = 3
WHERE value = 'designPlanning';

UPDATE infraohjelmointi_api_projectphase
SET index = 4, "order" = 4
WHERE value = 'constructionWait';

UPDATE infraohjelmointi_api_projectphase
SET index = 5, "order" = 5
WHERE value = 'constructionPreparation';

UPDATE infraohjelmointi_api_projectphase
SET index = 6, "order" = 6
WHERE value = 'construction';

UPDATE infraohjelmointi_api_projectphase
SET index = 7, "order" = 7
WHERE value = 'warrantyPeriod';

UPDATE infraohjelmointi_api_projectphase
SET index = 8, "order" = 8
WHERE value = 'completed';

UPDATE infraohjelmointi_api_projectphase
SET index = 9, "order" = 9
WHERE value = 'suspended';
