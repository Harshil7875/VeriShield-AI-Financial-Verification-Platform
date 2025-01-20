#!/usr/bin/env python3
"""
refined_data_generator_extended.py

A robust extension that:
  1) Randomizes scenario fraud rates each run (small variations)
  2) Adds time-based "waves" for user signups (fraud bursts)
  3) Creates IP nodes & user->IP edges
  4) Applies second-degree synergy in multi-pass labeling
  5) Injects random label flips (noise) to simulate real-world ambiguity

Existing scenarios:
  - low_fraud, default, high_fraud, ultra_low_fraud, medium_fraud, extreme_fraud
"""

import os
import random
import argparse
import pandas as pd
from faker import Faker
from datetime import timedelta, datetime
import numpy as np

###############################################################################
# GLOBAL DEFAULTS & CONFIG
###############################################################################
DEFAULT_NUM_USERS = 100_000
DEFAULT_NUM_BUSINESSES = 10_000
DEFAULT_NUM_IPS = 5000            # how many unique IP nodes to generate
DEFAULT_OUTPUT_DIR = "./data"
MISSING_FIELD_PROB = 0.02         # 2% chance to null out certain fields
RANDOM_LABEL_FLIP_PROB = 0.01     # ~1% chance to flip a label after final pass
NUM_WAVES = 3                     # number of "fraud waves" for user signups

fake = Faker()

# user segments as before
USER_SEGMENTS = {
    "casual":     (0.70, 0.0),
    "smb_owner":  (0.20, 0.05),
    "enterprise": (0.09, -0.05),
    "money_mule": (0.01, 0.40),
}

