# VeriShield-ML-Experiments

**VeriShield-ML-Experiments** is an **extension** of the [**VeriShield-AI-Financial-Verification-Platform**](https://github.com/Harshil7875/VeriShield-AI-Financial-Verification-Platform) project, providing a **sandbox** for **synthetic KYC/KYB data generation** and **fraud detection experimentation**. By creating **realistic** multi-owner or ring-based **fraud scenarios**, it supports **XGBoost**, **Deep Learning (MLP)**, and **Graph Neural Network (GNN)** approaches for advanced or **graph-oriented** analysis—including optional **IP** nodes for collision or blacklisted IP detection.

---

## **Table of Contents**

1. [Overview & Purpose](#overview--purpose)  
2. [Directory Structure](#directory-structure)  
3. [Prerequisites & Environment](#prerequisites--environment)  
4. [Data Generation Workflow](#data-generation-workflow)  
   - [Refined Data Generator (Extended)](#refined-data-generator-extended)  
   - [Scenarios & Outputs](#scenarios--outputs)  
5. [Exploratory Data Analysis](#exploratory-data-analysis)  
6. [Model Training & Results](#model-training--results)  
   - [XGBoost (Tabular)](#xgboost-tabular)  
   - [Deep Learning (Keras MLP)](#deep-learning-keras-mlp)  
   - [Graph Neural Networks (GNN)](#graph-neural-networks-gnn)  
   - [Summary of Findings](#summary-of-findings)  
7. [Future Directions](#future-directions)  
8. [License](#license)

---

## **1. Overview & Purpose**

This sub-project **integrates** with the main VeriShield platform (Phase 4 of the [parent repo’s roadmap](https://github.com/Harshil7875/VeriShield-AI-Financial-Verification-Platform)). It focuses on:

- **Synthetic Data**: Generates large-scale user, **business**, and optional **IP** node data with **configurable** fraud rates and advanced collusion patterns (ring leaders, multi-owner webs, watchlist countries, suspicious IP collisions, etc.).  
- **EDA & Analysis**: Provides **notebooks** for discovering suspicious signals like ring networks, multi-owner businesses, or blacklisted IP triggers.  
- **Model Training**: Demonstrates how to train **XGBoost** or **Keras** MLP models on tabular data, plus advanced **GNN** workflows (heterogeneous graph, multi-edge).  
- **Multi-Pass Synergy**: The extended generator script can run multiple labeling passes so user/business/IP fraud labels reinforce each other, mimicking real-world ring-based fraud.

**Real-World Use Case**: Data scientists can **prototype** ring-fraud detection pipelines here, then **deploy** them into the main VeriShield microservices for real-time inference or event-driven (Kafka) processing.

---

## **2. Directory Structure**

```
verishield_ml_experiments/
├── README.md                        <-- You are here!
├── data_generators/
│   ├── refined_data_generator.py    <-- Original generator
│   ├── refined_data_generator_extended.py <-- Extended for IP nodes & synergy
│   ├── data/
│   │   ├── medium_fraud/
│   │   │   ├── synthetic_users.csv
│   │   │   ├── synthetic_businesses.csv
│   │   │   ├── ip_nodes.csv
│   │   │   ├── processed_gnn/
│   │   │   │   ├── user_features.npy
│   │   │   │   ├── biz_features.npy
│   │   │   │   ├── ip_features.npy
│   │   │   │   ├── user_labels.npy
│   │   │   │   ├── biz_labels.npy
│   │   │   │   ├── ip_labels.npy
│   │   │   │   ├── ...
│   │   │   ├── user_user_relationships.csv
│   │   │   ├── user_business_relationships.csv
│   │   │   └── user_ip_relationships.csv
│   │   └── ...
├── documentations/
│   ├── data-gen-readme.md
│   ├── eda-readme.md
│   └── gnn-dataprep-readme.md
├── notebooks/
│   ├── EDA/
│   │   ├── 02-GNN-DataPrep-EDA-1.ipynb   <-- EDA on GNN data (user/biz/IP)
│   │   └── ...
│   └── Model_Training/
│       ├── 01-GNN-DataPrep-2.ipynb      <-- builds .npy features, edges for GNN
│       ├── 02-Model-Training-GNN-PyTorch-3.ipynb  <-- multi-edge GNN approach
│       ├── 02-Model-Training-8.ipynb    <-- XGBoost approach (tabular)
│       ├── 02-Model-Training-10.ipynb   <-- Keras MLP approach (tabular)
└── requirements.txt
```

---

## **3. Prerequisites & Environment**

- **Python 3.8+**  
- **Conda** or **virtualenv** recommended  
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```
- **Key Libraries**:
  - `pandas`, `numpy`, `scikit-learn`, `imblearn`  
  - `xgboost` (for XGBoost training)  
  - `tensorflow` / `keras` (for MLP)  
  - **PyTorch Geometric** (for GNN usage)

*(Optional)*: For advanced usage (temporal GNN, hyperparameter search frameworks), see `gnn-dataprep-readme.md`.

---

## **4. Data Generation Workflow**

### **Refined Data Generator (Extended)**

- **Script**: `refined_data_generator_extended.py`
- **Highlights**:
  1. **Multi-Pass Labeling**: user/business fraud influences each other, plus optional IP synergy.  
  2. **Ring Leaders & Multi-Owner**: 0.5% ring leaders with user→user edges, ~40% users own 1–10 businesses, etc.  
  3. **IP Nodes**: If `--num-ips N > 0`, you also generate `ip_nodes.csv` + user→IP edges.  
  4. **Scenarios**: `low_fraud`, `medium_fraud`, `extreme_fraud`, etc. with varying base rates.

**Example**:
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
Generates CSVs plus any .npy arrays (after data prep in a separate notebook).

### **Scenarios & Outputs**

- **Scenarios**: e.g. `default`, `medium_fraud`, `high_fraud`, `ultra_low_fraud`.  
- **Outputs**:  
  - `synthetic_users.csv`, `synthetic_businesses.csv`, `ip_nodes.csv`  
  - `user_user_relationships.csv`, `user_business_relationships.csv`, `user_ip_relationships.csv`  
  - **(Optional)** `processed_gnn/` with `.npy` arrays for GNN usage (if you run the GNN prep notebook).

---

## **5. Exploratory Data Analysis**

- **EDA Notebooks** in `notebooks/EDA/`:  
  - Check shapes, label distribution, suspicious ring edges, IP collisions.  
  - Confirm data integrity (no out-of-range IDs, ~2–3 new node types, etc.).

---

## **6. Model Training & Results**

We tested multiple approaches on the synthetic data (e.g., `medium_fraud` scenario with ~100k users, 10k businesses, 5k IPs). **Below** are summarized results.

---

### **XGBoost (Tabular)**

**Notebook**: `02-Model-Training-8.ipynb`

1. **Data**  
   - ~1.5 million user records (enriched). Splits: 80/20 → **1.2M** train vs. **300k** test. Fraud ratio ~ 38%.  
   - Feature engineering: ~10–14 numeric/ordinal features (e.g. `gender`, `phone_len`, `email_domain_enc`, `ip_count`).  
   - Class imbalance: oversampled train set to 50/50.  
2. **Hyperparameter Search**  
   - `RandomizedSearchCV` with `learning_rate`, `max_depth`, `n_estimators`, etc.  
   - Best config e.g.: 
     ```python
     {
       'subsample': 0.9,
       'n_estimators': 500,
       'max_depth': 8,
       'learning_rate': 0.1,
       'colsample_bytree': 1.0
     }
     ```
3. **Final Performance (Threshold=0.5)**  
   - **Accuracy**: ~57%  
   - **Precision** (fraud=1): ~45–46%  
   - **Recall** (fraud=1): ~58–59%  
   - **F1**: ~0.51  
   - **AUC-PR** (probabilities): ~0.43–0.44  

*(Note: Setting threshold to 0.3 yields ~100% recall but ~38% precision, threshold 0.7 yields ~0% recall but ~99% legit precision.)*

---

### **Deep Learning (Keras MLP)**

**Notebook**: `02-Model-Training-10.ipynb`

1. **Data**  
   - Similarly ~1.5M user records, ~38% fraud.  
   - Feature set: 14 numeric columns. Oversampled 1.2M→~1.48M.  
   - MLP with 4 hidden layers × 128 units + dropout.  
2. **Training**  
   - 5–10 epochs, early stopping on validation loss.  
   - Because of over-sampling, careful threshold tuning is essential.  
3. **Results** (Threshold=0.5)  
   - **Accuracy**: ~57–58%  
   - **Precision**: ~45–46%  
   - **Recall**: ~58–60%  
   - **F1**: ~0.51–0.52  
   - **AUC-PR**: ~0.45  

*(Similar performance to XGBoost, with some variation in threshold-based metrics.)*

---

### **Graph Neural Networks (GNN)**

**Data Prep**: `01-GNN-DataPrep-2.ipynb` → merges CSV into `.npy` features & edges, e.g. `(user, business, ip)` node sets plus edges:

- `(user, 'user_user', user)`
- `(user, 'user_business', business)`
- `(user, 'user_ip', ip)`
- Reversed edges for business→user, ip→user if you want full message passing.

#### **Notebook**: `02-Model-Training-GNN-PyTorch-3.ipynb`

1. **Multi-Edge, Multi-Task**  
   - Possibly classifying `user.fraud_label`, `business.fraud_label`, `ip.fraud_label`.  
   - HeteroConv with SAGEConv on each relation.  
2. **Example Results**  
   - On a ~**100k users, 10k biz, 5k IP** scenario:  
     - **User Val Accuracy** ~ **74–75%** (some runs reached ~78%).  
     - **Biz Accuracy** typically higher (~95%+ for the scenario’s distribution).  
     - **IP** classification can be near 100% if the generator’s IP label logic is simpler or if few IP nodes are flagged as suspicious.  
3. **Thresholds**  
   - For user classification, ~74–78% accuracy might correspond to ~**74–75%** recall at moderate precision, or vice versa.  
   - The synergy of ring leaders + suspicious IP can yield a bigger improvement vs. purely tabular.  

*(Exact metrics vary by scenario, random seeds, number of IP nodes, synergy passes, etc.)*

---

### **Summary of Findings**

- **Tabular** (XGBoost / MLP) 
  - ~57–58% accuracy, ~0.51–0.52 F1, ~0.43–0.45 PR-AUC, given a ~38% base fraud scenario.  
- **GNN** (multi-edge) 
  - Potentially **higher** user-level accuracy (74–78%), especially if ring-based or IP-based synergy is strong in the data.  
  - Multi-task business classification can reach ~96–97% accuracy if scenario strongly correlates fraudulent owners to biz labels.  
  - IP classification might be near ~99–100% if the generator’s IP logic is simpler or IP coverage is smaller.

*(Your exact results may differ by random seed, scenario settings, hyperparam choices, or synergy passes.)*

---

## **7. Future Directions**

1. **Temporal & Incremental**  
   - Add timestamps for user signups, business creation, IP usage. Possibly use **temporal GNN** or time-based feature engineering.  
2. **Node or Edge-Level Richness**  
   - Store transaction volumes, device fingerprint overlaps, ring expansions.  
   - If you have real or pseudo data, incorporate partial subgraphs for advanced ring detection.  
3. **Scalability**  
   - For very large user sets (1M+), use **Neighbor Sampling** in PyTorch Geometric for mini-batch training.  
   - Explore containerized or distributed solutions if data grows further.  
4. **Metric Priorities**  
   - Real fraud detection often prioritizes **recall** for suspicious accounts or a cost-based approach (balance false positives with false negatives).  
   - Adjust thresholds or train for precision/recall trade-offs that suit real-world production risk appetites.

---

## **8. License**

This project is available under the **[MIT License](../LICENSE)**.  
Contributions or **pull requests** welcome—help expand multi-edge synergy, IP blacklists, or advanced GNN modules.