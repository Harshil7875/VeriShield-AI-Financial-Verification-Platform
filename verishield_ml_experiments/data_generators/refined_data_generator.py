#!/usr/bin/env python3
"""
refined_data_generator.py

A multi-phase, highly configurable synthetic data generator for VeriShield Phase 4+.

Changes in this version:
------------------------
1. A new command-line argument: --output-dir (default: "./data")
   - This sets a parent directory where subfolders for each scenario are created.
2. All CSV outputs go to:  {output_dir}/{scenario}/
   e.g., ./data/high_fraud/synthetic_users.csv
3. If the subfolder doesn't exist, it's created automatically.
"""

import os
import random
import argparse
import pandas as pd
from faker import Faker
from datetime import timedelta, datetime

###############################################################################
# GLOBAL DEFAULTS & CONFIG
###############################################################################
DEFAULT_NUM_USERS = 100_000
DEFAULT_NUM_BUSINESSES = 10_000
DEFAULT_OUTPUT_DIR = "./data"
MISSING_FIELD_PROB = 0.02  # 2% chance to null out certain fields

fake = Faker()

# Adjust to your liking for advanced distribution
USER_SEGMENTS = {
    "casual":     (0.70, 0.0),   # 70% of users, normal base
    "smb_owner":  (0.20, 0.05),  # 20% of users, slightly higher fraud
    "enterprise": (0.09, -0.05), # 9% of users, lower fraud
    "money_mule": (0.01, 0.40),  # 1% of users, much higher fraud
}

SCENARIO_CONFIG = {
    "low_fraud":  {"user_base_fraud": 0.05, "biz_base_fraud": 0.05},
    "high_fraud": {"user_base_fraud": 0.30, "biz_base_fraud": 0.25},
    "default":    {"user_base_fraud": 0.15, "biz_base_fraud": 0.10},
}

WATCHLIST_COUNTRIES = ["NK", "IR", "SY", "CU", "AF", "SO", "LY"]

COUNTRY_PHONE_PREFIXES = {
    "US": ["+1", "+000", "+999"],
    "GB": ["+44", "+999", "+000"],
    "DE": ["+49", "+999"],
    "AU": ["+61", "+999"],
}

SUSPICIOUS_EMAIL_DOMAINS = [
    "@tempmail.xyz", "@disposable.com", "@fakemail.com",
    "@throwaway.io", "@spamgourmet.com", "@sharklasers.com",
    "@guerrillamail.com", "@maildrop.cc"
]

###############################################################################
# STEP 1: GENERATE UNLABELED USERS & BUSINESSES
###############################################################################

def pick_user_segment() -> str:
    r = random.random()
    cumulative = 0.0
    for seg, (prob, _) in USER_SEGMENTS.items():
        cumulative += prob
        if r < cumulative:
            return seg
    return "casual"  # fallback

def generate_unlabeled_users(num_users: int):
    users = []
    collision_map = _build_ip_collision_map(num_users, ratio=0.20)
    base_start = datetime.now() - timedelta(days=90)

    for i in range(num_users):
        user_id = i + 1
        user = _create_base_user_record(user_id, collision_map, base_start)
        users.append(user)

    return pd.DataFrame(users)

def _build_ip_collision_map(total_users: int, ratio: float = 0.20):
    num_colliding = int(total_users * ratio)
    # Limit distinct IPs to reduce collisions
    repeated_ips = [fake.ipv4_public() for _ in range(500)]
    mapping = {}
    for i in range(num_colliding):
        ip_choice = random.choice(repeated_ips)
        mapping[i+1] = {
            "ip": ip_choice,
            "device_id": fake.lexify(text="device_????????")
        }
    return mapping

