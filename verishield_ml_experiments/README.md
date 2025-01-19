# VeriShield-ML-Experiments

**VeriShield-ML-Experiments** is an open-source sandbox designed to **simulate KYC/KYB** environments and **experiment** with various fraud detection methods—ranging from **traditional ML** (XGBoost, Deep Learning) to **graph neural networks** (GNNs). By generating synthetic data under multiple fraud scenarios, it enables **realistic testing** of multi-owner or ring-based fraud patterns.

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

This repository creates a **testbed** for fraud detection research:

- **Synthetic Data**: Generates large-scale user and business datasets with **configurable** fraud rates and advanced collusion patterns (ring leaders, multi-owner).  
- **EDA & Analysis**: Provides **notebooks** to explore missing data, suspicious IP usage, ring-based structures, etc.  
- **Model Training**: Shows how to train **XGBoost** or **Keras** MLP models on tabular data to detect fraud labels.  
- **Graph Workflows**: Prepares data for a **GNN** approach, capturing ring-fraud or multi-owner relationships more naturally than table-based ML.

The code is intended for **data scientists** and **engineers** who need a realistic environment for prototyping advanced fraud detection pipelines.

---

## 2. Directory Structure

```
VeriShield-ML-Experiments/
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
  - **`refined_data_generator.py`**: core script for creating multi-pass fraud data.  
  - **`data/`**: houses scenario-specific CSV outputs (e.g., `high_fraud`).  
  - **`processed_gnn/`**: created after running GNN data prep, storing `.npy` arrays.  

- **`notebooks/EDA/`**: Exploratory analysis of CSV outputs (e.g., `01-EDA-4.ipynb` for ring-leader checks).  
- **`notebooks/Model_Training/`**:  
  - **`01-GNN-DataPrep.ipynb`**: builds node features, edge lists for GNN usage.  
  - **`02-Model-Training-8.ipynb`**: trains XGBoost on user-level fraud.  
  - **`02-Model-Training-10.ipynb`**: trains a Keras MLP for fraud detection.

---

## 3. Prerequisites & Environment

- **Python 3.8+** (3.11 recommended)  
- **Conda** or **virtualenv** for isolation  
- Install dependencies via:
  ```bash
  pip install -r requirements.txt
  ```
- Key libraries:  
  - **pandas, numpy, scikit-learn**  
  - **imblearn** (oversampling)  
  - **xgboost** (XGBoost model)  
  - **tensorflow** (Keras for MLP)  

*(Optional)*: If doing **GNN** experimentation, install **PyTorch Geometric** or **DGL**.

---

## 4. Data Generation Workflow

### Refined Data Generator

- **Script**: `data_generators/refined_data_generator.py`  
- **Purpose**: Produces large user/business datasets with multi-pass fraud labeling. Incorporates ring leaders, multi-owner edges, watchlist countries, etc.

**Command Example**:
```bash
cd data_generators
python refined_data_generator.py --scenario high_fraud \
  --num-users 100000 --num-businesses 10000 \
  --iterations 2 --seed 42
```
Generates **4 CSVs** in `data_generators/data/high_fraud/`:
- `synthetic_users.csv`, `synthetic_businesses.csv`  
- `user_business_relationships.csv`, `user_user_relationships.csv`

### Scenarios & Outputs

- **Scenarios**: `default`, `low_fraud`, `high_fraud`.  
- **Outputs**: user columns (`segment`, `fraud_label`, etc.), business columns (`registration_country`, etc.), plus ring leaders & ownership edges.  
- Multi-pass logic means user labels influence business labels across multiple iterations.

---

## 5. Exploratory Data Analysis

In `notebooks/EDA/`:

1. **`01-EDA-2.ipynb`, `01-EDA-3.ipynb`, `01-EDA-4.ipynb`**:  
   - Load scenario CSVs, check distributions, ring-leader stats, suspicious signals.  
   - Verify missing data or out-of-range IDs are handled properly.  

These notebooks help confirm **data quality** and reveal suspicious patterns (IP collisions, ring leaders, multi-owner businesses) before modeling.

---

## 6. Model Training

### XGBoost

- **Notebook**: `02-Model-Training-8.ipynb`
- **Steps**:
  1. **Load** `synthetic_users_enriched.csv`.  
  2. **Feature Engineering**: phone length, IP flags, watchlist, etc.  
  3. **Split & Oversampling**: upsample minority fraud class.  
  4. **Hyperparameter Tuning**: uses `RandomizedSearchCV` for `max_depth`, `learning_rate`, `n_estimators`, etc.  
  5. **Evaluation**: threshold-based metrics (precision/recall), PR AUC.

### Deep Learning (Keras)

- **Notebook**: `02-Model-Training-10.ipynb`
- **Steps**:
  1. **Load** `synthetic_users_enriched.csv`.  
  2. **Feature Engineering**: create numeric fields for suspicious signals.  
  3. **Train/Test Split** & scaling.  
  4. **Oversampling** with `RandomOverSampler`.  
  5. **MLP**: multiple dense layers, dropout, early stopping.  
  6. **Evaluate** at multiple thresholds, track confusion matrix, PR AUC, etc.

Both pipelines show **moderate** results (50–60% accuracy, PR AUC ~0.4–0.5), highlighting the **complex** nature of ring-based fraud. Real gains often require **graph-based** features.

---

## 7. GNN Data Preparation

### Notebook & Process

- **Notebook**: `01-GNN-DataPrep.ipynb`
- **Purpose**: Converts your CSV data into node features, edge lists, and optional train/val/test splits for GNN usage.

**Key Steps**:
1. **Load** users, businesses, and relationship CSVs.  
2. **Validate** IDs (no out-of-range references).  
3. **Feature Engineer** user and business columns (suspicious phone, watchlist countries, ring-leader flags).  
4. **Construct** `edge_user_user` and `edge_user_biz` arrays; assign 0-based IDs for users/businesses.  
5. **Save** `.npy` files (e.g., `user_features.npy`, `biz_features.npy`, `edge_user_user.npy`, `edge_user_biz.npy`).  
6. (Optional) Create masks (`train_mask_users.npy`) if you plan to classify user nodes.

### Using the Generated Graph Data

- **Hetero Graph**: If you use PyTorch Geometric or DGL, you can store two node types (“user”, “business”) and two edge types (“user_user”, “user_business”).  
- **Monolithic Graph**: Combine all nodes in one index space, but typically less flexible.  
- **Custom Features**: Extend the script if you want to create IP or device nodes, or incorporate edge weights for partial ownership.

---

## 8. Future Directions

1. **Advanced Graph Features**: Turn IP addresses, devices into separate node types for deeper ring detection.  
2. **Temporal GNN**: If sign-up or transaction timestamps matter, adopt dynamic or rolling graph approaches.  
3. **New Fraud Scenarios**: Instead of extreme (`high_fraud ~98% biz fraud`), define balanced or moderate distributions.  
4. **Production Scale**: For millions of entities, consider chunked generation, out-of-memory data handling, or distributed GNN training.

---