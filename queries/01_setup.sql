-- 01_setup.sql
-- Schema, type correction, and the reshaped view the analysis runs on.

CREATE SCHEMA IF NOT EXISTS hubspot;

-- Load data/deals_extract.csv into hubspot.deals_raw before running the rest.
-- Supabase infers createdate, closedate and hs_lastmodifieddate as timestamps
-- correctly. The seven stage-entry columns arrive as text, because they
-- contain blanks.

-- An empty string is not NULL. Casting '' to a timestamp fails, so NULLIF
-- has to clear the blanks before the cast sees them.
ALTER TABLE hubspot.deals_raw
  ALTER COLUMN hs_date_entered_appointmentscheduled TYPE timestamptz
    USING NULLIF(hs_date_entered_appointmentscheduled, '')::timestamptz,
  ALTER COLUMN hs_date_entered_qualifiedtobuy TYPE timestamptz
    USING NULLIF(hs_date_entered_qualifiedtobuy, '')::timestamptz,
  ALTER COLUMN hs_date_entered_presentationscheduled TYPE timestamptz
    USING NULLIF(hs_date_entered_presentationscheduled, '')::timestamptz,
  ALTER COLUMN hs_date_entered_decisionmakerboughtin TYPE timestamptz
    USING NULLIF(hs_date_entered_decisionmakerboughtin, '')::timestamptz,
  ALTER COLUMN hs_date_entered_contractsent TYPE timestamptz
    USING NULLIF(hs_date_entered_contractsent, '')::timestamptz,
  ALTER COLUMN hs_date_entered_closedwon TYPE timestamptz
    USING NULLIF(hs_date_entered_closedwon, '')::timestamptz,
  ALTER COLUMN hs_date_entered_closedlost TYPE timestamptz
    USING NULLIF(hs_date_entered_closedlost, '')::timestamptz;


-- HubSpot stores stage history as seven columns, one per stage, each holding
-- a date or nothing. That is readable one deal at a time and wrong for
-- comparing deals, because the stage name lives in the column name instead
-- of in the data.
--
-- This gives one row per stage a deal actually entered. A skipped stage has
-- no row, so "did this deal enter qualification" becomes a lookup instead of
-- a null check spread across a wide table.
--
-- Built as a view so deals_raw stays exactly as it came out of HubSpot.

CREATE OR REPLACE VIEW hubspot.deal_stage_events AS
SELECT deal_id, 'appointmentscheduled' AS stage, 1 AS stage_order,
       hs_date_entered_appointmentscheduled AS entered_at
FROM hubspot.deals_raw WHERE hs_date_entered_appointmentscheduled IS NOT NULL
UNION ALL
SELECT deal_id, 'qualifiedtobuy', 2, hs_date_entered_qualifiedtobuy
FROM hubspot.deals_raw WHERE hs_date_entered_qualifiedtobuy IS NOT NULL
UNION ALL
SELECT deal_id, 'presentationscheduled', 3, hs_date_entered_presentationscheduled
FROM hubspot.deals_raw WHERE hs_date_entered_presentationscheduled IS NOT NULL
UNION ALL
SELECT deal_id, 'decisionmakerboughtin', 4, hs_date_entered_decisionmakerboughtin
FROM hubspot.deals_raw WHERE hs_date_entered_decisionmakerboughtin IS NOT NULL
UNION ALL
SELECT deal_id, 'contractsent', 5, hs_date_entered_contractsent
FROM hubspot.deals_raw WHERE hs_date_entered_contractsent IS NOT NULL
UNION ALL
SELECT deal_id, 'closedwon', 6, hs_date_entered_closedwon
FROM hubspot.deals_raw WHERE hs_date_entered_closedwon IS NOT NULL
UNION ALL
SELECT deal_id, 'closedlost', 6, hs_date_entered_closedlost
FROM hubspot.deals_raw WHERE hs_date_entered_closedlost IS NOT NULL;
