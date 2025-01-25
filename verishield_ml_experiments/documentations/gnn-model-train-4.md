# **Notebook: `02-Model-Training-GNN-PyTorch-4.ipynb`** 

This README describes the results of training a **multi-task GNN** (with IP classification) on a synthetic **medium_fraud** scenario dataset generated via the **`data-gen-v1.py`** synergy-based script. We used **`01-GNN-DataPrep-2.ipynb`** to preprocess the data into `.npy` files, and ran **`02-Model-Training-GNN-PyTorch-4.ipynb`** to train the final model.

---

## **1. Dataset Overview**

- **Scenario**: `medium_fraud`
- **Number of Entities**:
  - **Users**: 10,000  
  - **Businesses**: 2,500  
  - **IPs**: 2,500  
- **Edges**:
  - `user->user`: 1,024 (duplicated for undirected)  
  - `user->business`: 21,350  
  - `user->ip`: 10,000  
  - Plus reverse edges: `business->rev_user_business->user` and `ip->rev_user_ip->user`
- **Data Splits** (70/15/15):
  - For **users**: 7,000 train, 1,500 val, 1,500 test  
  - For **businesses**: 1,750 train, 375 val, 375 test  
  - For **IPs**: 1,750 train, 375 val, 375 test

### **Metadata**
- **User Features**: 7 columns:  
  1. `segment_code`, 2. `is_ring_leader`, 3. `ip_count_log`, 4. `phone_susp`, 5. `email_susp`, 6. `country_watch`, 7. `burst_signup`
- **Business Features**: 3 columns:  
  1. `watchlist_regctry`, 2. `susp_name_flag`, 3. `biz_age_log`
- **IP Features**: **0** columns (empty Nx0); only a `fraud_label` column was used for classification

For more details, see the **`metadata.json`** file in the `processed_gnn` directory.

---

## **2. GNN Configuration**

- **Model**: `FraudGNN`  
  - 2-layer **HeteroConv** with **SAGEConv** for each relation type (`user_user`, `user_business`, `user_ip`, etc.).  
  - **Hidden Dim**: 64  
  - **Output Heads**: user (2 classes), business (2 classes), IP (2 classes)
- **Multi-Task**:  
  - `MULTI_TASK=True`: simultaneously classifying **users** and **businesses**  
  - `IP_CLASSIFICATION=True`: also classifies **IPs**  
- **Optimizer**: **Adam** with `lr=1e-3`
- **Epochs**: 10  
- **Batch Size**: 1,024 (although the training code still runs full-batch for each step)
- **Steps per Epoch**: 7 (from `train_user_count=7000 / batch_size=1024`, rounded up)

---

## **3. Training & Validation Results**

During training, we logged **loss** and **validation accuracy** for each node type:

| **Epoch** | **Loss** | **User Val Acc** | **Biz Val Acc** | **IP Val Acc** |
|-----------|---------:|-----------------:|-----------------:|---------------:|
| 1         | 2.1874  | 0.5753           | 0.7787          | 0.5973         |
| 2         | 1.9114  | 0.5867           | 0.7787          | 0.6213         |
| 3         | 1.9275  | 0.5840           | 0.7787          | 0.6320         |
| 4         | 1.8964  | 0.5860           | 0.7787          | 0.6347         |
| 5         | 1.8842  | 0.6053           | 0.7787          | 0.6160         |
| 6         | 1.8789  | 0.6080           | 0.7787          | 0.6133         |
| 7         | 1.8727  | 0.6127           | 0.7787          | 0.6213         |
| 8         | 1.8675  | 0.6147           | 0.7787          | 0.6213         |
| 9         | 1.8623  | 0.6147           | 0.7787          | 0.6133         |
| 10        | 1.8572  | 0.6147           | 0.7787          | 0.6107         |

**Note**: The **business** val accuracy plateaued early at ~77.87%. The IP accuracy rose to the 63% range around epoch 4, then hovered near ~61–63%. User accuracy eventually reached ~61–62% on validation.

---

## **4. Final Test Accuracy**

After the final epoch (10):

- **User Test Accuracy**: **64.20%**  
- **Business Test Accuracy**: **76.53%**  
- **IP Test Accuracy**: **60.53%**

Though these numbers may appear moderate, they reflect the complexity of a **multi-task** setting with synergy-based data (ring leaders, multi-owner businesses, and IP collisions). The results show that **business** nodes tend to be easier to classify (perhaps due to stronger or more obvious fraud signals), whereas **users** and **IPs** are more nuanced.

---

## **5. Next Steps & Considerations**

1. **Additional Feature Engineering**  
   - IP nodes currently have **no** features beyond their label. Adding IP-based fields (e.g. `ip_suspicious_flag`, geo-locations, or repeated usage stats) could improve IP classification.
2. **Mini-Batch Implementation**  
   - Right now, we compute **`steps_per_epoch`** from the user train size (7,000) and batch size (1,024), but the code still does a single **full-batch** forward per step. Implementing real node or edge mini-batching (e.g., via neighbor sampling in PyTorch Geometric) could scale better and refine the synergy signals.
3. **Hyperparameter Tuning**  
   - Adjust hidden_dim, learning_rate, or synergy weighting in the generator.  
   - Try more epochs to see if the model converges further.
4. **Precision & Recall**  
   - Accuracy is a coarse metric in fraud detection. You may want to monitor precision, recall, or AUC-PR for each node type—particularly if fraud distribution is skewed.

---

## **6. Conclusion**

This experiment demonstrates a **multi-edge, multi-task** GNN approach on a **medium_fraud** synergy-based dataset. The final test accuracies indicate:

- **Users**: ~64%  
- **Businesses**: ~77%  
- **IPs**: ~61%

While there’s room for improvement, these results confirm that a **single** GNN model can learn from **all** node types (user/business/IP) in **one** forward pass, leveraging synergy-based edges (ring leaders, multi-owner webs, IP collisions) to detect fraud.