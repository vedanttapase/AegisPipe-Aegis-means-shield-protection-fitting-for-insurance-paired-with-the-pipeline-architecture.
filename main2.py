import json
import os
import io
import pandas as pd
import time
import base64
from PIL import Image
from openai import OpenAI

# 1. Configuration & Setup
BASE_DIR = "../dataset"
OUTPUT_FILE = "../output.csv"

client = OpenAI(
    api_key="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",
    base_url="https://api.groq.com/openai/v1"
)

def encode_image(image_path):
    """Opens, normalizes, resizes, and safely encodes any image."""
    try:
        with Image.open(image_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.thumbnail((1024, 1024)) # Keep payload small to save tokens!
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
    except Exception as e:
        print(f"    ⚠️ Local Image Error processing {image_path}: {e}")
        return None

def run_production_pipeline():
    print("Loading production datasets...")
    claims_df = pd.read_csv(os.path.join(BASE_DIR, "claims.csv"))
    history_df = pd.read_csv(os.path.join(BASE_DIR, "user_history.csv"))
    rules_df = pd.read_csv(os.path.join(BASE_DIR, "evidence_requirements.csv"))
    
    # --- AUTO-RESUME LOGIC ---
    processed_users = set()
    if os.path.exists(OUTPUT_FILE):
        existing_df = pd.read_csv(OUTPUT_FILE)
        if 'user_id' in existing_df.columns:
            processed_users = set(existing_df['user_id'].tolist())
            print(f"Found {len(processed_users)} already processed users in output.csv. Skipping them.")
            
    cols_order = [
        "user_id", "image_paths", "user_claim", "claim_object", 
        "evidence_standard_met", "evidence_standard_met_reason", "risk_flags", 
        "issue_type", "object_part", "claim_status", "claim_status_justification", 
        "supporting_image_ids", "valid_image", "severity"
    ]

    print(f"\nStarting evaluation...\n")
    
    for index, test_row in claims_df.iterrows():
        user_id = test_row['user_id']
        
        # 1. Skip if already processed!
        if user_id in processed_users:
            print(f"[{index+1}/{len(claims_df)}] ⏭️ Skipping {user_id} (Already saved)")
            continue

        claim_object = test_row['claim_object']
        user_claim = test_row['user_claim']
        
        print(f"[{index+1}/{len(claims_df)}] ⚙️ Processing {user_id}...")
        
        # 2. Relational Mapping
        user_hist = history_df[history_df['user_id'] == user_id]
        hist_summary = user_hist['history_summary'].values[0] if not user_hist.empty else "No history available."

        matched_rules = rules_df[(rules_df['claim_object'] == claim_object) | (rules_df['claim_object'] == 'all')]
        rules_text = "\n".join([f"- [{r['requirement_id']}]: {r['minimum_image_evidence']}" for _, r in matched_rules.iterrows()])

        # 3. Master Prompt
        system_prompt = f"""You are a strict, literal visual verification system for damage claims.

### STRICT VOCABULARY
`object_part`:
- Car: front_bumper, rear_bumper, door, hood, windshield, side_mirror, headlight, taillight, fender, quarter_panel, body, unknown
- Laptop: screen, keyboard, trackpad, hinge, lid, corner, port, base, body, unknown
- Package: box, package_corner, package_side, seal, label, contents, item, unknown

`issue_type`: dent, scratch, crack, glass_shatter, broken_part, missing_part, torn_packaging, crushed_packaging, water_damage, stain, none, unknown

### CRITICAL DECISION RULES
1. MULTIPLE IMAGES: If one is blurry but another is clear, SUPPORT the claim using the clear image's ID. Add "blurry_image" to risk flags.
2. FAKE IMAGE: If it's a stock photo/screen picture/text overlay, add "non_original_image" or "text_instruction_present" to risk_flags.
3. WRONG OBJECT/PART: If claim is "hood" but image is "bumper", set claim_status="contradicted", risk_flags="wrong_object", issue_type="unknown", object_part="unknown".
4. CLEAN SURFACE: If image is clear but perfectly fine: claim_status="contradicted", issue_type="none", severity="none", risk_flags="damage_not_visible".
5. EXAGGERATED DAMAGE: If claim="smashed" but image="scratch": claim_status="contradicted", issue_type="scratch", severity="low", risk_flags="claim_mismatch".
6. UNDERSTATED DAMAGE: If claim="dent" but image is completely crushed: SUPPORT the claim. Use the claimed issue_type.
7. MISSING CONTENTS / NOT ENOUGH INFO: 
- Wrong angle: valid_image=true, risk_flags="wrong_angle;damage_not_visible", claim_status="not_enough_information".
- Missing contents: valid_image=false, risk_flags="cropped_or_obstructed;damage_not_visible", claim_status="not_enough_information".
8. VALID IMAGE: True unless missing-contents, stock photo, or extreme blur.
9. HISTORY: Only add "user_history_risk;manual_review_required" if history mentions "rejected claims", "fraud", or "needed evidence review".

### CONTEXT
1. RULES: {rules_text}
2. HISTORY: {hist_summary}
3. CLAIM: "{user_claim}"

### TARGET SCHEMA
Respond ONLY with this JSON format. Boolean values MUST be lowercase true/false.
{{
  "evidence_standard_met": true or false,
  "evidence_standard_met_reason": "Short objective confirmation.",
  "risk_flags": "none, blurry_image, cropped_or_obstructed, wrong_object, wrong_angle, damage_not_visible, claim_mismatch, non_original_image, text_instruction_present, user_history_risk, manual_review_required (separate with ;)",
  "issue_type": "Select ONE",
  "object_part": "Select ONE",
  "claim_status": "supported, contradicted, or not_enough_information",
  "claim_status_justification": "Short reasoning.",
  "supporting_image_ids": "Image ID or 'none'",
  "valid_image": true or false,
  "severity": "none, low, medium, high, or unknown"
}}
"""

        # 4. Parse & Encode Images
        raw_image_paths = test_row['image_paths']
        image_paths = raw_image_paths.split(';')
        image_ids = [os.path.splitext(os.path.basename(p))[0] for p in image_paths]
        full_image_paths = [os.path.join(BASE_DIR, p) if not p.startswith(BASE_DIR) else p for p in image_paths]
        
        messages = [{"role": "system", "content": system_prompt}]
        user_content = [{"type": "text", "text": "Evaluate the following images against the claim and requirements:"}]

        for img_path, img_id in zip(full_image_paths, image_ids):
            if os.path.exists(img_path):
                base64_img = encode_image(img_path) 
                if base64_img:
                    user_content.append({"type": "text", "text": f"Image ID: {img_id}"})
                    user_content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}
                    })
                
        messages.append({"role": "user", "content": user_content})
        
        # 5. API Call & Real-Time Save
        try:
            response = client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=messages,
                response_format={"type": "json_object"},
                max_tokens=800,
                temperature=0.1
            )
            ai_result = json.loads(response.choices[0].message.content)
            
            combined_result = {
                "user_id": user_id, "image_paths": raw_image_paths, 
                "user_claim": user_claim, "claim_object": claim_object, **ai_result
            }
            
            # --- REAL TIME APPENDING ---
            row_df = pd.DataFrame([combined_result])
            row_df = row_df.reindex(columns=cols_order, fill_value="unknown")
            row_df['evidence_standard_met'] = row_df['evidence_standard_met'].astype(str).str.lower()
            row_df['valid_image'] = row_df['valid_image'].astype(str).str.lower()
            
            # Write header ONLY if the file doesn't exist yet
            write_header = not os.path.exists(OUTPUT_FILE)
            row_df.to_csv(OUTPUT_FILE, mode='a', header=write_header, index=False)
            
            print(f"  ✅ Saved!")
            
        except Exception as e:
            print(f"  ❌ API Error: {e}")
            
        time.sleep(2.5) # Protect your new rate limits!

    print("\n✅ Pipeline Finished! Check output.csv.")

if __name__ == "__main__":
    run_production_pipeline()