# Demand-to-Delivery Diagnostic Agent
AGCO Advanced AI Bootcamp — Capstone 02 · Supply Chain

Ask why a product, plant or part is at risk; get a ranked, evidence-backed diagnosis with
mitigation options. All data is synthetic.

## What it does
Hybrid retrieval over two systems: a **Neo4j** knowledge graph (204,583 nodes,
491,690 relationships) for structured facts, and a **Chroma** vector index
(74 chunks from 59 narrative notes) for rationale and commentary. An
OpenAI agent plans retrieval, calls typed tools, and returns a schema-validated JSON
diagnosis with verified evidence IDs and a governance badge.

## Setup
1. **Neo4j Desktop** — create a local instance, install the **APOC** plugin, start it.
2. **Environment** (never commit these):
   ```
   NEO4J_URI=neo4j://127.0.0.1:7687     # 127.0.0.1, NOT localhost - see Phase 0
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=<your password>
   NEO4J_DATABASE=neo4j
   OPENAI_API_KEY=<your key>            # OPENAI_APIKEY also accepted
   ```
   If `NEO4J_PASSWORD` is unset the notebook prompts via `getpass` and stores nothing.
3. **Dependencies** (Python 3.11–3.14):
   ```
   pip install neo4j openai chromadb rank-bm25 pydantic python-dotenv pandas gradio ipykernel
   ```

## Run
Open `solution.ipynb` and **Run All** (~11 minutes, ~$0.60 of OpenAI usage). Phases:

| Phase | Content | Runtime |
|---|---|---|
| 0 | Environment & connectivity | seconds |
| 1 | Data discovery & ontology | ~30s |
| 2 | Graph ingestion + duplicate-safety proof | ~2.5 min |
| 3 | Chunking, embeddings, Chroma index | ~30s |
| 4 | Agent, tools, guardrails | ~1 min |
| 5 | Evaluation, judge, tuning iteration | ~7 min |
| 6 | Gradio UI, never-do tests, governance | ~1 min |

Phase 6 launches the demo UI and prints its URL. Call `demo.close()` to stop it.

## Results
| Metric | Baseline | Tuned |
|---|---|---|
| Deterministic score | 0.717 | 0.827 |
| Badge accuracy | 0.267 | 0.733 |
| Unverified evidence IDs | 18 | 0 |
| LLM judge mean (1–5) | 4.49 | 4.57 |
| Latency p95 | 32.34s | 51.03s |
| Golden-note recall | 5/7 | 5/7 |

Re-ingestion is idempotent: a second full load changes node and relationship counts by zero.

## Reading the notebook
It is a **working log**. Failed attempts are left in place with their output, marked
❌ Attempt / 🔍 Diagnosis / ✅ Landed, because the decisions only make sense alongside what
they replaced. 15 open issues are registered in `artifacts/`.

## Known limitations
- **ingestion** — Some integer-valued columns are float-formatted in the source CSV (e.g. reserved_qty='346.0', planned_qty='20.0'). _Mitigation: Phase 2 coerces via float() then int() where the value is integral, with the column's target type declared per-field in the load spec._
- **entity resolution** — 14 of 225 flagged duplicate suppliers could not be resolved automatically (9 have no name-block match, 3 are ambiguous ties, 2 score below threshold). _Mitigation: Loaded with needs_steward_review=true and surfaced in the UI rather than guessed. A data steward resolves them out-of-band._
- **entity resolution** — No ground-truth labels exist for the 211 auto-merges - we can show they are self-consistent, not that they are correct. _Mitigation: Phase 5 adds a deterministic benchmark check on a hand-verified sample._
- **evidence completeness** — supplier_capacity.csv ends at 2026-04, but the shortage window is 2026-08/09. _Mitigation: The agent must report this as missing evidence and lower confidence on that specific driver, rather than asserting it as fact._
- **evidence conflict** — PO-9999001 has two Delayed shipment records (SHP-0013901, SHP-0021122) on different lanes for the same 600 units. _Mitigation: Phase 2 keeps both edges; the agent surfaces the conflict in contradictory_or_missing_evidence instead of picking one._
- **deployment** — The graph is hosted on a local Neo4j Desktop instance, not a shared cloud DB. _Mitigation: Phase 2 ingestion is fully reproducible from the CSVs in one pass. Production would use Aura Professional or a managed cluster._
- **graph model** — Alias entities are loaded as :SupplierAlias / :PartAlias stub nodes rather than as extra labels on the canonical node. _Mitigation: Alias stubs carry no business relationships - only ALIAS_OF - so normal traversals never reach them. Documented for query authors._
- **ingestion** — Relationship creation is not transactional across the whole load: apoc.periodic.iterate commits per batch. _Mitigation: The load is idempotent (proved in 2.6), so re-running completes it. Production would need a load-status ledger._
- **retrieval** — Golden-note recall is only 5/7 at top-15. The substitution-approval and logistics-alert notes are missed, and top similarity is ~0.36. _Mitigation: Recorded as the Phase 5 tuning baseline. BM25 fusion, an anchor-driven second retrieval pass, and query decomposition are the candidate fixes._
- **retrieval** — Chunks are prefixed with a front-matter header, so every chunk from one note shares that text. _Mitigation: Phase 5 evaluates diversity and tests a per-note cap in the tuning iteration._
- **retrieval** — The plant_id regex (P followed by 1-2 digits) is loose and would match ordinary prose tokens. _Mitigation: Every candidate is validated against the graph before becoming an anchor; unmatched candidates are reported as rejected, not silently dropped._
- **agent** — Generated-Cypher fallback is implemented and validated but the agent currently only calls templated queries. _Mitigation: validate_cypher() is proven against 6 adversarial cases in 4.2; wiring it as a tool is a Phase 5 tuning candidate once benchmark gaps are known._
- **cost** — Cost figures use hard-coded per-million-token prices, not billed amounts. _Mitigation: Token counts are logged exactly; only the USD conversion is approximate._
- **evaluation** — The judge is the same model family as the agent under test (gpt-4.1 judging gpt-4.1). _Mitigation: Deterministic checks carry equal weight in the analysis and cannot be influenced by the judge. A cross-family judge would be the production fix._
- **evaluation** — Expected answers were written by inspecting the dataset, not by an independent domain expert. _Mitigation: Every expected value is a literal fact from a named CSV row, so the checks are at least objectively verifiable._

## Outputs
- `artifacts/phase1_profile.json`, `phase2_graph.json`, `phase3_vectors.json`, `phase5_evaluation.json`
- `artifacts/benchmark_baseline.csv`, `benchmark_tuned.csv`
- `benchmark_questions.json` — re-runnable benchmark set
- `logs/audit.jsonl` — every query, tool call, evidence ID, judge score
- `chroma_store/` — persisted vector index
