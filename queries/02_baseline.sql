-- 02_baseline.sql
-- The reported number, and the thing that made me question it.


-- The sales cycle distribution. This was the trigger.
-- 251 deals close in one to three months, which is normal. 17 close the same
-- day they were created, which is not.
SELECT
  CASE
    WHEN closedate - createdate < INTERVAL '2 days'  THEN '0-1 days'
    WHEN closedate - createdate < INTERVAL '8 days'  THEN '2-7 days'
    WHEN closedate - createdate < INTERVAL '31 days' THEN '8-30 days'
    WHEN closedate - createdate < INTERVAL '91 days' THEN '31-90 days'
    ELSE '90+ days'
  END AS bucket,
  COUNT(*) AS deals
FROM hubspot.deals_raw
WHERE hs_is_closed
GROUP BY 1
ORDER BY MIN(closedate - createdate);


-- The reported win rate. 389 deals, 292 closed, 27.1%.
-- This number is correct. It is also an average over two populations that
-- convert at very different rates.
SELECT
  COUNT(*) AS deals,
  COUNT(*) FILTER (WHERE hs_is_closed) AS closed,
  COUNT(*) FILTER (WHERE hs_is_closed_won) AS won,
  ROUND(100.0 * COUNT(*) FILTER (WHERE hs_is_closed_won)
        / NULLIF(COUNT(*) FILTER (WHERE hs_is_closed), 0), 1) AS win_rate_pct
FROM hubspot.deals_raw;
