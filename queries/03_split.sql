-- 03_split.sql
-- Split the closed deals by whether they ever entered qualification.
-- A deal that entered the stage has a timestamp. A deal that never entered
-- it has nothing, so NULL is the test.


-- 19.3% for deals that followed the process (n=192).
-- 42.0% for deals that skipped qualification (n=100).
SELECT
  CASE WHEN hs_date_entered_qualifiedtobuy IS NULL
       THEN 'skipped qualification'
       ELSE 'entered qualification' END AS path,
  COUNT(*) FILTER (WHERE hs_is_closed) AS closed,
  COUNT(*) FILTER (WHERE hs_is_closed_won) AS won,
  ROUND(100.0 * COUNT(*) FILTER (WHERE hs_is_closed_won)
        / NULLIF(COUNT(*) FILTER (WHERE hs_is_closed), 0), 1) AS win_rate_pct
FROM hubspot.deals_raw
GROUP BY 1;


-- 53.2%. Same 42 deals as above, different denominator.
-- The query above asks: of deals that skipped, how many won?
-- This one asks: of deals that won, how many had skipped?
SELECT
  COUNT(*) AS wins,
  COUNT(*) FILTER (WHERE hs_date_entered_qualifiedtobuy IS NULL) AS wins_that_skipped,
  ROUND(100.0 * COUNT(*) FILTER (WHERE hs_date_entered_qualifiedtobuy IS NULL)
        / COUNT(*), 1) AS pct
FROM hubspot.deals_raw
WHERE hs_is_closed_won;