def _create_base_user_record(user_id: int, collision_map: dict, base_start: datetime):
    profile = fake.simple_profile()
    collision_entry = collision_map.get(user_id)

    if collision_entry:
        signup_ip = collision_entry["ip"]
        device_id = collision_entry["device_id"]
    else:
        signup_ip = fake.ipv4_public()
        device_id = fake.lexify(text="device_????????")

    cc = fake.country_code()
    prefix_list = COUNTRY_PHONE_PREFIXES.get(cc, [])
    if not prefix_list:
        prefix_list = ["+999", "+000", "555-", fake.msisdn()[:3]]
    prefix = random.choice(prefix_list)
    phone_val = prefix + str(random.randint(1000000, 9999999))

    days_offset = random.randint(0, 90)
    suspicious_burst = False
    if random.random() < 0.05:
        suspicious_burst = True
        created_dt = base_start + timedelta(days=days_offset, seconds=random.randint(0, 60))
    else:
        created_dt = base_start + timedelta(days=days_offset, seconds=random.randint(0, 86400))

    seg = pick_user_segment()

    user_dict = {
        "user_id": user_id,
        "segment": seg,
        "name": profile["name"],
        "email": profile["mail"],
        "username": profile["username"],
        "birthdate": profile["birthdate"].isoformat() if profile["birthdate"] else None,
        "gender": profile["sex"],
        "signup_ip": signup_ip,
        "device_id": device_id,
        "phone": phone_val,
        "country_code": cc,
        "created_at": created_dt,
        "burst_signup": suspicious_burst,
        "fraud_label": None,
    }

    # Random missing fields
    for f in ["name", "email", "phone", "country_code"]:
        if random.random() < MISSING_FIELD_PROB:
            user_dict[f] = None

    return user_dict

def generate_unlabeled_businesses(num_businesses: int):
    biz_list = []
    for i in range(num_businesses):
        biz_id = i + 1
        biz_name = random.choice([
            fake.company(),
            fake.company_suffix(),
            "FakeCo " + fake.word(),
            fake.bs(),
            "Phantom Inc " + fake.color_name()
        ])
        reg_ctry = fake.country_code()
        biz_dict = {
            "business_id": biz_id,
            "business_name": biz_name,
            "registration_country": reg_ctry,
            "incorporation_date": fake.date_between(start_date="-15y", end_date="today"),
            "owner_name": fake.name(),
            "fraud_label": None,
        }

        if random.random() < MISSING_FIELD_PROB:
            biz_dict["registration_country"] = None
        if random.random() < MISSING_FIELD_PROB:
            biz_dict["owner_name"] = None

        biz_list.append(biz_dict)

    return pd.DataFrame(biz_list)

###############################################################################
# STEP 2: USER-USER RELATIONSHIPS
###############################################################################

def create_user_user_relationships(df_users: pd.DataFrame, ring_leader_fraction=0.005) -> pd.DataFrame:
    df_users["is_ring_leader"] = False
    user_count = len(df_users)
    ring_leader_count = int(user_count * ring_leader_fraction)

    # randomly pick ring leaders
    ring_leader_ids = random.sample(df_users["user_id"].tolist(), ring_leader_count)
    df_users.loc[df_users["user_id"].isin(ring_leader_ids), "is_ring_leader"] = True

    user_user_edges = []
    for leader_id in ring_leader_ids:
        link_count = random.randint(5, 15)
        possible_targets = list(set(df_users["user_id"]) - {leader_id})
        link_count = min(link_count, len(possible_targets))
        targets = random.sample(possible_targets, link_count)
        for t in targets:
            user_user_edges.append({
                "from_user_id": leader_id,
                "to_user_id": t
            })

    return pd.DataFrame(user_user_edges)

###############################################################################
# STEP 3: USER-BUSINESS RELATIONSHIPS
###############################################################################

def link_users_to_businesses(df_users: pd.DataFrame, df_biz: pd.DataFrame,
                            base_ownership_prob=0.4, max_biz_per_user=10,
                            allow_multi_ownership=True) -> pd.DataFrame:
    relationships = []
    user_ids = df_users["user_id"].tolist()
    biz_ids = df_biz["business_id"].tolist()

    for u in user_ids:
        if random.random() < base_ownership_prob:
            count = random.randint(1, max_biz_per_user)
            chosen_biz = random.sample(biz_ids, min(count, len(biz_ids)))
            for b in chosen_biz:
                relationships.append({"user_id": u, "business_id": b})

    return pd.DataFrame(relationships)

###############################################################################
# STEP 4: MULTI-PASS LABEL ASSIGNMENT
###############################################################################

