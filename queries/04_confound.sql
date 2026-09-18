-- 04_confound.sql
-- Before concluding anything: is skipping spread evenly, or concentrated?


-- By source. Partner referrals skip far more than anything else.
SELECT
  deal_source,
  COUNT(*) AS deals,
  ROUND(100.0 * COUNT(*) FILTER (WHERE hs_date_entered_qualifiedtobuy IS NULL)
        / COUNT(*), 1) AS skip_rate_pct
FROM hubspot.deals_raw
GROUP BY 1
ORDER BY skip_rate_pct DESC;


-- The same question by rep, to see whether it tracks with the channel
-- or with the person. Two reps skip far more than the rest.
SELECT
  hubspot_owner,
  COUNT(*) AS deals,
  ROUND(100.0 * COUNT(*) FILTER (WHERE hs_date_entered_qualifiedtobuy IS NULL)
        / COUNT(*), 1) AS skip_rate_pct
FROM hubspot.deals_raw
GROUP BY 1
ORDER BY skip_rate_pct DESC;


-- Integrity checks. None of these are visible in native CRM reporting.

-- Stage entries recorded before the deal existed.
SELECT COUNT(*) AS backdated_entries
FROM hubspot.deal_stage_events e
JOIN hubspot.deals_raw d USING (deal_id)
WHERE e.entered_at < d.createdate;

-- Open deals already past their own close date.
SELECT COUNT(*) AS stale_open
FROM hubspot.deals_raw
WHERE NOT hs_is_closed AND closedate < NOW();

-- Closed won with no value attached.
SELECT COUNT(*) AS won_without_amount
FROM hubspot.deals_raw
WHERE hs_is_closed_won AND COALESCE(amount, 0) = 0;

-- Whole pipeline traversed inside a single day.
SELECT COUNT(*) AS same_day_traversal
FROM (
  SELECT deal_id
  FROM hubspot.deal_stage_events
  GROUP BY deal_id
  HAVING COUNT(*) >= 5
     AND MAX(entered_at) - MIN(entered_at) < INTERVAL '1 day'
) t;
