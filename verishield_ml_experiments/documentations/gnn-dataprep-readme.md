# **Notebook: `01-GNN-DataPrep-2.ipynb` (Extended for IP Nodes)**

## **Overview**

This notebook transforms **VeriShield synthetic data** (users, businesses, **IPs**, and their relationships) into **graph-ready** arrays for **Graph Neural Network (GNN)** experiments. By extracting numeric features, assigning node indices, and building edge lists (including **user→user**, **user→business**, and **user→IP** edges), it sets the foundation for **ring-based** or **multi-owner** fraud detection, as well as **IP collision** analysis in advanced GNN libraries like **PyTorch Geometric** or **DGL**.

### **Key Objectives**

1. **Load Scenario Data**  
   - Reads **user**, **business**, and **IP** CSVs (e.g., `synthetic_users.csv`, `synthetic_businesses.csv`, `ip_nodes.csv`), plus the relationship files (`user_user_relationships.csv`, `user_business_relationships.csv`, and **`user_ip_relationships.csv`**).

2. **Feature Engineering**  
   - Converts categorical fields (e.g., user segments, suspicious signals) into numeric tensors, handling missing values.  
   - Optional: incorporate IP-based flags if you have suspicious IP ranges.

3. **Node & Edge Mapping**  
   - Assigns **0-based IDs** to **users**, **businesses**, and **IPs**.  
   - Builds **user–user** edges (for ring leaders), **user–business** edges (for ownership), and **user–IP** edges (for collision or shared IP analysis).

4. **Train/Val/Test Splits**  
   - Splits user, business, and optionally IP nodes into **70/15/15** sets (by default) if you want to train and evaluate a multi-node-type classification model.

5. **Save Artifacts**  
   - Exports `.npy` arrays (features, labels, edge lists, masks) under a `processed_gnn/` subfolder for direct usage in GNN libraries.

---

## **Usage & Configuration**

1. **Set the `SCENARIO`**  
   - For example: `SCENARIO = "medium_fraud"` if you have data under `data_generators/data/medium_fraud/`.  
   - Adjust `DATA_BASE_PATH` if your folder structure differs from the default.

2. **Run the Notebook**  
   - Launch `01-GNN-DataPrep-2.ipynb`.  
   - Confirm the CSV files (`synthetic_users.csv`, `synthetic_businesses.csv`, `ip_nodes.csv`, etc.) exist in your scenario path.  
   - Execute the cells in order to generate GNN-compatible files.

3. **Optional Settings**  
   - **`SINGLE_TASK_USER_ONLY`**: If `True`, you focus on user fraud classification only. If `False`, you might handle multi-task classification for both users and businesses.  
   - **Train/Val/Test Splits**: Toggle `DO_SPLIT`. Adjust `TRAIN_RATIO`, `VAL_RATIO`, `TEST_RATIO` as needed. You can even create **IP** splits if you plan to classify IP nodes.

---

## **Notebook Structure**

1. **Cell 1: Imports & Global Settings**  
   - Loads `pandas`, `numpy`, optional PyTorch, sets up display configs.

2. **Cell 2: Configuration**  
   - Defines scenario path, output folder (`processed_gnn`), and ratio splits.  
   - Creates the necessary output directory.

