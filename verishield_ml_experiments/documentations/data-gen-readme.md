# Refined Data Generator (`refined_data_generator.py`)

## Overview

This script produces **synthetic user and business data** suitable for fraud detection experimentation. Unlike simpler generators, it applies a **multi-pass labeling** process—allowing users’ fraud labels to influence business labels, and vice versa. The result is a more **realistic** dataset with interlinked fraudulent behavior, including **ring leaders**, **multi-owner businesses**, and a **configurable base fraud rate**.

Key highlights:

- **Multiple Scenarios**: `default`, `low_fraud`, `high_fraud` (or custom) to vary fraud prevalence.  
- **Ring Leader Edges**: A fraction of users become ring leaders, creating `user_user` relationships for **collusion** or ring-based fraud.  
- **Ownership Edges**: Users can own multiple businesses, introducing more complex multi-owner structures.  
- **Multi-Pass Fraud Labels**: Iterates through labeling steps so that fraudulent users can make their businesses suspicious—and vice versa.

## How It Works

1. **Generate Unlabeled Entities**  
   - Creates a list of **users** (with segments, IP collisions, suspicious signups, etc.).  
   - Creates a list of **businesses** (with potentially suspicious names or registration countries).  

2. **Create Relationships**  
   - **User–User**: A small fraction of users become ring leaders, linking to ~5–15 random other users.  
   - **User–Business**: About 40% of users own 1–10 businesses, establishing ownership edges.

3. **Assign Fraud Labels** (Multi-Pass)  
   - Users get a probability of being fraudulent based on **segment**, suspicious signals, ring-leader status, and the fraud status of any businesses they own.  
   - Businesses get a probability of being fraudulent based on **suspicious name** keywords, watchlist countries, and the fraud status of owners.  
   - Runs multiple iterations (`--iterations`) to let user labels and business labels influence each other across passes.

4. **Enrich User Features**  
   - Adds extra columns like `email_domain`, `ip_count`, `num_fraud_biz_owned`, etc., to help with feature engineering for ML or GNN usage.

5. **Output Files**  
   - **`synthetic_users.csv`**  
   - **`synthetic_businesses.csv`**  
   - **`user_business_relationships.csv`**  
   - **`user_user_relationships.csv`**  

Each file resides under `data/<scenario>` (default `./data/<scenario>`), reflecting the selected scenario.

## Command-Line Usage

Example:
```bash
cd data_generators
python refined_data_generator.py \
    --scenario high_fraud \
    --num-users 100000 \
    --num-businesses 10000 \
    --iterations 2 \
    --seed 42 \
    --output-dir ./my_synthetic_data
```

### Arguments

| Argument              | Default      | Description                                                                                                                     |
|-----------------------|-------------|---------------------------------------------------------------------------------------------------------------------------------|
| `--num-users`         | `100000`    | Number of synthetic user records to generate.                                                                                  |
| `--num-businesses`    | `10000`     | Number of synthetic business records to generate.                                                                              |
| `--seed`              | `None`      | Random seed for reproducible results. If not provided, results vary each run.                                                   |
| `--scenario`          | `"default"` | Defines base fraud probabilities. Options: `default`, `low_fraud`, `high_fraud` (can be extended).                              |
| `--iterations`        | `1`         | Number of labeling passes. More passes = stronger user↔business fraud influence.                                               |
| `--output-dir`        | `./data`    | Parent directory for the output CSV subfolder. The final path is `--output-dir/scenario/`.                                     |

## Key Outputs

1. **`synthetic_users.csv`**  
   - **Columns** (sample):  
     - `user_id`, `segment`, `email`, `phone`, `country_code`, `burst_signup`, `is_ring_leader`, `fraud_label`, etc.  
     - Extra engineered columns like `ip_count`, `email_domain`, `num_fraud_biz_owned`.  

2. **`synthetic_businesses.csv`**  
   - **Columns** (sample):  
     - `business_id`, `business_name`, `registration_country`, `owner_name`, `fraud_label`, etc.

3. **`user_user_relationships.csv`**  
   - Pairs of `(from_user_id, to_user_id)` indicating ring-leader edges.

4. **`user_business_relationships.csv`**  
   - Pairs of `(user_id, business_id)` indicating ownership.

## Typical Fraud Rates

- **`low_fraud`**: 5–10% of users/businesses. Minimal ring suspicions.  
- **`default`**: 15–20% range. Moderate suspicion.  
- **`high_fraud`**: 30% user fraud, potentially 98% business fraud if multi-owner pass labeling triggers. Very imbalanced scenario.

## Best Practices

1. **Use a Seed**  
   - If you want reproducible data, pass `--seed <value>`. Otherwise, IP addresses, device IDs, etc. will differ each run.  

2. **Limit Large Generations**  
   - Generating millions of users or businesses can be slow. If you need huge data, consider chunking or incremental runs.  

3. **Multi-Pass**  
   - More passes (e.g., `--iterations 2 or 3`) can amplify ring-based or multi-owner influence. Keep in mind performance trade-offs for large datasets.  

4. **Further Tuning**  
   - You can modify the dictionary `USER_SEGMENTS`, `SCENARIO_CONFIG`, or add watchlist countries/keywords in the script to experiment with different conditions.