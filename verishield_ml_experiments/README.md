# VeriShield-ML-Experiments

**VeriShield-ML-Experiments** is an **extension** of the [**VeriShield-AI-Financial-Verification-Platform**](https://github.com/Harshil7875/VeriShield-AI-Financial-Verification-Platform) project, providing a **sandbox** for **synthetic KYC/KYB data generation** and **fraud detection experimentation**. By creating **realistic** multi-owner or ring-based **fraud scenarios**, it supports **XGBoost**, **Deep Learning (MLP)**, and **Graph Neural Network (GNN)** approaches for advanced or **graph-oriented** analysis—including optional **IP** nodes for collision or blacklisted IP detection.

---

## **Table of Contents**

1. [Overview & Purpose](#overview--purpose)  
2. [Directory Structure](#directory-structure)  
3. [Prerequisites & Environment](#prerequisites--environment)  
4. [Data Generation Workflow](#data-generation-workflow)  
   - [Synergy-Based Data Generation (`data-gen-v1.py`)](#synergy-based-data-generation-data-gen-v1py)  
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
- **Model Training**: Demonstrates how to train **XGBoost** or **Keras** MLP models on tabular data, plus advanced **GNN** workflows (heterogeneous graph, multi-edge) for ring-fraud detection.  
- **Synergy-Based Labeling**: Allows multi-pass user/business/IP labeling so entities reinforce each other’s fraud probability, **mimicking real-world ring-based** scenarios.

**Real-World Use Case**: Data scientists can **prototype** ring-fraud detection pipelines here, then **deploy** them into the main VeriShield microservices for real-time inference or event-driven (Kafka) processing.

---

## **2. Directory Structure**

```
verishield_ml_experiments/
├── README.md                        <-- You are here!
├── data_generators/
│   ├── data-gen-v1.py              <-- "Ideal" synergy-based generator (near 50% final fraud)
│   ├── refined_data_generator_extended.py <-- older extended generator
│   ├── data/
│   │   ├── medium_fraud/
│   │   ├── high_fraud/
│   │   └── ...
│   ├── data-v1/
│   │   ├── medium_fraud/
│   │   ├── high_fraud/
│   │   └── ...
│   └── ...
├── documentations/
│   ├── data-gen-readme.md
│   ├── eda-readme.md
│   └── gnn-dataprep-readme.md
├── notebooks/
│   ├── EDA/
│   │   ├── 02-GNN-DataPrep-EDA-1.ipynb   <-- EDA on GNN data (user/biz/IP)
│   │   └── ...
│   └── Model_Training/
│       ├── 01-GNN-DataPrep-3.ipynb      <-- builds .npy features, edges for GNN
│       ├── 02-Model-Training-GNN-PyTorch-4.ipynb  <-- multi-edge GNN approach
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

### **Synergy-Based Data Generation (`data-gen-v1.py`)**

- **Script**: `data-gen-v1.py`
- **Highlights**:
  1. **Iterative Convergence to ~50% Fraud**: Adjusts base rates each pass so users/businesses/IPs collectively approach 50% fraud (±2%).  
  2. **Ring & Multi-Owner**: e.g., 0.5% ring leaders, 40% of users own multiple businesses, plus IP collisions.  
  3. **Synergy**: user↔biz↔ip synergy repeats until stable.  
  4. **Scenarios**: `low_fraud`, `medium_fraud`, `high_fraud`, etc. start at different base rates.  
  5. **Final CSVs**: `synthetic_users.csv`, `synthetic_businesses.csv`, `ip_nodes.csv`, plus relationship files.

**Example**:
```bash
cd data_generators
python data-gen-v1.py \
    --scenario high_fraud \
    --num-users 50000 \
    --num-businesses 10000 \
    --num-ips 8000 \
    --seed 999 \
    --output-dir ./data-v1
```
Generates synergy-based CSVs in `./data-v1/high_fraud/`.

### **Scenarios & Outputs**

- **Scenarios**: `low_fraud`, `default`, `medium_fraud`, `high_fraud`, `extreme_fraud`.  
- **Outputs**:  
  - `synthetic_users.csv`, `synthetic_businesses.csv`, `ip_nodes.csv`  
  - `user_user_relationships.csv`, `user_business_relationships.csv`, `user_ip_relationships.csv`  
  - Each scenario in a subfolder, e.g. `data-v1/medium_fraud/`.

---

## **5. Exploratory Data Analysis**

- **EDA Notebooks** in `notebooks/EDA/`:  
  - Check shapes, label distribution, suspicious ring edges, IP collisions.  
  - Confirm data integrity (no out-of-range IDs, synergy-based or near-50% final rates, etc.).

---

## **6. Model Training & Results**

After generating CSVs, **convert** them into `.npy` arrays for GNN usage with a `01-GNN-DataPrep-*.ipynb`.  
Then train with `02-Model-Training-*` notebooks (XGBoost, MLP, or GNN).

### **XGBoost (Tabular)**

- **Notebook**: `02-Model-Training-8.ipynb`
- Typically ~57–58% user accuracy on a 38% base fraud scenario.  
- Class imbalance solutions (oversampling, threshold tuning) crucial.

### **Deep Learning (Keras MLP)**

- **Notebook**: `02-Model-Training-10.ipynb`
- Similar performance to XGBoost (~57–58% accuracy).  
- Can be more flexible with hidden layers, dropout.

### **Graph Neural Networks (GNN)**

- **Notebook**: `02-Model-Training-GNN-PyTorch-4.ipynb` (extended for multi-task IP).
- Builds a **heterogeneous** graph with user, business, IP node types.  
- Multi-edge synergy can significantly improve user-level or business-level fraud detection if ring or IP collisions are strong.

### **Summary of Findings**

- **Tabular**: ~57–60% user accuracy, can be boosted with heavy feature engineering.  
- **GNN**: Often yields higher synergy-based accuracy for users, can exceed 70–75% if ring or IP collusion is strong. Business classification might reach 90–95% if watchlist or multiple owners strongly correlate. IP classification depends on whether IP has real features or synergy alone.

---

## **7. Future Directions**

1. **Temporal & Incremental**  
   - Add timestamps or daily signups, enabling time-based synergy or temporal GNN.  
2. **Scalability**  
   - For huge data (1M+ users), implement mini-batching or neighbor sampling in PyTorch Geometric.  
3. **IP Feature Enrichment**  
   - Currently, IP features are often Nx0. Add geolocation, blacklisted ranges, usage frequency, etc.  
4. **Real Hybrid Data**  
   - If partial real data is available, integrate subgraphs into the synergy approach.

---

## **8. License**

This project is available under the **[MIT License](../LICENSE)**.  
Contributions or **pull requests** welcome—help expand multi-edge synergy, IP blacklists, or advanced GNN modules.