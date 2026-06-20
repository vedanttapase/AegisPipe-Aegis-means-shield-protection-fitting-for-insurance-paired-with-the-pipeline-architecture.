[evaluation_report.md](https://github.com/user-attachments/files/29157988/evaluation_report.md)
# Operational Analysis & Evaluation Report

## Evaluation Strategy
To develop this pipeline, we built an iterative Jupyter Notebook loop against `dataset/sample_claims.csv`. 
We compared three model configurations:
1. **Zero-Shot Base:** Tended to hallucinate out-of-bounds vocabulary (e.g., inventing `trackpad_area` instead of `trackpad`).
2. **Few-Shot Prompting:** Handled vocabulary better but struggled with Edge Cases (rejecting claims if the damage was "too severe" compared to a claimed "dent").
3. **Decision-Tree Prompting (Final):** We mapped 9 explicit logical rules (e.g., handling missing contents vs. obscured angles) and provided strict JSON schema enforcement. This yielded the highest accuracy against the ground-truth sample labels.

## Operational Metrics

* **Approximate Model Calls:** * Sample Processing: ~20 calls
  * Test Processing: ~56 calls 
  * Total Calls: ~76 requests.
* **Token Usage (Approximate):**
  * Input Tokens: ~800 tokens per call (System Prompt + Transcript + Base64 Image Compression).
  * Output Tokens: ~150 tokens per call (Strict JSON format).
* **Images Processed:** ~90 total images (accounting for multi-image claims).
* **Latency & Runtime:** * API latency averaged ~2-3 seconds per request using Groq's fast Llama 3 models.
  * Total pipeline runtime for the final test set is approximately ~4 minutes.
* **TPM/RPM & Rate Limits:** * To respect the 30 RPM limit on free-tier APIs, the orchestration script utilizes a `time.sleep(2)` throttle between iterations. 
  * **Batching/Caching:** Because every claim requires a unique contextual evaluation combining user history, specific rules, and new images, we processed sequentially (batch size = 1) to ensure zero context-bleed. 

## Cost Analysis
* **Strategy:** Optimized for $0.00 cost by utilizing Groq's high-speed free tier and `meta-llama/llama-4-scout-17b-16e-instruct`.
* If deployed to a paid GPT-4o or Claude 3.5 Sonnet tier, estimating ~$0.005 per multimodal call, processing a dataset of this size would cost roughly **$0.38**.