# base scenario config
SCENARIO_CONFIG = {
    "low_fraud":       {"user_base_fraud": 0.05, "biz_base_fraud": 0.05},
    "default":         {"user_base_fraud": 0.15, "biz_base_fraud": 0.10},
    "high_fraud":      {"user_base_fraud": 0.30, "biz_base_fraud": 0.25},
    "ultra_low_fraud": {"user_base_fraud": 0.02, "biz_base_fraud": 0.02},
    "medium_fraud":    {"user_base_fraud": 0.20, "biz_base_fraud": 0.15},
    "extreme_fraud":   {"user_base_fraud": 0.40, "biz_base_fraud": 0.35},
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
# 1) DYNAMIC SCENARIO PARAM RETRIEVAL
###############################################################################
def get_scenario_params(scenario_name: str):
    """Adds small random jitter (+/- 5%) to the base fraud rates each run."""
    base = SCENARIO_CONFIG.get(scenario_name, SCENARIO_CONFIG["default"])
    base_uf = base["user_base_fraud"]
    base_bf = base["biz_base_fraud"]

    scale_user = random.uniform(0.95, 1.05)
    scale_biz  = random.uniform(0.95, 1.05)

    return {
        "user_base_fraud": base_uf * scale_user,
        "biz_base_fraud":  base_bf * scale_biz
    }

###############################################################################
# PICK SEGMENT FOR USERS
###############################################################################
def pick_user_segment() -> str:
    """Randomly selects a user segment (casual, smb_owner, enterprise, money_mule)."""
    r = random.random()
    cumulative = 0.0
    for seg, (prob, _) in USER_SEGMENTS.items():
        cumulative += prob
        if r < cumulative:
            return seg
    return "casual"  # fallback

###############################################################################
# 2) WAVES FOR USER SIGNUPS
###############################################################################
def create_time_waves(num_users: int, wave_count=3):
    """
    Assign each user to a "wave," giving them a day offset + second offset,
    plus a wave_fraud_boost factor to amplify base fraud in that wave.
    """
    waves = []
    for _ in range(wave_count):
        start_day = random.randint(0, 60)            # wave starts within first 60 days
        length    = random.randint(5, 15)           # wave length 5..15 days
        end_day   = start_day + length
        fraud_boost = random.uniform(0.1, 0.3)      # each wave adds +0.1..0.3 to user fraud
        waves.append((start_day, end_day, fraud_boost))

    assignments = []
    for _ in range(num_users):
        wave = random.choice(waves)
        day_offset = random.randint(wave[0], wave[1])
        seconds_in_day = random.randint(0, 86400)
        assignments.append((day_offset, seconds_in_day, wave[2]))
    return assignments

###############################################################################
# 3) IP NODE GENERATION
###############################################################################
def generate_ip_nodes(total_ips=5000):
    """
    Create a DF of IP nodes. We'll store: ip_id, ip_addr.
    """
    ip_list = [fake.ipv4_public() for _ in range(total_ips)]
    ip_nodes = pd.DataFrame({
        "ip_id": range(1, total_ips+1),
        "ip_addr": ip_list
    })
    return ip_nodes

def link_users_to_ips(df_users, df_ip, collision_ratio=0.20):
    """
    Creates user->ip relationships. We'll pick random IPs from df_ip.
    Also enforce partial collisions if desired. 
    """
    user_ip_rows = []
    ip_ids = df_ip["ip_id"].tolist()

    # number of users that share IP collisions
    # (similar to old collision_map approach, but now via IP nodes)
    num_colliding = int(len(df_users) * collision_ratio)
    repeated_ips = random.sample(ip_ids, k=min(500, len(ip_ids)))  # pool for collisions

    for i, row in df_users.iterrows():
        user_id = row["user_id"]
        if i < num_colliding:
            # choose from collision IP pool
            chosen_ip = random.choice(repeated_ips)
        else:
            # pick randomly from entire IP set
            chosen_ip = random.choice(ip_ids)

        user_ip_rows.append({
            "user_id": user_id,
            "ip_id": chosen_ip
        })

    return pd.DataFrame(user_ip_rows)

###############################################################################
# (A) GENERATE UNLABELED USERS (UPDATED FOR WAVES)
###############################################################################
def generate_unlabeled_users(num_users: int):
    """
    Now we incorporate 'wave_fraud_boost' from time waves, storing them in user records.
    """
    base_start = datetime.now() - timedelta(days=90)
    wave_info = create_time_waves(num_users, wave_count=NUM_WAVES)

    users = []
    for i in range(num_users):
        user_id = i + 1
        day_offset, seconds_in_day, wave_boost = wave_info[i]
        user_dict = _create_base_user_record(user_id, base_start, day_offset, seconds_in_day, wave_boost)
        users.append(user_dict)

    return pd.DataFrame(users)

def _create_base_user_record(user_id: int, base_start: datetime, day_offset: int, seconds_in_day: int, wave_boost: float):
    profile = fake.simple_profile()

    # phone logic
    cc = fake.country_code()
    prefix_list = COUNTRY_PHONE_PREFIXES.get(cc, [])
    if not prefix_list:
        prefix_list = ["+999", "+000", "555-", fake.msisdn()[:3]]
    prefix = random.choice(prefix_list)
    phone_val = prefix + str(random.randint(1000000, 9999999))

    # decide if user is part of a "suspicious_burst"
    suspicious_burst = False
    # 5% chance we shorten the daily second range
    if random.random() < 0.05:
        suspicious_burst = True
        seconds_in_day = random.randint(0, 60)

    created_dt = base_start + timedelta(days=day_offset, seconds=seconds_in_day)

    seg = pick_user_segment()
    user_dict = {
        "user_id": user_id,
        "segment": seg,
        "name": profile["name"],
        "email": profile["mail"],
        "username": profile["username"],
        "birthdate": profile["birthdate"].isoformat() if profile["birthdate"] else None,
        "gender": profile["sex"],
        # store wave_boost so labeling can incorporate it
        "wave_fraud_boost": wave_boost,
        "device_id": fake.lexify(text="device_????????"),
        "phone": phone_val,
        "country_code": cc,
        "created_at": created_dt,
        "burst_signup": suspicious_burst,
        "fraud_label": None,
    }

    # random missing fields
    for f in ["name", "email", "phone", "country_code"]:
        if random.random() < MISSING_FIELD_PROB:
            user_dict[f] = None

    return user_dict

###############################################################################
# (B) GENERATE UNLABELED BUSINESSES
###############################################################################
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
# USER-USER RELATIONSHIPS
###############################################################################
def create_user_user_relationships(df_users: pd.DataFrame, ring_leader_fraction=0.005) -> pd.DataFrame:
    df_users["is_ring_leader"] = False
    user_count = len(df_users)
    ring_leader_count = int(user_count * ring_leader_fraction)

    if ring_leader_count < 1:
        return pd.DataFrame(columns=["from_user_id","to_user_id"])  # edge case

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
# USER-BUSINESS RELATIONSHIPS
###############################################################################
def link_users_to_businesses(df_users: pd.DataFrame, df_biz: pd.DataFrame,
                            base_ownership_prob=0.4, max_biz_per_user=10) -> pd.DataFrame:
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
# HELPER: SAFE FRAUD LABEL FETCH
###############################################################################
def safe_fraud_label(df_users, user_id_val: int) -> int:
    """
    Retrieves the 'fraud_label' for a given user_id from df_users, 
    returning 0 if not found or if it is None/NaN.
    """
    subset = df_users.loc[df_users["user_id"] == user_id_val, "fraud_label"]
    if len(subset) < 1:
        return 0
    val = subset.values[0]
    if val is None or pd.isna(val):
        return 0
    return int(val)

###############################################################################
# MULTI-PASS LABEL ASSIGNMENT (UPDATED FOR 2ND-DEGREE SYNERGY)
###############################################################################
def assign_fraud_labels_users(
    df_users: pd.DataFrame,
    df_biz: pd.DataFrame,
    df_user_biz: pd.DataFrame,
    df_user_user: pd.DataFrame,
    scenario_params: dict,
    iteration=1,
    user_ip_map=None,
    ip_user_map=None
):
    user_base_fraud = scenario_params["user_base_fraud"]
    biz_fraud_map = dict(zip(df_biz["business_id"], df_biz["fraud_label"]))
    # fill None with 0
    for k, v in biz_fraud_map.items():
        if v is None:
            biz_fraud_map[k] = 0

    # user->biz adjacency
    user_to_biz = df_user_biz.groupby("user_id")["business_id"].apply(list).to_dict()

    # user->user adjacency
    user_graph = {}
    for idx, row in df_user_user.iterrows():
        f_u = row["from_user_id"]
        t_u = row["to_user_id"]
        user_graph.setdefault(f_u, []).append(t_u)

    new_labels = []
    for idx, row in df_users.iterrows():
        # base + wave
        p = user_base_fraud
        p += row.get("wave_fraud_boost", 0.0)

        seg = row.get("segment", "casual")
        _, seg_fraud_mod = USER_SEGMENTS.get(seg, (1.0, 0.0))
        p += seg_fraud_mod

        # suspicious signals
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

        # direct owned businesses
        owned_biz_ids = user_to_biz.get(row["user_id"], [])
        known_fraud_biz_count = sum(biz_fraud_map.get(bid, 0) for bid in owned_biz_ids)
        p += 0.05 * known_fraud_biz_count

        # ring-based second-degree synergy
        neighbors = user_graph.get(row["user_id"], [])
        neighbor_fraud_count = 0
        for nb in neighbors:
            neighbor_fraud_count += safe_fraud_label(df_users, nb)
        p += 0.03 * neighbor_fraud_count

        # IP-based synergy
        if user_ip_map:
            ip_id = user_ip_map.get(row["user_id"], None)
            if ip_id and ip_user_map:
                co_users = ip_user_map.get(ip_id, [])
                co_fraud_count = 0
                for cu in co_users:
                    if cu != row["user_id"]:
                        co_fraud_count += safe_fraud_label(df_users, cu)
                p += 0.025 * co_fraud_count

        label = 1 if random.random() < max(0, p) else 0

        # forced overrides
        if label == 0 and p < 0.2 and random.random() < 0.02:
            label = 1
        if label == 1 and p > 0.4 and random.random() < 0.02:
            label = 0

        new_labels.append(label)

    df_users["fraud_label"] = new_labels
    return df_users

def assign_fraud_labels_businesses(
    df_users: pd.DataFrame,
    df_biz: pd.DataFrame,
    df_user_biz: pd.DataFrame,
    scenario_params: dict,
    iteration=1
):
    biz_base_fraud = scenario_params["biz_base_fraud"]
    user_fraud_map = dict(zip(df_users["user_id"], df_users["fraud_label"]))
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

        # random offset
        if random.random() < 0.03:
            p += 0.10

        owners = biz_to_users.get(row["business_id"], [])
        num_fraud_owners = sum(user_fraud_map.get(uid, 0) for uid in owners)
        p += 0.10 * num_fraud_owners

        label = 1 if random.random() < max(0, p) else 0

        # forced overrides
        if label == 0 and p < 0.2 and random.random() < 0.02:
            label = 1
        if label == 1 and p > 0.4 and random.random() < 0.02:
            label = 0

        new_labels.append(label)

    df_biz["fraud_label"] = new_labels
    return df_biz

###############################################################################
# FEATURE ENRICHMENT
###############################################################################
def enrich_user_features(df_users, df_user_biz, df_biz):
    df_users["email_domain"] = df_users["email"].apply(
        lambda x: x.split('@')[-1] if x and '@' in str(x) else "missing"
    )
    ip_counts = df_users.groupby("device_id")["user_id"].transform("count")
    df_users["ip_count"] = ip_counts  # or revert to signup_ip if desired

    # # of fraud businesses owned
    df_merged = df_user_biz.merge(
        df_biz[["business_id", "fraud_label"]],
        on="business_id", how="left"
    )
    df_merged["fraud_label"] = df_merged["fraud_label"].fillna(0)

    fraud_count = df_merged.groupby("user_id")["fraud_label"].sum().reset_index(name="num_fraud_biz_owned")
    df_users = df_users.merge(fraud_count, on="user_id", how="left")
    df_users["num_fraud_biz_owned"] = df_users["num_fraud_biz_owned"].fillna(0)
    return df_users

###############################################################################
# MAIN
###############################################################################
def main():
    parser = argparse.ArgumentParser(description="Extended multi-pass data generator for VeriShield (robust).")
    parser.add_argument("--num-users", type=int, default=DEFAULT_NUM_USERS)
    parser.add_argument("--num-businesses", type=int, default=DEFAULT_NUM_BUSINESSES)
    parser.add_argument("--num-ips", type=int, default=DEFAULT_NUM_IPS,
                        help="Number of unique IP nodes to generate.")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--scenario", type=str, default="default",
                        choices=[
                            "default", "low_fraud", "high_fraud",
                            "ultra_low_fraud", "medium_fraud", "extreme_fraud"
                        ])
    parser.add_argument("--iterations", type=int, default=1)
    parser.add_argument("--output-dir", type=str, default=DEFAULT_OUTPUT_DIR,
                        help="Parent directory to store scenario subfolders. Default=./data")
    args = parser.parse_args()

    # Optional: set random seed
    if args.seed is not None:
        random.seed(args.seed)
        Faker.seed(args.seed)
        print(f"[INFO] Seed set to {args.seed}")

    # scenario param with small random jitter
    scenario_name = args.scenario
    scenario_params = get_scenario_params(scenario_name)

    print(f"===== Refined Data Generation (Scenario: {scenario_name}) =====")
    print(f"Users: {args.num_users}, Businesses: {args.num_businesses}, IPs: {args.num_ips}")
    print(f"Base user fraud (jittered): {scenario_params['user_base_fraud']:.3f} | "
          f"Biz base fraud (jittered): {scenario_params['biz_base_fraud']:.3f}")
    print(f"Label Assignment Iterations: {args.iterations}")

    # 1) Generate unlabeled users & businesses
    print("-> Generating unlabeled users & businesses...")
    df_users = generate_unlabeled_users(args.num_users)
    df_biz   = generate_unlabeled_businesses(args.num_businesses)

    # 2) Generate IP nodes & link users -> IP
    df_ip = generate_ip_nodes(args.num_ips)
    df_user_ip = link_users_to_ips(df_users, df_ip, collision_ratio=0.20)
    print(f"[INFO] Created {len(df_ip)} IP nodes.")
    print(f"[INFO] Created {len(df_user_ip)} user->IP relationships.")

    # 3) user-user ring relationships
    df_user_user = create_user_user_relationships(df_users, ring_leader_fraction=0.005)
    print(f"[INFO] Created {len(df_user_user)} user-user relationships.")

    # 4) user-biz relationships
    df_user_biz = link_users_to_businesses(df_users, df_biz,
                                           base_ownership_prob=0.40,
                                           max_biz_per_user=10)
    print(f"[INFO] Created {len(df_user_biz)} user-business relationships.")

    # Build easy in-memory maps for second-degree synergy
    ip_user_map = df_user_ip.groupby("ip_id")["user_id"].apply(list).to_dict()
    user_ip_map = dict(zip(df_user_ip["user_id"], df_user_ip["ip_id"]))

    # 5) Multi-pass labeling
    for i in range(args.iterations):
        print(f"-> Labeling pass {i+1} of {args.iterations}...")
        # users
        df_users = assign_fraud_labels_users(
            df_users=df_users,
            df_biz=df_biz,
            df_user_biz=df_user_biz,
            df_user_user=df_user_user,
            scenario_params=scenario_params,
            iteration=i+1,
            user_ip_map=user_ip_map,
            ip_user_map=ip_user_map
        )
        # businesses
        df_biz = assign_fraud_labels_businesses(
            df_users=df_users,
            df_biz=df_biz,
            df_user_biz=df_user_biz,
            scenario_params=scenario_params,
            iteration=i+1
        )

    # 6) Anomaly injection / label flips
    flips_u = 0
    for i, row in df_users.iterrows():
        if random.random() < RANDOM_LABEL_FLIP_PROB:
            df_users.at[i, "fraud_label"] = 1 - (row["fraud_label"] or 0)
            flips_u += 1
    flips_b = 0
    for i, row in df_biz.iterrows():
        if random.random() < RANDOM_LABEL_FLIP_PROB:
            df_biz.at[i, "fraud_label"] = 1 - (row["fraud_label"] or 0)
            flips_b += 1

    if flips_u or flips_b:
        print(f"[INFO] Performed {flips_u} user-label flips and {flips_b} biz-label flips for noise injection.")

    # 7) Enrichment
    df_users = enrich_user_features(df_users, df_user_biz, df_biz)

    scenario_dir = os.path.join(args.output_dir, scenario_name)
    os.makedirs(scenario_dir, exist_ok=True)
    print(f"-> CSV outputs will be saved to: {scenario_dir}")

    # Write CSV files
    users_csv   = os.path.join(scenario_dir, "synthetic_users.csv")
    biz_csv     = os.path.join(scenario_dir, "synthetic_businesses.csv")
    ip_csv      = os.path.join(scenario_dir, "ip_nodes.csv")
    rel_ui_csv  = os.path.join(scenario_dir, "user_ip_relationships.csv")
    rel_ub_csv  = os.path.join(scenario_dir, "user_business_relationships.csv")
    rel_uu_csv  = os.path.join(scenario_dir, "user_user_relationships.csv")

    df_users.to_csv(users_csv, index=False)
    df_biz.to_csv(biz_csv, index=False)
    df_ip.to_csv(ip_csv, index=False)
    df_user_ip.to_csv(rel_ui_csv, index=False)
    df_user_biz.to_csv(rel_ub_csv, index=False)
    df_user_user.to_csv(rel_uu_csv, index=False)

    # Summaries
    u_fraud_rate = df_users["fraud_label"].mean() if "fraud_label" in df_users.columns else 0
    b_fraud_rate = df_biz["fraud_label"].mean() if "fraud_label" in df_biz.columns else 0

    print("===== Summary =====")
    print(f"Users: {len(df_users)} => Fraud ratio: {u_fraud_rate:.2%}")
    print(f"Businesses: {len(df_biz)} => Fraud ratio: {b_fraud_rate:.2%}")
    print(f"IP Nodes: {len(df_ip)}")
    print("User->IP links:", len(df_user_ip))
    print("User->User links:", len(df_user_user))
    print("User->Biz links:", len(df_user_biz))
    print("Done! Enjoy your robust synthetic data with new scenario expansions!")


if __name__ == "__main__":
    main()
