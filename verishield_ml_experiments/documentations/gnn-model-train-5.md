# **Notebook: `02-Model-Training-GNN-PyTorch-5.ipynb`** 

This README presents **multi-task GNN** training results on a **“high_fraud”** synthetic dataset generated via **`data-gen-v1.py`**. The data was then transformed into GNN-ready arrays (`.npy` files) using **`01-GNN-DataPrep-3.ipynb`**, and finally trained via a **PyTorch Geometric** notebook (`02-Model-Training-GNN-PyTorch-5.ipynb`).

## **1. Dataset Overview**

- **Scenario**: `high_fraud` (starting base rates ~30% user, 25% biz fraud, plus synergy logic)  
- **Number of Entities**:
  - **Users**: 50,000  
  - **Businesses**: 10,000  
  - **IPs**: 8,000  
- **Edges**:
  - `user->user`: 4,918 (duplicated for undirected)  
  - `user->business`: 110,731  
  - `user->ip`: 50,000  
- **Split Ratios**: 70% train, 15% val, 15% test for each node type  

**Resulting CSVs**: `synthetic_users.csv`, `synthetic_businesses.csv`, `ip_nodes.csv`, etc.  
**Processed** into `.npy` arrays under `processed_gnn/` with **real** user, business, and IP fraud labels.

## **2. Model & Training Configuration**

- **Model**: `FraudGNN`  
  - Two **SAGEConv** layers per relation (user↔user, user↔biz, user↔ip) within **HeteroConv** blocks  
  - **Hidden Dim**: 64  
  - **Output Heads**: user (2 classes: legit/fraud), business (2 classes), IP (2 classes)  
- **Multi-Task**: 
  - `MULTI_TASK=True` → user + business classification  
  - `IP_CLASSIFICATION=True` → IP classification as well  
- **Optimizer**: Adam, `lr=0.001`  
- **Epochs**: 200  
- **Batch Size**: 1,024 (though the actual code uses **full-batch** updates each step)  
- **Steps Per Epoch**: 35 (from `train_users=35,000 / 1,024` ≈ 35)  

Each epoch logs **training loss** and **validation accuracies** for users, businesses, and IPs.

## **3. Final Validation Progress**

Here’s a **snapshot** of key validation metrics over time (selected highlights):

| **Epoch** | **Loss**  | **User Val Acc** | **Biz Val Acc** | **IP Val Acc** |
|-----------|----------:|-----------------:|-----------------:|---------------:|
| 1         | 1.6061   | 0.6801           | 0.9227          | 0.6417         |
| 50        | 1.2350   | 0.7132           | 0.9240          | 0.6317         |
| 100       | 1.1356   | 0.7096           | 0.9220          | 0.6217         |
| 150       | 1.0773   | 0.7048           | 0.9173          | 0.6042         |
| 200       | 1.0381   | 0.7065           | 0.9160          | 0.5967         |

**Observations**:

- **Business** val accuracy hovers ~91–92% from early on.  
- **User** and **IP** fluctuate in the 60–70% range.  

## **4. Final Test Accuracies**

After 200 epochs:

- **User Test Accuracy**: **69.44%**  
- **Business Test Accuracy**: **91.87%**  
- **IP Test Accuracy**: **61.50%**

**Interpretation**:

- **Business** classification is comparatively easier (91.87% test accuracy). Possibly because the synergy logic or watchlist flags provide strong, consistent indicators.  
- **User** classification (~69.44%) and **IP** classification (~61.50%) are more challenging, reflecting the **high_fraud** scenario’s strong synergy webs. Some features might still be too subtle or overshadowed by the large dataset complexity.  
- The IP feature matrix is **empty** (Nx0) in this dataset; IP classification relies on adjacency synergy alone.

## **5. Next Steps**

1. **Additional IP Features**:  
   - IPs have no numeric or categorical features besides the label. Adding IP-based columns (e.g., geo-locations, blacklisted IP ranges) could help push IP accuracy higher.  
2. **Mini-Batching**:  
   - The training script sets `BATCH_SIZE=1024` but does a full-graph forward each step. Implementing **neighbor sampling** or other mini-batching can improve scalability with 50k+ nodes.  
3. **Advanced Synergy**:  
   - Possibly tune synergy weighting (the ratio at which ring leaders, IP collisions, or multi-owner webs influence labeling) in `data-gen-v1.py` for less or more correlation.  
4. **Precision/Recall**:  
   - Since ~50–70% of nodes are fraud, tracking precision/recall or confusion matrices might be more informative than raw accuracy.

---

**In summary**, on the **high_fraud** synergy-based dataset (50k users, 10k biz, 8k IPs), our multi-task GNN achieves **~69.44% user**, **91.87% business**, **61.50% IP** test accuracy after 200 epochs. While business classification remains high, further feature engineering or synergy tuning is recommended for improving user/IP performance in heavily fraudulent environments.
