---
note_type: Inventory Exception Narrative
author: Materials Planning - Plant P2
date: 2026-08-19
related_part_id: SC-417
related_plant_id: P2
related_alt_plant_id: P5
---

# Inventory Exception - SC-417 Shortage at Plant P2, Possible Transfer from Plant P5

As of the August inventory snapshot, available SC-417 inventory at Plant P2
has fallen below safety stock (available_qty below the 150-unit safety
stock threshold; see inventory_positions.csv for Plant P2, part SC-417,
period 2026-08 and 2026-09). Combined with the delayed PO-9999001 shipment
and the quality hold on batch BATCH-SC-417-20260710-2, Plant P2 does not
have sufficient uncommitted SC-417 supply to cover the September 11 build
of the Harvester X9 1200 Series (production plan PLAN-9999001) at the
originally planned quantity.

Plant P5 (Rhineland Fabrication Center, Germany) is showing a surplus
position for SC-417 in the same period (see inventory_positions.csv, Plant
P5, part SC-417, period 2026-09, stock_status = Surplus). Plant P5 also
builds the Harvester platform, so a cross-plant transfer is mechanically
feasible, though international transfer lead time and any customs/logistics
constraints between Germany and the U.S. have not yet been evaluated by
Logistics.

Recommend Materials Planning open a formal transfer request for review
alongside the SC-418 substitution option (see substitution approval note,
2026-03-18) as parallel mitigation paths for the September 11 build.
