-- IO-863: phase index/order after the taxonomy restructure (migration 0109).
-- The three planning phases (draftInitiation/draftApproval/constructionPlan) were
-- merged into a single `designPlanning` ("Suunnittelu") phase. This is the manual
-- fallback for migration 0109's step 8; the source of truth is
-- phase_taxonomy.TARGET_PHASE_ORDER. Keep both files in sync.

UPDATE infraohjelmointi_api_projectphase AS p
SET index = v.idx,
    "order" = v.idx
FROM (
    VALUES
        ('proposal', 0),
        ('design', 1),
        ('programming', 2),
        ('designPlanning', 3),
        ('constructionWait', 4),
        ('constructionPreparation', 5),
        ('construction', 6),
        ('warrantyPeriod', 7),
        ('completed', 8),
        ('suspended', 9)
) AS v(value, idx)
WHERE p.value = v.value;