3. **Cell 3: Load CSVs**  
   - Reads:
     - `synthetic_users.csv`  
     - `synthetic_businesses.csv`  
     - **`ip_nodes.csv`**  
     - `user_user_relationships.csv`, `user_business_relationships.csv`, **`user_ip_relationships.csv`**.  
   - Prints shapes to confirm data integrity (e.g., # of rows, columns).

4. **Cell 4: Basic Validation & Checks**  
   - Ensures no out-of-range user, business, or **IP** IDs in the relationship tables.  
   - Drops invalid edges if necessary (e.g., `user_id > number_of_users`).

5. **Cell 5: Feature Engineering**  
   - Encodes user segments (`segment_code`), ring-leader flags, phone/email suspiciousness.  
   - Marks watchlist countries or suspicious business names.  
   - Log-transforms numeric fields (`ip_count_log`, `biz_age_log`).  
   - *(Optional)* Creates a **`susp_ip_flag`** or other fields if you want to store IP-based suspicious signals.

6. **Cell 6: Node ID Assignment & Edge Building**  
   - Converts `user_id`, `business_id`, and **`ip_id`** to 0-based indices (`node_id`).  
   - Builds **user–user**, **user–business**, and **user–ip** edge pairs (e.g., `edge_user_user.npy`, `edge_user_biz.npy`, `edge_user_ip.npy`).

7. **Cell 7: Creating Feature Arrays & Labels**  
   - For **users**: array of shape `[num_users, user_feature_dim]`.  
   - For **businesses**: array of shape `[num_businesses, biz_feature_dim]`.  
   - *(Optional)* For **IPs**: array of shape `[num_ips, ip_feature_dim]`, plus zero or custom `ip_labels` if you’re classifying IP nodes.  

8. **Cell 8: Train/Val/Test Splits**  
   - If `DO_SPLIT = True`, randomly shuffles each node type’s IDs to create boolean masks (`train_mask_users`, etc.).  
   - Splits 70/15/15 by default.

9. **Cell 9: Saving Processed Data**  
   - Writes `.npy` files for:
     - **`user_features.npy`, `user_labels.npy`**  
     - **`biz_features.npy`, `biz_labels.npy`**  
     - **`ip_features.npy`, `ip_labels.npy`** *(if using IP classification)*  
     - **`edge_user_user.npy`, `edge_user_biz.npy`, `edge_user_ip.npy`**  
     - **masks** (`train_mask_users.npy`, etc.)  
   - Creates a **`metadata.json`** capturing scenario details.

---

## **Output Files**

All outputs go to:  
```
/path/to/data_generators/data/<SCENARIO>/processed_gnn/
```
Typical files include:

- **User**:  
  - `user_features.npy` (shape `[num_users, user_feature_dim]`)  
  - `user_labels.npy` (shape `[num_users]`, 0/1 for fraud)  
- **Business**:  
  - `biz_features.npy` (shape `[num_businesses, biz_feature_dim]`)  
  - `biz_labels.npy` (shape `[num_businesses]`, 0/1)  
- **IP** *(Optional)*:  
  - `ip_features.npy` (shape `[num_ips, ip_feature_dim]`)  
  - `ip_labels.npy` (if you plan to label IP nodes)  
- **Edges**:  
  - `edge_user_user.npy` (shape `[2, E_uu]`)  
  - `edge_user_biz.npy` (shape `[2, E_ub]`)  
  - `edge_user_ip.npy` (shape `[2, E_ui]`)  
- **Masks** (if splitting):  
  - `train_mask_users.npy`, `val_mask_users.npy`, `test_mask_users.npy`  
  - `(train/val/test)_mask_biz.npy` if multi-task  
  - `(train/val/test)_mask_ip.npy` if IP classification  
- **`metadata.json`**: scenario, feature columns, ratio splits, edge counts, etc.

---

## **Use in GNN Libraries**

1. **PyTorch Geometric** *(Heterogeneous)*  
   ```python
   from torch_geometric.data import HeteroData
   data = HeteroData()
   data['user'].x = torch.from_numpy(user_features)
   data['user'].y = torch.from_numpy(user_labels)
   data['business'].x = torch.from_numpy(biz_features)
   data['business'].y = torch.from_numpy(biz_labels)
   data['ip'].x = torch.from_numpy(ip_features)       # if using IP nodes
   data['ip'].y = torch.from_numpy(ip_labels)         # if labeling IP nodes

   data[('user','user_user','user')].edge_index = torch.from_numpy(user_user_arr)
   data[('user','user_business','business')].edge_index = torch.from_numpy(user_biz_arr)
   data[('user','user_ip','ip')].edge_index = torch.from_numpy(user_ip_arr)  # new IP edges
   # etc.
   ```

2. **DGL** *(HeteroGraph)*  
   - Similar approach, create node/edge types: `('user','business','owns')`, `('user','ip','collides')`, etc.

3. **Homogeneous Graph**  
   - If you prefer a single adjacency matrix, you can offset IDs or store them in separate ranges. However, a heterogeneous setup often yields more clarity for ring-based and IP-based relationships.

---

## **When to Rerun This Notebook**

- **New Scenario or IP Logic**  
  - If you generate fresh data in `low_fraud` or **added new IP features**, rerun the notebook to create updated `.npy` files.
- **Adjusted Feature Engineering**  
  - If you add suspicious IP range flags, new user fields, or rename columns, you’ll need to regenerate arrays.
- **Model Refresh**  
  - Whenever you add or remove relationships (like user→ip) or change the synergy logic drastically, re-running ensures the node/edge arrays match your new data.

---

With these updates, you can **fully integrate** IP nodes alongside user and business data, preparing a **three-node-type** graph for advanced GNN-based fraud detection.