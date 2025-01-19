# VeriShield-ML-Experiments

**VeriShield-ML-Experiments** is an **extension** of the [**VeriShield-AI-Financial-Verification-Platform**](https://github.com/Harshil7875/VeriShield-AI-Financial-Verification-Platform) project, providing a **sandbox** for **synthetic KYC/KYB data generation** and **fraud detection experimentation**. By creating **realistic multi-owner or ring-based** fraud scenarios, it supports **XGBoost**, **Deep Learning**, and **Graph Neural Network** (GNN) approaches for more advanced or **graph-oriented** analysis.

---

## Table of Contents

1. [Overview & Purpose](#overview--purpose)  
2. [Directory Structure](#directory-structure)  
3. [Prerequisites & Environment](#prerequisites--environment)  
4. [Data Generation Workflow](#data-generation-workflow)  
   - [Refined Data Generator](#refined-data-generator)  
   - [Scenarios & Outputs](#scenarios--outputs)  
5. [Exploratory Data Analysis](#exploratory-data-analysis)  
6. [Model Training](#model-training)  
   - [XGBoost](#xgboost)  
   - [Deep Learning (Keras)](#deep-learning-keras)  
7. [GNN Data Preparation](#gnn-data-preparation)  
   - [Notebook & Process](#notebook--process)  
   - [Using the Generated Graph Data](#using-the-generated-graph-data)  
8. [Future Directions](#future-directions)  
9. [License](#license)

---

## 1. Overview & Purpose

This sub-project **integrates** with the main VeriShield platform (Phase 4 of the [parent repo’s roadmap](https://github.com/Harshil7875/VeriShield-AI-Financial-Verification-Platform)). It focuses on:

- **Synthetic Data**: Generates large-scale user and business datasets with **configurable** fraud rates and advanced collusion patterns (ring leaders, multi-owner, watchlist countries, etc.).  
- **EDA & Analysis**: Provides **notebooks** for discovering suspicious signals like IP collisions, ring networks, and multi-owner businesses.  
- **Model Training**: Demonstrates how to train **XGBoost** or **Keras** MLP models on tabular data for fraud detection.  
- **Graph Workflows**: Prepares data for a **GNN** approach, capturing ring-fraud or multi-owner relationships more naturally than standard ML.

**Use Case**: Data scientists or engineers can **prototype** advanced fraud detection pipelines here. Then, once models are refined, they can be **integrated** into the main VeriShield microservice or Kafka consumer for real-time scoring.

---

## 2. Directory Structure

```
verishield_ml_experiments/
├── README.md                           <-- You are here!
├── data_generators/
│   ├── refined_data_generator.py       <-- Main script for generating CSVs
│   ├── full_data_generator.py          <-- Older generator script
│   ├── data/
│   │   ├── default/
│   │   ├── low_fraud/
│   │   └── high_fraud/
│   └── ...
├── documentations/
│   ├── brainstorm-gnn.md
│   ├── data-gen-readme.md
│   ├── eda-readme.md
│   └── gnn-dataprep-readme.md
├── notebooks/
│   ├── EDA/
│   │   ├── 01-EDA-2.ipynb
│   │   ├── 01-EDA-3.ipynb
│   │   └── 01-EDA-4.ipynb
│   └── Model_Training/
│       ├── 01-GNN-DataPrep.ipynb      <-- GNN data prep notebook
│       ├── 02-Model-Training-8.ipynb  <-- XGBoost approach
│       ├── 02-Model-Training-10.ipynb <-- Deep Learning approach
└── requirements.txt
```

- **`data_generators/`**:
  - **`refined_data_generator.py`**: main generator for multi-pass fraud labeling.  
  - **`data/`**: scenario-specific CSV outputs (`default`, `low_fraud`, `high_fraud`).  
  - **`processed_gnn/`** subfolder: created after GNN data prep, storing `.npy` arrays.  
- **`notebooks/EDA/`**: Exploratory notebooks analyzing CSV outputs.  
- **`notebooks/Model_Training/`**:
  - **`01-GNN-DataPrep.ipynb`**: builds node features & edges for GNN usage.  
  - **`02-Model-Training-8.ipynb`**: trains XGBoost on user-level fraud.  
  - **`02-Model-Training-10.ipynb`**: trains a Keras MLP on user-level fraud.

---

## 3. Prerequisites & Environment

- **Python 3.8+** (3.11 recommended)  
- **Conda** or **virtualenv** for isolation  
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```
- **Key Libraries**:
  - `pandas`, `numpy`, `scikit-learn`  
  - `imblearn` (oversampling)  
  - `xgboost` (for XGBoost training)  
  - `tensorflow` (Keras MLP)  

*(Optional)*: If exploring **GNN** usage, install **PyTorch Geometric** or **DGL**.

> For **deployment** or **event-driven** integration, see the main [VeriShield-AI-Financial-Verification-Platform](https://github.com/Harshil7875/VeriShield-AI-Financial-Verification-Platform) repo.

---

## 4. Data Generation Workflow

### Refined Data Generator

- **Script**: `data_generators/refined_data_generator.py`
- **Highlights**:
  1. **Multi-Pass Labeling**: user/business fraud influences each other over multiple iterations.  
  2. **Ring Leaders**: ~0.5% of users become ring leaders, linking to multiple other users.  
  3. **Ownership Edges**: users can own multiple businesses, creating multi-owner webs.

**Usage Example**:
```bash
cd data_generators
python refined_data_generator.py --scenario high_fraud \
  --num-users 100000 --num-businesses 10000 \
  --iterations 2 --seed 42
```
Generates 4 CSVs (e.g., `synthetic_users.csv`, `synthetic_businesses.csv`, etc.) in `data_generators/data/high_fraud/`.

### Scenarios & Outputs

- **Scenarios**: `default`, `low_fraud`, `high_fraud` (modify base fraud rates).  
- **Outputs**: user columns (`segment`, `fraud_label`, etc.), business columns (`registration_country`, etc.), plus ring leader and ownership edges.  
- Adjust `--iterations` to increase label cross-influence.

---

## 5. Exploratory Data Analysis

- **EDA Notebooks**: In `notebooks/EDA/` (`01-EDA-2.ipynb`, `01-EDA-3.ipynb`, `01-EDA-4.ipynb`).  
- Inspect: ring-leader frequency, IP collisions, watchlist countries, business fraud distribution, etc.  
- Confirms data integrity before proceeding to model training.

---

## 6. Model Training

### XGBoost

- **Notebook**: `02-Model-Training-8.ipynb`
- **Steps**:
  1. Load an enriched CSV (e.g., `synthetic_users_enriched.csv`).  
  2. Feature engineering (phone length, suspicious IP/email, etc.).  
  3. Split & oversample.  
  4. Tune hyperparams with `RandomizedSearchCV`.  
  5. Evaluate with threshold-based metrics (precision, recall, PR AUC).

### Deep Learning (Keras)

- **Notebook**: `02-Model-Training-10.ipynb`
- **Steps**:
  1. Load and preprocess data similarly.  
  2. Build a Keras MLP (dense layers + dropout).  
  3. Train with early stopping; evaluate at multiple thresholds.  
  4. Typically sees moderate performance (~50–60% accuracy).

Both approaches highlight **imbalance** and **complex collusion** patterns—why GNN or advanced feature engineering can help.

---

## 7. GNN Data Preparation

### Notebook & Process

- **`01-GNN-DataPrep.ipynb`**: transforms your CSV data into node feature matrices, edge lists, and optional train/val/test masks for user nodes.

**Key Steps**:
1. Load raw CSVs (`synthetic_users.csv`, etc.).  
2. Validate IDs, drop out-of-range references.  
3. Create numeric or boolean features (ring leader, suspicious phone, etc.).  
4. Build adjacency arrays for **user–user** and **user–business**.  
5. Save `.npy` arrays (e.g., `user_features.npy`, `edge_user_user.npy`) under `processed_gnn/`.

### Using the Generated Graph Data

- **PyTorch Geometric** or **DGL**: create a heterograph with two node types (`user`, `business`) and two edge types (`user_user`, `user_business`).  
- Explore ring-based or multi-owner fraud detection in a more natural, multi-hop fashion.

---

## 8. Future Directions

1. **Advanced Graph Features**: IP addresses or devices as separate nodes.  
2. **Temporal GNN**: incorporate timestamps for sign-up or ownership changes.  
3. **Scenario Diversity**: beyond `high_fraud`, create mid-level or time-based scenarios.  
4. **Production Scale**: for millions of nodes, consider chunked generation or distributed GNN training.

---

**Note**: For **deployment** or **real-time inference** details, refer to the [parent VeriShield repo](https://github.com/Harshil7875/VeriShield-AI-Financial-Verification-Platform), which implements FastAPI, Kafka, Neo4j, and a microservices architecture. This sub-project **focuses** on offline data generation, EDA, and ML prototyping—**tying** into the main system’s event-driven flows (Phase 4) once models are ready.
