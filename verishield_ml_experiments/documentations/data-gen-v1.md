# **data-gen-v1.py — Synergy-Based Data Generator**

This script **generates** synthetic users, businesses, and IP nodes with **iterative “convergence”** to **~50% fraud** rates **without** brute-force label flipping. It preserves synergy relationships (user→user, user→business, user→IP) and repeats labeling passes until users, businesses, and IPs are all near **50%** fraud within a tolerance (e.g., ±2%). 

## **1. Key Features**

1. **Base Fraud Rates**  
   - Starts with a scenario-based “user_base_fraud” and “biz_base_fraud.” For example:  
     - **`low_fraud`**: ~5% each  
     - **`medium_fraud`**: ~20% user, 15% biz  
     - **`extreme_fraud`**: ~40% user, 35% biz  
   - Adds **IP** base fraud at 0.10 by default.

2. **Multi-Pass Synergy**  
   - Each pass updates user/business/IP labels based on adjacency:  
     - **user↔user** (ring leaders),  
     - **user↔business** (fraud owners → suspicious biz),  
     - **user↔IP** (IP collisions from fraudulent users).  
   - After labeling each pass, it measures the actual fraud ratios for users, businesses, and IPs.  
   - If one node type is above/below ~50%, the script **adjusts** the base fraud rate up/down slightly and re-labels.

3. **Convergence**  
   - Repeats synergy labeling for up to **10** passes (default).  
   - If the script achieves ~50% for all three node types within ±2% tolerance, it stops early.

4. **Final Steps**  
   - Introduces minor **noise** (~1% label flips) to mimic real-world mislabeling.  
   - **Enriches** user features (e.g., email domain, number of fraud businesses owned).  
   - Saves final CSV outputs (`synthetic_users.csv`, `synthetic_businesses.csv`, `ip_nodes.csv`, etc.).

## **2. Usage Example**

Run **`data-gen-v1.py`** from inside `verishield_ml_experiments/data_generators/`:

```bash
python data-gen-v1.py \
    --num-users 10000 \
    --num-businesses 2000 \
    --num-ips 2000 \
    --scenario medium_fraud \
    --seed 42 \
    --output-dir ./data-v1
```

**Arguments**:
- **`--num-users`**: number of user records to generate (default=10,000).  
- **`--num-businesses`**: number of business records (default=2,000).  
- **`--num-ips`**: number of IP nodes (default=2,000).  
- **`--scenario`**: which scenario base rates to start with (`low_fraud`, `medium_fraud`, etc.).  
- **`--seed`**: random seed for reproducibility.  
- **`--output-dir`**: folder where final CSVs are saved (default=./data).

## **3. Output Files**

After labeling completes, you’ll find CSVs in a subfolder like **`<output-dir>/<scenario>/`**:

1. **`synthetic_users.csv`**  
2. **`synthetic_businesses.csv`**  
3. **`ip_nodes.csv`**  
4. **`user_user_relationships.csv`** (ring edges)  
5. **`user_business_relationships.csv`** (ownership edges)  
6. **`user_ip_relationships.csv`** (IP collisions)  

The script prints a **final summary** of user/business/IP fraud ratios (should be ~50%), plus the total edges for each relationship type.

## **4. How It Works**

1. **Generate Unlabeled Entities**  
   - Creates `num_users` user records with random personal info, wave-based “fraud booster,” etc.  
   - Creates `num_businesses` with random names, watchlist countries, etc.  
   - Creates `num_ips` with placeholder IP addresses.

2. **Build Relationships**  
   - Some fraction of users become ring leaders → user→user edges.  
   - 40% of users own 1–10 businesses → user→biz edges.  
   - 20% of users share collisions → user→IP edges.

3. **Synergy Labeling**  
   - Pass 1: label user + business, then IP.  
   - Measure fraud ratios.  
   - If any ratio is above or below 50% ± TOLERANCE, tweak base rates and rerun.  
   - Up to 10 passes or until converged.

4. **Noise & Enrichment**  
   - Randomly flip ~1% of labels for realism.  
   - Add user columns like `num_fraud_biz_owned`, `ip_count`, etc.

## **5. Limitations**

- If synergy is very strong, you might converge ~slightly off** 50%** for a node type (e.g. 48–52%).  
- The script focuses on user-level synergy. For extremely large data, repeated synergy passes can be CPU-intensive.  
- IP features are minimal by default—**only** a label plus an IP address. If you want IP-based columns (geo, suspicious ranges, etc.), extend the script.

## **6. Next Steps**

- **Use** `01-GNN-DataPrep-3.ipynb` (or similar) to convert these CSVs into `.npy` arrays for GNN libraries (PyTorch Geometric).  
- **Train** a multi-edge GNN with user, business, **and** IP classification in one model.  
- **Tune** synergy or threshold logic (like ring fraction, collision ratio, watchlist country weighting) to produce different patterns.

---

**In summary**, `data-gen-v1.py` is a **robust** synergy-driven generator that keeps ring-based, multi-owner, and user–IP collisions while **iteratively** adjusting base fraud rates until all node types **naturally** hover around **50%** fraudulent. This preserves real adjacency patterns rather than forcing label flips, making it well-suited for **multi-task** GNN experiments.