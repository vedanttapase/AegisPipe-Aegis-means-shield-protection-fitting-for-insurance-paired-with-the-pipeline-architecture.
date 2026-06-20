ClaimStream AI
An intelligent, multimodal data pipeline that automates the ingestion, feature extraction, and structured validation of insurance damage claims.

🚀 Core Features
Instead of forcing an LLM to act as an unregulated decision-maker, this project shifts the AI's role to an expert structured data extractor and compliance engine:

The 9-Rule Expert Prompt: Processes text claim narratives and damage images simultaneously, evaluating submissions against nine specific decision rules covering data presence, severity indexing (tiers 1 to 5), and anomaly/fraud indicators.

Cross-Modal Contradiction Detection: Explicitly flags structural mismatches between what the user describes in text and what is visually apparent in the image.

Structured CSV Outputs: Enforces rigid schema formatting to output clean, parseable metadata rows back into a final evaluation CSV file, creating a reliable audit trail.

🔮 Production Roadmap
While this hackathon MVP operates as a standalone Python utility processing static files, it is designed to seamlessly integrate into an enterprise orchestration workflow (such as n8n):

[ Incoming Claim Trigger ] ──► [ n8n Workflow Engine ]
                                        │
                                        ▼
                         [ Multimodal Groq Script Node ]
                                        │ (Extracts Data Payload)
                                        ▼
                         [ Deterministic Switch/Routing ]
                                        │
             ├─► Fraud / Data Mismatch ──► [ Special Audit Queue ]
             ├─► Low Cost & Severity   ──► [ Instant Payout Webhook ]
             └─► Standard Claims       ──► [ Adjuster Review Dashboard ]
By decoupling the AI feature extraction layer from the deterministic business logic layer, the system remains completely flexible with messy user inputs but 100% compliant, transparent, and auditable in its operational decisions.
