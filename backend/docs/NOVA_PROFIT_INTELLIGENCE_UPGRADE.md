# NOVA Profit-Driven Intelligence Upgrade

## 1) Architecture Update

NOVA now operates with a dedicated **profit intelligence layer**:

1. `ProfitIntelligenceEngine`
   - Cost tracking (`experiment_cost_events`)
   - Profit/ROI/CAC computation
   - Time-aware profit windows (`last_24h`, `last_7_days`, growth rate)
   - Cross-experiment comparison and ranking
   - Priority scoring and level assignment
2. `EconomicController` (integration)
   - Enforces ROI-positive scaling rule
   - Uses priority for capital allocation (HIGH/MEDIUM/LOW)
3. `StrategyLearningEngine` (integration)
   - Persists strategy-level economic patterns in `strategy_patterns`
4. `CognitiveLoop` (integration)
   - Broadcasts economic ranking signal for autonomous planning

## 2) New DB Schema

### `economic_experiments` (new columns)
- `cost_total`
- `cost_real_total`
- `cost_simulated_total`
- `cost_per_click`
- `cost_per_lead`
- `revenue_total`
- `profit_total`
- `profit_per_user`
- `cac`
- `growth_rate`
- `priority_score`
- `priority_level`

### New table: `experiment_cost_events`
- `experiment_id`
- `source` (`manual_input`, `simulated_traffic`, future ad providers)
- `cost_amount`
- `is_simulated` (strict separation of real/simulated)
- `metadata_json`

### New table: `strategy_patterns`
- `strategy_type`
- `success_rate`
- `avg_profit`
- `sample_size`
- `last_seen`

## 3) Modules Added

- `backend/intelligence/profit_intelligence_engine.py`

Capabilities:
- `track_cost(...)`
- `update_profit_snapshot(...)`
- `compare_experiments(...)`
- `update_priority(...)`

## 4) Decision Logic Changes

1. **Profit > vanity metrics**: economics snapshot updates each cycle.
2. **No scaling without positive ROI**:
   - A metric decision of `scale` is downgraded to `hold` when ROI <= 0.
3. **Reliability before priority**:
   - Unreliable data forces LOW priority.
4. **Capital allocation policy**:
   - HIGH + positive ROI -> increase capital aggressively.
   - MEDIUM + positive ROI -> modest capital increase.
   - LOW or negative ROI -> reduce capital.
5. **Real vs simulated isolation**:
   - Profit/ROI decisions use real cost baseline.

## 5) Example Flow

1. Experiment receives traffic and conversion events.
2. Costs are recorded through `track_experiment_cost`.
3. Profit snapshot computes:
   - `cost_total`, `cost_per_click`, `cost_per_lead`
   - `revenue_total`, `profit`, `profit_per_user`, `cac`, `roi`
4. Priority is computed from weighted:
   - profit, ROI, growth_rate, reliability
5. Economic controller chooses capital action:
   - HIGH -> allocate more
   - LOW -> reduce/stop scaling
6. Strategy learner records strategy economic pattern in `strategy_patterns`.

## 6) Test Scenarios

1. **Positive economics + reliable sample**
   - Input: reliable traffic, positive profit, ROI > 0
   - Expected: priority HIGH/MEDIUM, scaling allowed
2. **Strong conversion but negative ROI**
   - Input: conversion threshold met, ROI <= 0
   - Expected: decision forced to hold (no scaling)
3. **Unreliable sample**
   - Input: low sample size
   - Expected: gather more data / LOW priority
4. **Simulated-heavy cost stream**
   - Input: simulated costs dominate
   - Expected: real/simulated costs split; decision baseline uses real costs
5. **Portfolio ranking**
   - Input: multiple active experiments
   - Expected: ranked list + best experiment returned
