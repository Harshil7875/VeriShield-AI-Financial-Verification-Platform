# README: `02-Model-Training-GNN-PyTorch-1.ipynb`

This notebook demonstrates **fraud detection** on a **heterogeneous graph** (users and businesses) using **PyTorch Geometric**. It mirrors the TensorFlow GNN workflow but replaces TensorFlow-specific components with PyTorch modules.

## 1. Purpose

1. **Load Preprocessed `.npy` Data**  
   - Reads user and business features/labels, as well as edge lists and node masks, all exported by a preceding data-preparation step (e.g., `01-GNN-DataPrep.ipynb`).

2. **Build a Heterogeneous Graph**  
   - Uses `torch_geometric.data.HeteroData` to represent node sets (`user`, `business`) and edges (`user_user`, `user_business`).

3. **Define a GNN Model**  
   - Implements a two-layer **`HeteroConv`** with `SAGEConv` for each edge type, aggregating messages from user→user and user→business edges.

4. **Train & Evaluate**  
   - Performs node-level classification on **user** nodes, masking out subsets for training, validation, and testing.  
   - Tracks validation accuracy each epoch and reports final test accuracy.

## 2. Requirements

- **Python 3.7+**  
- **PyTorch** (version >= 1.10 recommended)  
- **PyTorch Geometric** (version >= 2.0)  
- **numpy**  
- **json** (optional, if you want to read `metadata.json`)

### Installing PyTorch & PyG

```bash
# Example (CPU-only), adapt as needed for CUDA:
pip install torch torchvision torchaudio

# Install PyTorch Geometric (CPU-only, or choose correct CUDA for GPU):
pip install torch-scatter torch-sparse torch-geometric
```

Please refer to the official [PyTorch Geometric Installation Guide](https://pytorch-geometric.readthedocs.io/en/latest/notes/installation.html) for platform-specific wheels and CUDA versions.

## 3. Folder Structure & Data

The `.npy` files (features, labels, edges, masks) should exist in:

```
<some_path>/processed_gnn/
  ├── user_features.npy
  ├── user_labels.npy
  ├── biz_features.npy
  ├── biz_labels.npy
  ├── edge_user_user.npy
  ├── edge_user_biz.npy
  ├── train_mask_users.npy
  ├── val_mask_users.npy
  ├── test_mask_users.npy
  └── metadata.json  (optional)
```

- **`user_features.npy`**: shape `[num_users, user_feature_dim]`
- **`user_labels.npy`**: shape `[num_users]`
- **`biz_features.npy`**: shape `[num_businesses, biz_feature_dim]`
- **`biz_labels.npy`**: shape `[num_businesses]` (optional for multi-task)
- **`edge_user_user.npy`**: shape `[2, E_uu]`  
- **`edge_user_biz.npy`**: shape `[2, E_ub]`
- **`train_mask_users.npy`, `val_mask_users.npy`, `test_mask_users.npy`**: shape `[num_users]`, booleans

**Notebook** expects a variable `PROCESSED_DIR` pointing to this folder.

## 4. Usage

1. **Open the Notebook**  
   - Launch Jupyter Lab or Jupyter Notebook and open `02-Model-Training-GNN-PyTorch-1.ipynb`.

2. **Adjust Path & Hyperparameters**  
   - In the **Configuration** section, set `PROCESSED_DIR` to the correct path.  
   - Optionally modify `HIDDEN_DIM`, `LEARNING_RATE`, `EPOCHS`, `STEPS_PER_EPOCH`, etc.

3. **Run the Cells**  
   - Execute the cells **top-to-bottom**.  
   - The notebook will:
     1. Load `.npy` arrays.  
     2. Construct a `HeteroData` object for users/businesses.  
     3. Define a two-layer GNN model (`UserFraudGNN`).  
     4. Train the model for `EPOCHS`, repeatedly applying backprop on the train-mask users.  
     5. Print validation accuracy each epoch and final test accuracy.

4. **Outputs**  
   - You’ll see console logs showing loss values and validation accuracy per epoch.  
   - At the end, you get a final test accuracy for user-fraud classification.

## 5. Notebook Sections

1. **Imports & Setup**  
   - Imports PyTorch, PyG, numpy, and configures the GPU device.

2. **Configuration**  
   - Paths (where `.npy` files live) and hyperparams (model dimensions, etc.).

3. **Data Loading**  
   - Loads `.npy` arrays into PyTorch Tensors (float for features, long for labels/edges, bool for masks).

4. **Build `HeteroData`**  
   - Creates `data['user']`, `data['business']`, and attaches edge sets.  
   - Moves all to `device`.

5. **Model Definition**  
   - `UserFraudGNN` class:  
     - Two rounds of `HeteroConv`, each with a `SAGEConv` sublayer per edge type (user_user, user_business).  
     - Final linear layer outputs `[num_users, 2]`.

6. **Training & Evaluation Functions**  
   - **Train Step**: Forward pass on the entire graph, mask out training users, compute cross-entropy, backprop.  
   - **Evaluate**: Argmax predictions on val or test mask, compute accuracy.

7. **Main Loop**  
   - Repeats training steps multiple times each epoch (`STEPS_PER_EPOCH`), logs average loss.  
   - Evaluates on val set each epoch, then prints final test accuracy.

8. **Wrap-Up**  
   - Ends with a summary.

## 6. Extending the Notebook

- **Conv Layers**: Swap out `SAGEConv` for other PyG layers (like `GATConv` or `GCNConv`).  
- **Mini-Batching**: If your data is too large, consider neighbor sampling (`NeighborLoader`) or cluster-based approaches.  
- **Multi-Task**: If you want to also classify `business` nodes, add a separate output head and compute combined losses.  
- **Advanced Metrics**: Instead of raw accuracy, compute AUC, F1, or other metrics for fraud detection.

## 7. Troubleshooting

- **Module Not Found**: Make sure `torch-geometric` is installed in the same environment.  
- **Memory Issues**: For a very large graph, the full-batch approach may not fit in memory; switch to mini-batching.  
- **Mismatch in .npy Shapes**: Ensure the data generation notebook (`01-GNN-DataPrep.ipynb`) produced the correct shapes and index ranges.
