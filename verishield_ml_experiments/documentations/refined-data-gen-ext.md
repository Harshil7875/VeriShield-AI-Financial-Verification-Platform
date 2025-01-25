# **Refined Data Generator (Extended)**

## **Overview**

This **robust extended generator** produces **synthetic user, IP, and business data** for fraud detection experimentation. Key improvements include:

1. **Dynamic Fraud Rates** with **scenario jitter** (±5% each run).  
2. **Time-Based Waves** for user signups, creating “bursts” that can boost fraud likelihood.  
3. **IP Nodes** and **user→IP** relationships, enriching the graph with multiple node types.  
4. **2nd-Degree Synergy** in multi-pass labeling (fraud can propagate through user→user and user→IP→user connections).  
5. **Label Flip Noise** (~1% default) to emulate real-world mislabeling.

As before, the script also handles **ring leaders** (user–user edges), **multi-owner** relationships (user–business edges), and multi-pass labeling that refines fraud labels. By default, you’ll generate:

- **Users** (some with suspicious signups, ring leader flags, etc.)  
- **IP Nodes** (shared among users to simulate collision)  
- **Businesses** (with watchlist countries, suspicious names, or legitimate data)

## **Key Highlights**

1. **Six Main Scenarios** (plus added jitter each run):  
   - `low_fraud`, `default`, `high_fraud`, `ultra_low_fraud`, `medium_fraud`, `extreme_fraud`  
   - E.g., `ultra_low_fraud` might yield ~2% base fraud, while `extreme_fraud` can push ~40% user fraud.  
   - Each scenario’s final rates differ slightly due to random scaling, multi-pass synergy, and label flips.

2. **User→IP Relationships**  
   - Introduces an **`ip_nodes.csv`** file with `ip_id`, `ip_addr`.  
   - The new **`user_ip_relationships.csv`** captures collisions (20% by default). This fosters a **heterogeneous** graph for GNN usage.

3. **Time Waves & Fraud Bursts**  
   - Users sign up in **3** random waves, each potentially boosting their base fraud probability (`wave_fraud_boost`).  
   - Also, some accounts sign up in a **“suspicious burst”** window (few seconds), incrementing fraud likelihood.

4. **2nd-Degree Labeling**  
   - After labeling known ring leaders or owners, the script checks co-users on the same IP or multi-owner businesses.  
   - Suspicious ring neighbors or IP-sharing users can further raise or lower a user’s fraud chance.

5. **Noise Injection**  
   - ~1% of user/business labels get flipped after the final labeling pass, adding **realistic** label errors.

## **How It Works**

1. **Generate Unlabeled Entities**  
   - **Users**:  
     - assigned to waves (`day_offset`, `seconds_in_day`, `wave_fraud_boost`),  
     - random segments (`casual`, `money_mule`, etc.),  
     - optional missing fields (2%).  
   - **IPs**: a standalone list of IP addresses (`ip_nodes`).  
   - **Businesses**: some with suspicious names, watchlist countries, or random owners.

2. **Create Relationships**  
   - **User→IP**: each user is linked to an IP node; 20% of users share collisions.  
   - **User–User**: ~0.5% ring leaders, each connecting to ~5–15 random others.  
   - **User–Business**: ~40% of users own 1–10 businesses (multi-owner patterns).

3. **Multi-Pass Labeling**  
   - **Users**: Probability starts from scenario base + wave booster + ring leader.  
   - Adjusted by suspicious features (phone, email domain, watchlist).  
   - Looks at fraudulent businesses owned and co-user adjacency to shift probability up/down.  
   - **Businesses**: Similar approach, factoring suspicious name keywords, watchlist countries, or fraudulent owners.  
   - **Repeat** for `--iterations` passes, refining synergy.  
   - After final pass, randomly flip ~1% labels.

4. **Enrichment**  
   - Adds user columns like `email_domain`, `ip_count`, and `num_fraud_biz_owned`.  
   - Aids advanced ML or GNN feature engineering.

5. **Resulting Files**  
   - **`synthetic_users.csv`**  
   - **`synthetic_businesses.csv`**  
   - **`ip_nodes.csv`** (new)  
   - **`user_ip_relationships.csv`** (new)  
   - **`user_user_relationships.csv`**  
   - **`user_business_relationships.csv`**

## **Command-Line Usage**