def assign_fraud_labels_users(df_users: pd.DataFrame, df_biz: pd.DataFrame,
                              df_user_biz: pd.DataFrame, df_user_user: pd.DataFrame,
                              scenario_params: dict, iteration=1):
    user_base_fraud = scenario_params["user_base_fraud"]
    # business label map
    biz_fraud_map = dict(zip(df_biz["business_id"], df_biz["fraud_label"]))
    # coalesce None => 0
    for k, v in biz_fraud_map.items():
        if v is None:
            biz_fraud_map[k] = 0

    user_to_biz = df_user_biz.groupby("user_id")["business_id"].apply(list).to_dict()

    new_labels = []
    for idx, row in df_users.iterrows():
        p = user_base_fraud
        seg = row.get("segment", "casual")
        _, seg_fraud_mod = USER_SEGMENTS.get(seg, (1.0, 0.0))
        p += seg_fraud_mod

        email = (row.get("email") or "").lower()
        if any(d in email for d in SUSPICIOUS_EMAIL_DOMAINS):
            p += 0.20
        phone = str(row.get("phone") or "")
        if len(phone) < 7:
            p += 0.10
        elif any(x in phone for x in ["+999", "666-666"]):
            p += 0.15
        if row.get("burst_signup"):
            p += 0.15

        if row.get("is_ring_leader", False):
            p += 0.30

        owned_biz_ids = user_to_biz.get(row["user_id"], [])
        known_fraud_biz_count = sum(biz_fraud_map.get(bid, 0) for bid in owned_biz_ids)
        p += 0.05 * known_fraud_biz_count

        label = 1 if random.random() < max(0, p) else 0

        # forced overrides
        if label == 0 and p < 0.2 and random.random() < 0.02:
            label = 1
        if label == 1 and p > 0.4 and random.random() < 0.02:
            label = 0

        new_labels.append(label)

    df_users["fraud_label"] = new_labels
    return df_users


def assign_fraud_labels_businesses(df_users: pd.DataFrame, df_biz: pd.DataFrame,
                                   df_user_biz: pd.DataFrame, scenario_params: dict, iteration=1):
    biz_base_fraud = scenario_params["biz_base_fraud"]
    user_fraud_map = dict(zip(df_users["user_id"], df_users["fraud_label"]))
    # coalesce None => 0
    for k, v in user_fraud_map.items():
        if v is None:
            user_fraud_map[k] = 0

    biz_to_users = df_user_biz.groupby("business_id")["user_id"].apply(list).to_dict()

    new_labels = []
    for idx, row in df_biz.iterrows():
        p = biz_base_fraud
        bname = (row.get("business_name") or "").lower()
        if any(k in bname for k in ["test", "fake", "shell", "phantom", "bogus", "shady"]):
            p += 0.15
        reg_ctry = (row.get("registration_country") or "").upper()
        if reg_ctry in WATCHLIST_COUNTRIES:
            p += 0.20

        if random.random() < 0.03:
            p += 0.10

        owners = biz_to_users.get(row["business_id"], [])
        num_fraud_owners = sum(user_fraud_map.get(uid, 0) for uid in owners)
        p += 0.10 * num_fraud_owners

        label = 1 if random.random() < max(0, p) else 0

        if label == 0 and p < 0.2 and random.random() < 0.02:
            label = 1
        if label == 1 and p > 0.4 and random.random() < 0.02:
            label = 0

        new_labels.append(label)

    df_biz["fraud_label"] = new_labels
    return df_biz

###############################################################################
# STEP 5: FEATURE ENRICHMENT
###############################################################################

def enrich_user_features(df_users, df_user_biz, df_biz):
    df_users["email_domain"] = df_users["email"].apply(
        lambda x: x.split('@')[-1] if x and '@' in str(x) else "missing"
    )

    ip_counts = df_users.groupby("signup_ip")["user_id"].transform("count")
    df_users["ip_count"] = ip_counts

    df_merged = df_user_biz.merge(df_biz[["business_id", "fraud_label"]], on="business_id", how="left")
    df_merged["fraud_label"] = df_merged["fraud_label"].fillna(0)

    fraud_count = df_merged.groupby("user_id")["fraud_label"].sum().reset_index(name="num_fraud_biz_owned")
    df_users = df_users.merge(fraud_count, on="user_id", how="left")
    df_users["num_fraud_biz_owned"] = df_users["num_fraud_biz_owned"].fillna(0)

    return df_users

