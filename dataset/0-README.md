# AGCO Capstone - Demand-to-Delivery Diagnostic Agent
## Synthetic Dataset Pack (Supply Chain domain)

**Everything in this pack is synthetic.** All company names, supplier names,
plant names, and part numbers are fictional and were generated for this
training exercise only. No real AGCO operational data is included or implied.

Total: **13 CSV files** (269,000+ data rows) + **59 unstructured evidence
notes** (Markdown), sized to match Section 13.1 of the capstone brief.

---

## 1. How to use this pack

1. Load all 13 CSVs into Neo4j using MERGE/upsert Cypher, following the
   node/relationship types in Section 8.3 of the brief.
2. Chunk and embed the files in `unstructured_supply_notes/` into your
   vector index.
3. Use the **golden scenario** below (Part `SC-417` / Plant `P2`) as your
   first end-to-end benchmark question — it is a fully-connected, hand-seeded
   thread running through every file and note, matching the exact example
   in Section 13.2 of the brief ("Why is Part SC-417 projected to create a
   shortage at Plant P2?").
4. Everything *outside* the golden thread is randomized noise — realistic
   in shape and distribution, but not individually curated. Use it to stress-test
   retrieval, entity resolution, and multi-hop traversal at scale.

---

## 2. File-by-file schema

### parts.csv (15,120 rows)
Part master and compatibility metadata.
| Column | Notes |
|---|---|
| part_id | Format `{CategoryCode}-{number}`, e.g. `SC-417`. Categories: EN=Engine, HY=Hydraulic, EL=Electrical, CH=Chassis, TR=Transmission, BR=Brake, SC=Sensor & Control, FT=Fastener, FL=Fluid & Seal, CB=Cab & Interior, EC=Electronic Control Unit, ST=Structural Steel |
| part_name, part_category, unit_of_measure, unit_cost, lead_time_days, safety_stock_qty, is_critical, min_order_qty, part_status, weight_kg, part_notes | |

*Irregularities:* ~5% nulls in `unit_cost`, `lead_time_days`, `weight_kg`, `min_order_qty`. ~0.8% of parts have a duplicate "alias" row (`part_id` suffixed `-ALT`, name upper-cased) for entity-resolution practice.

### products_bom.csv (21,600 rows)
Product → required-part BOM lines. 70 products across 7 platforms (Harvester,
Tractor, Baler, Sprayer, Planter, Combine, Tillage), ~300 BOM lines/product avg.
Columns: `bom_id, product_id, part_id, qty_per_unit, bom_version, effective_date, is_optional`.
*Irregularities:* ~5% null `bom_version`/`effective_date`.

### suppliers.csv (15,225 rows)
Columns: `supplier_id, supplier_name, supplier_country, supplier_region, supplier_tier, risk_rating, onboarding_date, certification_status, payment_terms, active_flag, supplier_notes`.
*Irregularities:* ~5% nulls across `risk_rating/country/certification_status/payment_terms`. ~1.5% of rows are deliberate **alias/duplicate suppliers** (name case-mangled or padded with extra whitespace + " Inc."), flagged via `supplier_notes = "Possible duplicate entity..."` — use these to test alias resolution (FR-2).

### supplier_capacity.csv (28,000 rows)
1,000 sampled supplier-part sourcing relationships × 28 monthly periods (2024-01 → 2026-04).
Columns: `capacity_id, supplier_id, part_id, period, capacity_units, committed_units, utilization_pct, capacity_notes`.

### demand_forecast.csv (21,630 rows)
Product × region × period, with Baseline rows plus probabilistic Uplift/Downside variants.
Columns: `forecast_id, product_id, period, region, forecast_qty, forecast_type, forecast_version, created_date, planner_id`.

### customer_orders.csv (30,260 rows)
Individual order-level demand signals. Columns: `order_id, product_id, dealer_id, order_date, requested_qty, region, customer_segment, order_status`.

### purchase_orders.csv (27,002 rows)
Columns: `po_id, supplier_id, part_id, plant_id, po_date, promised_date, po_qty, unit_price, po_status, po_notes`.
`po_status` ∈ {Closed, Open, Late, Partial, Cancelled}.

### shipments.csv (21,122 rows)
Derived from a sample of non-Open POs. Columns: `shipment_id, po_id, lane_id, carrier, ship_date, eta_date, actual_arrival_date, shipment_qty, shipment_status`.

### inventory_positions.csv (24,005 rows)
4 monthly snapshots (2026-06 → 2026-09) × ~500 parts/plant × 12 plants.
Columns: `inventory_id, part_id, plant_id, period, on_hand_qty, reserved_qty, safety_stock_qty, available_qty, stock_status`.

### quality_events.csv (16,001 rows)
Batch-level inspection/quality records. Columns: `quality_event_id, part_id, supplier_id, batch_id, event_date, event_type, severity, disposition_status, affected_qty`.
`event_type` ∈ {Incoming Inspection Pass (~84%), Hold, Defect, Recall, Deviation Approved}. Passing inspections carry `severity = "Not Applicable"`.

### plants_and_production_plans.csv (18,001 rows)
Build-schedule lines per plant/product. Columns: `plan_id, plant_id, plant_name, plant_country, product_id, scheduled_build_date, planned_qty, plan_status, part_shortage_risk_flag`.

### substitution_rules.csv (16,020 rows)
Approved-substitute mappings. Columns: `substitution_id, original_part_id, substitute_part_id, compatibility_scope, approval_status, approval_date, limited_compatibility_flag, compatibility_notes`.

### logistics_lanes.csv (15,200 rows)
Origin-country → destination-plant lane metadata by mode and month (2025-01 → 2026-10).
Columns: `lane_id, origin_country, destination_plant_id, mode, period, avg_lead_time_days, risk_score, cost_index`.

### unstructured_supply_notes/ (59 Markdown files)
7 note types: Supplier Risk Note, Quality Investigation Note, Planning Meeting
Summary, Substitution Approval Note, Procurement Comment, Inventory Exception
Narrative, Logistics Alert. Each has a YAML front-matter block with
`related_*_id` fields you can use as anchors when validating vector-to-graph
expansion.

---

## 3. Deliberate irregularities (~5%, by design)

Per file, roughly 5% of rows carry random nulls in non-key columns (see
per-file notes above) to simulate real-world missing data. Additional
irregularities baked in on purpose:

- **Duplicate/alias entities**: ~0.8% of parts and ~1.5% of suppliers have a
  messy duplicate record (different ID, mangled name) — tests FR-2 (entity
  resolution) before graph load.
- **Conflicting/ambiguous signals** in the golden scenario (see below):
  a supplier-capacity delay *and* an unrelated quality hold *and* a
  demand-forecast uplift are all true at once for the same part/plant,
  exactly per the brief's scenario anchor ("the immediate signal looks like
  supplier lateness, but the full picture includes...").
- **Negative `available_qty`** is possible at Plant P2 in the golden thread
  (reserved exceeds on-hand) — deliberately left un-clamped so the "shortage"
  signal is unambiguous in the data itself.

---

## 4. The golden scenario (use this to validate your build)

This is the fully-connected reference case matching Section 13.2, Q1 of the
brief almost verbatim. Every ID below is real and cross-references across
every file and note.

| Entity | ID | What it shows |
|---|---|---|
| Critical part | `SC-417` ("Grain Flow Sensor Module - Harvester X9 Platform") | `is_critical=True`, single-sourced |
| Product | `HRV-03` ("Harvester X9 1200 Series") | requires 2× SC-417 per unit (BOM, `is_optional=False`) |
| Plant at risk | `P2` (Prairie Junction Assembly Plant, USA) | scheduled build `PLAN-9999001`, 2026-09-11, `plan_status=At Risk`, `part_shortage_risk_flag=True` |
| Supplier | `SUP-00042` (NorthStar Sensor Systems, Mexico) | sole approved source for SC-417, `risk_rating=Medium-High` |
| Late PO | `PO-9999001` | 600 units, promised 2026-08-20, `po_status=Late` |
| Delayed shipment | `SHP-0021122` | tied to PO-9999001, `shipment_status=Delayed`, `actual_arrival_date` still null |
| Elevated-risk lane | `LANE-000966` | Mexico → P2, Truck, period 2026-08, `risk_score=High` |
| Quality hold (separate cause) | `QE-9999001` | batch `BATCH-SC-417-20260710-2`, 340 units, `event_type=Hold`, `disposition_status=Under Investigation` |
| Forecast uplift | `demand_forecast.csv`, HRV-03 / North America / 2026-09 | Baseline 95 → Uplift 127 (~34% increase) |
| Shortage inventory | `inventory_positions.csv`, SC-417 @ P2, 2026-08/09 | drops "Below Safety Stock", available_qty goes negative by 2026-09 |
| Mitigation: substitute | `substitution_rules.csv`, SC-417 → `SC-418` | `approval_status=Approved with Limited Compatibility` — NOT yet validated for the exact build spec run at P2 |
| Mitigation: transfer | `inventory_positions.csv`, SC-417 @ `P5` (Rhineland Fabrication Center, Germany), 2026-09 | `stock_status=Surplus` |
| Supporting notes | 7 files in `unstructured_supply_notes/` prefixed `supplier_risk_note_northstar`, `quality_investigation_sc417`, `planning_meeting_summary_hrv03`, `substitution_approval_sc417_sc418`, `procurement_comment_po9999001`, `inventory_exception_sc417_transfer`, `logistics_alert_mexico_p2` | narrative evidence for vector retrieval |

**Expected diagnosis shape:** the shortage is *not* a single cause — it's the
combination of (a) a genuine supplier-capacity/logistics delay on the open PO,
(b) an unrelated quality hold on a separate batch, and (c) a forecast uplift
that increased the September requirement right as supply tightened. Two
partial mitigations exist (SC-418 substitute — compatibility not fully
cleared; P5 inventory transfer — logistics/customs not yet evaluated) but
neither is a clean fix, which is exactly the kind of "state assumptions,
don't overclaim confidence" case FR-6 and the guardrail framework (Section
9.4) are meant to surface.

Everything else in the dataset (other parts, suppliers, products, plants,
POs, shipments, etc.) is realistic random noise for your own benchmark
questions and retrieval stress-testing.

---

## 5. Suggested additional benchmark questions

Beyond the brief's five example questions (Section 13.2), the dataset
supports:

- "Which suppliers have a Medium-High or High risk rating in Mexico, and
  what parts do they solely supply?" (tests graph aggregation)
- "Show me every part with a quality hold in the last 90 days that is also
  below safety stock at any plant." (tests multi-hop join across 3 files)
- "Which approved substitutes have limited-compatibility flags, and which
  products do they cover?" (tests substitution_rules ↔ products_bom join)
- Pick any random duplicate-alias supplier/part pair and ask the agent to
  identify it — a good deterministic check for FR-2.