**Example** (medium fraud, 2 labeling passes, seed=42, custom IP count):
```bash
cd data_generators
python refined_data_generator_extended.py \
    --scenario medium_fraud \
    --num-users 100000 \
    --num-businesses 10000 \
    --num-ips 5000 \
    --iterations 2 \
    --seed 42 \
    --output-dir ./data
```

| Argument              | Default         | Description                                                                                                                         |
|-----------------------|-----------------|-------------------------------------------------------------------------------------------------------------------------------------|
| `--num-users`         | `100000`        | Number of synthetic user records to generate.                                                                                      |
| `--num-businesses`    | `10000`         | Number of synthetic business records to generate.                                                                                  |
| `--num-ips`           | `5000`          | Number of unique IP nodes to create (for user→IP relationships).                                                                   |
| `--seed`              | `None`          | Random seed for reproducible results. If not provided, each run differs.                                                           |
| `--scenario`          | `"default"`     | Defines base fraud probabilities (jittered ±5%). **Choices**: `default`, `low_fraud`, `high_fraud`, `ultra_low_fraud`, `medium_fraud`, `extreme_fraud`. |
| `--iterations`        | `1`             | Number of labeling passes. More passes => stronger synergy (user↔biz↔ip↔user).                                                    |
| `--output-dir`        | `./data`        | Parent directory for CSV output. Files go into `--output-dir/<scenario>/`.                                                         |

## **Key Outputs**

1. **`synthetic_users.csv`**  
   - **Columns** (sample):  
     - `user_id`, `segment`, `email`, `phone`, `country_code`, `burst_signup`, `wave_fraud_boost`, `is_ring_leader`, `fraud_label`, etc.  
     - Additional: `email_domain`, `ip_count`, `num_fraud_biz_owned`.  
     - **`created_at`**: Timestamp from wave-based logic.

2. **`synthetic_businesses.csv`**  
   - **Columns** (sample):  
     - `business_id`, `business_name`, `registration_country`, `owner_name`, `fraud_label`, etc.

3. **`ip_nodes.csv`** *(New)*  
   - `ip_id`, `ip_addr` for each IP node.

4. **`user_ip_relationships.csv`** *(New)*  
   - `user_id`, `ip_id`. Some collisions if `collision_ratio` is >0.

5. **`user_user_relationships.csv`**  
   - `(from_user_id, to_user_id)` ring-based edges, referencing `is_ring_leader`.

6. **`user_business_relationships.csv`**  
   - `(user_id, business_id)`. 40% of users own 1–10 businesses.

## **Typical Fraud Rates**

- **`ultra_low_fraud`**: ~2% user/business.  
- **`low_fraud`**: ~5–10%.  
- **`default`**: ~15–20%.  
- **`medium_fraud`**: ~20% user / 15% biz.  
- **`high_fraud`**: ~30% user / 25% biz.  
- **`extreme_fraud`**: ~40% user / 35% biz.  
*(Note: Final rates vary per run due to wave boosters, multi-pass synergy, random label flips.)*

## **Best Practices & Tips**

1. **Use a Seed**  
   - For reproducible runs: `--seed <value>`. Otherwise, you’ll get a new IP distribution, wave schedules, ring leaders, etc. each time.

2. **Handling Large Runs**  
   - Generating hundreds of thousands of users + multiple passes can be time-consuming. Consider parallelizing or chunked generation for extremely large data.

3. **Multi-Pass Labeling**  
   - Increasing `--iterations` to 2 or 3 helps “propagate” fraud signals.  
   - With ring leaders, multi-owner businesses, and shared IP collisions, synergy can strongly inflate final fraud probabilities.

4. **IP Node Usage**  
   - The GNN can exploit `user -> ip -> user` links to detect suspicious IP sharing. Check for IP nodes with especially high fraud rates.

5. **Noise Injection**  
   - A small fraction of labels (1% by default) is flipped after the final pass. This trains models to handle real-world label noise and uncertain ground truth.

6. **Customize**  
   - Adjust wave logic, collision ratio, watchers, or synergy constants (`p += 0.03 * neighbor_fraud_count`) to create more advanced or domain-specific patterns.

---

With these **enhanced** relationships and **labeling** strategies, your **GNN** or other ML pipeline can explore **ring-based**, **IP-based**, and **time-based** fraud patterns, making it better prepared for **real-world** KYC/KYB scenarios.