###############################################################################
# MAIN
###############################################################################

def main():
    parser = argparse.ArgumentParser(description="Refined multi-pass data generator for VeriShield.")
    parser.add_argument("--num-users", type=int, default=DEFAULT_NUM_USERS)
    parser.add_argument("--num-businesses", type=int, default=DEFAULT_NUM_BUSINESSES)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--scenario", type=str, default="default",
                        choices=["default", "low_fraud", "high_fraud"])
    parser.add_argument("--iterations", type=int, default=1)
    parser.add_argument("--output-dir", type=str, default=DEFAULT_OUTPUT_DIR,
                        help="Parent directory to store scenario subfolders. Default=./data")
    args = parser.parse_args()

    # Set seeds
    if args.seed is not None:
        random.seed(args.seed)
        Faker.seed(args.seed)
        print(f"[INFO] Seed set to {args.seed}")

    scenario_params = SCENARIO_CONFIG.get(args.scenario, SCENARIO_CONFIG["default"])
    scenario_name = args.scenario  # "default", "low_fraud", or "high_fraud"

    print(f"===== Refined Data Generation (Scenario: {scenario_name}) =====")
    print(f"Users: {args.num_users}, Businesses: {args.num_businesses}")
    print(f"Base user fraud: {scenario_params['user_base_fraud']} | "
          f"Biz base fraud: {scenario_params['biz_base_fraud']}")
    print(f"Label Assignment Iterations: {args.iterations}")

    # 1) Generate unlabeled
    print("-> Generating unlabeled users & businesses...")
    df_users = generate_unlabeled_users(args.num_users)
    df_biz = generate_unlabeled_businesses(args.num_businesses)

    # 2) user-user relationships
    df_user_user = create_user_user_relationships(df_users, ring_leader_fraction=0.005)
    print(f"[INFO] Created {len(df_user_user)} user-user relationships.")

    # 3) user-biz relationships
    df_user_biz = link_users_to_businesses(df_users, df_biz,
                                           base_ownership_prob=0.40,
                                           max_biz_per_user=10)
    print(f"[INFO] Created {len(df_user_biz)} user-business relationships.")

    # 4) Multi-pass labeling
    for i in range(args.iterations):
        print(f"-> Labeling pass {i+1} of {args.iterations}...")
        df_users = assign_fraud_labels_users(
            df_users, df_biz, df_user_biz, df_user_user, scenario_params, iteration=i+1
        )
        df_biz = assign_fraud_labels_businesses(
            df_users, df_biz, df_user_biz, scenario_params, iteration=i+1
        )

    # 5) Enrichment
    df_users = enrich_user_features(df_users, df_user_biz, df_biz)

    # Prepare output directory
    scenario_dir = os.path.join(args.output_dir, scenario_name)
    os.makedirs(scenario_dir, exist_ok=True)
    print(f"-> CSV outputs will be saved to: {scenario_dir}")

    # Write CSVs
    users_csv = os.path.join(scenario_dir, "synthetic_users.csv")
    biz_csv = os.path.join(scenario_dir, "synthetic_businesses.csv")
    rel_user_biz_csv = os.path.join(scenario_dir, "user_business_relationships.csv")
    rel_user_user_csv = os.path.join(scenario_dir, "user_user_relationships.csv")

    df_users.to_csv(users_csv, index=False)
    df_biz.to_csv(biz_csv, index=False)
    df_user_biz.to_csv(rel_user_biz_csv, index=False)
    df_user_user.to_csv(rel_user_user_csv, index=False)

    # Summaries
    u_fraud_rate = df_users["fraud_label"].mean() if "fraud_label" in df_users.columns else 0
    b_fraud_rate = df_biz["fraud_label"].mean() if "fraud_label" in df_biz.columns else 0

    print("===== Summary =====")
    print(f"Users: {len(df_users)} => Fraud ratio: {u_fraud_rate:.2%}")
    print(f"Businesses: {len(df_biz)} => Fraud ratio: {b_fraud_rate:.2%}")
    print("User-User links:", len(df_user_user))
    print("User-Biz links:", len(df_user_biz))
    print("Done! Enjoy your refined synthetic data!")

if __name__ == "__main__":
    main()
