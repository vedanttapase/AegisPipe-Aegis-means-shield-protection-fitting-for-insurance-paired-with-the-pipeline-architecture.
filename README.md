# ClaimStream AI: Multimodal Evidence Verification Pipeline

An intelligent, multi-object data pipeline designed to automate the ingestion, multi-modal feature extraction, and structured verification of insurance damage claims.

The system simultaneously processes text-based claim transcripts and visual image evidence to evaluate claims across three asset categories: **cars**, **laptops**, and **packages**. It determines whether the evidence supports the claim, contradicts it, or lacks sufficient information, generating a completely structured, auditable data row for every submission.

---

## 🛠️ System Architecture & Engineering

Instead of treating an LLM as an unregulated, black-box decision-maker, this project shifts the AI's role to a **structured data extractor and cross-modal compliance engine**:

* **Dual-Data Ingestion Layer:** Joins live customer claim data (`claims.csv`) with contextual reference data, including `user_history.csv` (historical risk profiles) and `evidence_requirements.csv` (minimum evidence standards per object type).
* **Cross-Modal Contradiction Detection:** The system prompt forces the multimodal vision model (via the Groq API) to simultaneously analyze image files and text descriptions, looking for physical and structural mismatches (e.g., a text claim for a smashed laptop screen paired with an image of a pristine device).
* **Rigid Schema Enforcement:** Bypasses unstructured conversational text blocks by forcing the API to output strict, parseable metadata mapping to the exact data fields required by the system.

---

## 📂 Repository Structure

The project is organized following clean, decoupled software engineering standards:

```text
├── dataset/                         # Source input data files
│   ├── claims.csv                   # Target evaluation dataset
│   ├── user_history.csv             # Historical user claim counts and risk scores
│   └── evidence_requirements.csv    # Minimum image requirements per object category
├── notebooks/
│   └── test.ipynb                   # Exploratory notebook for prompt tuning & Groq API wiring
├── src/                             # Core pipeline logic 
│   ├── main.py                      # Main pipeline execution entry point
│   └── prompt_configs.py            # The 9-rule expert system prompt definition
├── evaluation/                      # Empirical validation tracking
│   ├── sample_evaluation_results.csv
│   └── sample_evaluation_results1.csv
├── output.csv                       # Final generated predictions schema
└── README.md                        # Project documentation

```

---

## 📈 Empirical Evaluation Framework

Rather than tuning the system blindly, prompt and model configurations were iteratively calibrated against a mock validation dataset. Performance was continuously tracked against two primary metrics inside the `evaluation/` folder:

1. **Severity Classification Alignment:** Ensuring visual asset damage consistently maps to standard categorical tiers (`none`, `low`, `medium`, `high`) without generating false positives that overwhelm downstream queues.
2. **Anomaly & Flag Recall:** Maximizing the engine’s ability to flag missing documentation, bad uploads (`valid_image == false`), or active claim contradictions to ensure risk compliance.

---

## 🔮 Enterprise Scaling Roadmap

To move this from a file-based utility to a production-grade microservice, the architecture separates the **AI extraction layer** from the **business automation layer**:

```
[ Incoming Claim Form ] ──► [ Workflow Orchestration (e.g., n8n) ]
                                            │
                                            ▼
                             [ This Multi-Modal Script Node ]
                                            │ (Returns Structured JSON Payload)
                                            ▼
                             [ Deterministic Rule Engine ]
                                            │
              ├─► Risk Flags / Mismatch ────► [ Manual Special Audit Queue ]
              ├─► Low Cost / High Match ────► [ Instant Automated Payout Webhook ]
              └─► Standard Validated Claims ──► [ Adjuster Triage Dashboard ]

```

This decoupling ensures that the system remains robust against highly variable user-submitted text and images, while ensuring the ultimate routing and financial actions remain 100% predictable, safe, and auditable.
