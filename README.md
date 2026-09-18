# 53% of closed-won deals never entered qualification

A CRM pipeline reporting a 27% win rate. The number is correct. It's also an average over two groups that convert at completely different rates, and the CRM can't show you the split.

---

## What started it

VP of Sales asked what the average sales cycle was. The distribution answered a different question:

| Time to close | Deals |
|---|---|
| 0-1 days | 17 |
| 2-7 days | 3 |
| 8-30 days | 17 |
| 31-90 days | 251 |
| 90+ days | 4 |

251 deals close in one to three months, which is what you'd expect. 17 closed the same day they were created. Deals don't close in a day, so something was wrong with how they were moving through the pipeline.

## The finding

| | Closed | Won | Win rate |
|---|---|---|---|
| Entered qualification | 192 | 37 | 19.3% |
| Skipped qualification | 100 | 42 | 42.0% |
| **Reported** | **292** | **79** | **27.1%** |

53% of all won deals never entered the qualification stage at all.

The 27% is real arithmetic. It just describes neither group.

## Why the CRM can't show this

HubSpot reports on a deal's current stage. It doesn't store the path a deal took in any form you can group a report by, so there's no "went through qualification" field to break the number down with.

The path history does exist, as per-stage entry timestamps on each deal record. It just isn't queryable inside the CRM. Pulling those into SQL is the whole project.

## Why it matters

Partner referral deals close at 42%. Everything else closes at 19%. The company has been using 27% for both.

That causes three problems:

**Forecasting.** Applying 27% to open pipeline will be wrong in whichever direction the mix moves.

**Rep performance.** Reps working standard deals are held to a number they can't reach. Reps working partner deals look better than they are.

**Channel investment.** Partner referrals convert at more than twice the rate of anything else, and nobody has made the case for putting more into them because nobody had the split.

One thing this doesn't answer: whether it's the channel or the reps. Partner deals skip qualification far more than anything else, but so do two specific reps, and this data can't separate the two.

## What I'd ask first

Does Qualified To Buy have written exit criteria? If it doesn't, nobody's cutting corners. The stage just isn't real, and that's a different problem.

Then: is fast-tracking partner referrals sanctioned, and do those two reps own the partner channel?

## What I'd instrument

- A **deal entry path** property set at creation, so the two populations are reportable instead of invisible. This is the highest-value change and the cheapest.
- **Required properties at stage gates.** Worth doing, with a caveat: gates only fire when a human moves a deal in the UI. API, workflow and import moves bypass them, so a gate is a nudge, not a control.
- **Detection for what a gate can't catch:** deals reaching late stages with no qualification timestamp, stage entries predating the deal's creation, whole-pipeline traversals inside one day.
- **Report win rate by entry path**, with both denominators shown.

What I wouldn't do is retroactively fix the historical deals. That means inventing stage transitions that never happened, and it destroys the only evidence the finding was ever true.

---

## Running it

1. Create a Supabase (or any Postgres) project.
2. Load `data/deals_extract.csv` into a table called `hubspot.deals_raw`.
3. Run `queries/01_setup.sql` through `04_confound.sql` in order.

`01_setup.sql` handles a wrinkle worth knowing about: the stage-entry columns import as text because they contain blanks, and an empty string is not NULL. Casting `''` to a timestamp fails, so `NULLIF` has to clear the blanks before the cast sees them.

## A note on the data

Synthetic. 389 deals generated with a planted pathology, using `data/generate_deals.py`. No client data is involved.

The method is real; the numbers are manufactured. I built the dataset so the analysis would have something to find, and the generator is included so anyone can verify what was planted and reproduce the result.

## One HubSpot constraint worth recording

Create Date on deals is system-set and read-only, and the stage-entry timestamps are written by HubSpot when a deal actually moves. Neither can be imported. So migrated records carry the import date as their creation date, and any HubSpot calculation built on it (Days to Close, for one) will be wrong for them.

Any migration carrying historical dates needs a custom date property, and any cycle-time reporting on migrated records has to be built on that property rather than the system field.
