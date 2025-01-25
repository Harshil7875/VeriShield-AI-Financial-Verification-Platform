# verishield_ml_experiments/data_generators/data-gen-v1.py
"""
data-gen-v1.py

Generates synthetic users, businesses, and IPs with multi-pass synergy (user↔biz, user↔IP, ring-based).
Aims to achieve ~50% fraud in each node type (users, businesses, IPs) WITHOUT simply flipping final labels.

Key Idea:
  1) Start with scenario-based "base_fraud" rates for users & businesses (+ synergy logic).
  2) Label users & businesses in a synergy pass, also label IPs based on connected fraudulent users.
  3) Check the resulting fraud ratios. If not near 50%, adjust the base_fraud rates (and/or synergy intensity).
  4) Repeat synergy labeling. Converge until each node type is near 50% fraud (within a small tolerance).
  5) Apply a small random label flip (noise) ~1% (optional) to simulate real-world mislabeling.

Result:
  - The synergy-based labeling is preserved throughout: ring leads, user→biz, user→IP synergy, etc.
  - We do multiple "convergence passes," each time adjusting base rates to nudge the final ratios toward 50%.
  - IP synergy is also iterative: we label IPs after user labeling, then feed that back into the next pass if desired.

Scenarios:
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
DEFAULT_NUM_USERS = 10_000
DEFAULT_NUM_BUSINESSES = 2_000
DEFAULT_NUM_IPS = 2_000
DEFAULT_OUTPUT_DIR = "./data"
MISSING_FIELD_PROB = 0.02        # 2% chance to null out certain fields
RANDOM_LABEL_FLIP_PROB = 0.01    # ~1% chance to flip a label after final pass
NUM_WAVES = 3                    # number of "fraud waves" for user signups

# How many synergy "convergence" passes to attempt (beyond the initial pass):
MAX_CONVERGENCE_PASSES = 10  
TOLERANCE = 0.02  # We'll consider "near 50%" if fraud ratio is in [0.48..0.52]

fake = Faker()

# user segments
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
# 1) SCENARIO PARAMS WITH RANDOM JITTER
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
    r = random.random()
    cumulative = 0.0
    for seg, (prob, _) in USER_SEGMENTS.items():
        cumulative += prob
        if r < cumulative:
            return seg
    return "casual"

###############################################################################
# 2) WAVES FOR USER SIGNUPS
###############################################################################
def create_time_waves(num_users: int, wave_count=3):
    waves = []
    for _ in range(wave_count):
        start_day = random.randint(0, 60)
        length    = random.randint(5, 15)
        end_day   = start_day + length
        fraud_boost = random.uniform(0.1, 0.3)
        waves.append((start_day, end_day, fraud_boost))

    assignments = []
    for _ in range(num_users):
        wave = random.choice(waves)
        day_offset = random.randint(wave[0], wave[1])
        seconds_in_day = random.randint(0, 86400)
        assignments.append((day_offset, seconds_in_day, wave[2]))
    return assignments

###############################################################################
# GENERATE IP NODES
###############################################################################
def generate_ip_nodes(total_ips=2000):
    ip_list = [fake.ipv4_public() for _ in range(total_ips)]
    ip_nodes = pd.DataFrame({
        "ip_id": range(1, total_ips + 1),
        "ip_addr": ip_list
    })
    # We'll store ip_fraud_label later
    ip_nodes["fraud_label"] = 0
    return ip_nodes

###############################################################################
# LINK USERS -> IPS
###############################################################################
def link_users_to_ips(df_users, df_ip, collision_ratio=0.20):
    user_ip_rows = []
    ip_ids = df_ip["ip_id"].tolist()

    num_colliding = int(len(df_users) * collision_ratio)
    repeated_ips = random.sample(ip_ids, k=min(500, len(ip_ids)))

    for i, row in df_users.iterrows():
        user_id = row["user_id"]
        if i < num_colliding:
            chosen_ip = random.choice(repeated_ips)
        else:
            chosen_ip = random.choice(ip_ids)
        user_ip_rows.append({"user_id": user_id, "ip_id": chosen_ip})

    return pd.DataFrame(user_ip_rows)

###############################################################################
# GENERATE USERS
###############################################################################
def generate_unlabeled_users(num_users: int):
    base_start = datetime.now() - timedelta(days=90)
    wave_info = create_time_waves(num_users, wave_count=NUM_WAVES)

    users = []
    for i in range(num_users):
        user_id = i + 1
        day_offset, seconds_in_day, wave_boost = wave_info[i]
        profile = fake.simple_profile()

        cc = fake.country_code()
        prefix_list = COUNTRY_PHONE_PREFIXES.get(cc, [])
        if not prefix_list:
            prefix_list = ["+999", "+000", "555-", fake.msisdn()[:3]]
        prefix = random.choice(prefix_list)
        phone_val = prefix + str(random.randint(1000000, 9999999))

        suspicious_burst = False
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

        users.append(user_dict)

    return pd.DataFrame(users)

###############################################################################
# GENERATE BUSINESSES
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
# USER-USER RELATIONSHIPS (RING LEADERS)
###############################################################################
def create_user_user_relationships(df_users, ring_leader_fraction=0.005):
    df_users["is_ring_leader"] = False
    user_count = len(df_users)
    ring_leader_count = int(user_count * ring_leader_fraction)

    if ring_leader_count < 1:
        return pd.DataFrame(columns=["from_user_id","to_user_id"])

    ring_leader_ids = random.sample(df_users["user_id"].tolist(), ring_leader_count)
    df_users.loc[df_users["user_id"].isin(ring_leader_ids), "is_ring_leader"] = True

    edges = []
    for leader_id in ring_leader_ids:
        link_count = random.randint(5, 15)
        possible_targets = list(set(df_users["user_id"]) - {leader_id})
        link_count = min(link_count, len(possible_targets))
        targets = random.sample(possible_targets, link_count)
        for t in targets:
            edges.append({
                "from_user_id": leader_id,
                "to_user_id": t
            })

    return pd.DataFrame(edges)

###############################################################################
# USER-BUSINESS RELATIONSHIPS
###############################################################################
def link_users_to_businesses(df_users, df_biz, base_ownership_prob=0.4, max_biz_per_user=10):
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
# SAFE FRAUD LABEL FETCH
###############################################################################
def safe_fraud_label(df, user_id_val):
    subset = df.loc[df["user_id"] == user_id_val, "fraud_label"]
    if len(subset) < 1:
        return 0
    val = subset.values[0]
    if val is None or pd.isna(val):
        return 0
    return int(val)

###############################################################################
# LABELING FUNCTIONS
###############################################################################
def label_users(df_users, df_biz, df_user_biz, df_user_user,
                user_base_fraud, user_synergy_factor,
                ip_user_map, user_ip_map):
    """
    Synergy-based user fraud labeling with adjustable user_base_fraud and synergy factor.
    synergy factor scales how strongly ring, IP, and biz adjacency influences p.
    """
    biz_fraud_map = dict(zip(df_biz["business_id"], df_biz["fraud_label"]))
    for k, v in biz_fraud_map.items():
        if v is None: biz_fraud_map[k] = 0

    user_to_biz = df_user_biz.groupby("user_id")["business_id"].apply(list).to_dict()

    # Build adjacency for user->user
    user_graph = {}
    for _, row in df_user_user.iterrows():
        f_u = row["from_user_id"]
        t_u = row["to_user_id"]
        user_graph.setdefault(f_u, []).append(t_u)

    new_labels = []
    for idx, row in df_users.iterrows():
        p = user_base_fraud
        p += row.get("wave_fraud_boost", 0.0)

        seg = row.get("segment", "casual")
        _, seg_mod = USER_SEGMENTS.get(seg, (1.0, 0.0))
        p += seg_mod * user_synergy_factor  # scale by synergy

        # suspicious signals
        email = (row.get("email") or "").lower()
        if any(d in email for d in SUSPICIOUS_EMAIL_DOMAINS):
            p += 0.20 * user_synergy_factor
        phone = str(row.get("phone") or "")
        if len(phone) < 7:
            p += 0.10 * user_synergy_factor
        elif any(x in phone for x in ["+999", "666-666"]):
            p += 0.15 * user_synergy_factor
        if row.get("burst_signup"):
            p += 0.15 * user_synergy_factor
        if row.get("is_ring_leader", False):
            p += 0.30 * user_synergy_factor

        # synergy with fraudulent businesses
        owned_biz_ids = user_to_biz.get(row["user_id"], [])
        known_fraud_biz_count = sum(biz_fraud_map.get(bid, 0) for bid in owned_biz_ids)
        p += 0.05 * known_fraud_biz_count * user_synergy_factor

        # synergy with ring neighbors
        neighbors = user_graph.get(row["user_id"], [])
        ring_fraud_count = 0
        for nb in neighbors:
            ring_fraud_count += safe_fraud_label(df_users, nb)
        p += 0.03 * ring_fraud_count * user_synergy_factor

        # synergy with IP
        if user_ip_map and ip_user_map:
            ip_id = user_ip_map.get(row["user_id"], None)
            if ip_id:
                co_users = ip_user_map.get(ip_id, [])
                co_fraud_count = 0
                for cu in co_users:
                    if cu != row["user_id"]:
                        co_fraud_count += safe_fraud_label(df_users, cu)
                p += 0.025 * co_fraud_count * user_synergy_factor

        label = 1 if random.random() < max(0, min(1, p)) else 0
        new_labels.append(label)

    df_users["fraud_label"] = new_labels
    return df_users

def label_businesses(df_users, df_biz, df_user_biz,
                     biz_base_fraud, biz_synergy_factor):
    user_fraud_map = dict(zip(df_users["user_id"], df_users["fraud_label"]))
    for k, v in user_fraud_map.items():
        if v is None: user_fraud_map[k] = 0

    biz_to_users = df_user_biz.groupby("business_id")["user_id"].apply(list).to_dict()

    new_labels = []
    for idx, row in df_biz.iterrows():
        p = biz_base_fraud

        bname = (row.get("business_name") or "").lower()
        if any(k in bname for k in ["test", "fake", "shell", "phantom", "bogus", "shady"]):
            p += 0.15 * biz_synergy_factor
        reg_ctry = (row.get("registration_country") or "").upper()
        if reg_ctry in WATCHLIST_COUNTRIES:
            p += 0.20 * biz_synergy_factor
        if random.random() < 0.03:
            p += 0.10 * biz_synergy_factor

        owners = biz_to_users.get(row["business_id"], [])
        num_fraud_owners = sum(user_fraud_map.get(uid, 0) for uid in owners)
        p += 0.10 * num_fraud_owners * biz_synergy_factor

        label = 1 if random.random() < max(0, min(1, p)) else 0
        new_labels.append(label)

    df_biz["fraud_label"] = new_labels
    return df_biz

def label_ips(df_ip, df_users, ip_user_map, ip_base_fraud, ip_synergy_factor):
    """
    Label IPs: if many connected users are fraud, IP is more likely fraud.
    """
    new_labels = []
    for i, row in df_ip.iterrows():
        ip_id_val = row["ip_id"]
        connected_users = ip_user_map.get(ip_id_val, [])
        # start with some base for IP
        p = ip_base_fraud

        if connected_users:
            # fraction of fraud among connected users
            fraud_count = 0
            for uid in connected_users:
                sub = df_users.loc[df_users["user_id"] == uid, "fraud_label"]
                if len(sub) > 0 and sub.values[0] == 1:
                    fraud_count += 1
            ratio = fraud_count / len(connected_users)
            p += ratio * ip_synergy_factor  # synergy effect
        else:
            # no connected users => minimal chance
            p += 0.01

        label = 1 if random.random() < max(0, min(1, p)) else 0
        new_labels.append(label)

    df_ip["fraud_label"] = new_labels
    return df_ip

###############################################################################
# ENRICH USER FEATURES
###############################################################################
def enrich_user_features(df_users, df_user_biz, df_biz):
    df_users["email_domain"] = df_users["email"].apply(
        lambda x: x.split('@')[-1] if x and '@' in str(x) else "missing"
    )
    ip_counts = df_users.groupby("device_id")["user_id"].transform("count")
    df_users["ip_count"] = ip_counts

    df_merged = df_user_biz.merge(
        df_biz[["business_id", "fraud_label"]],
        on="business_id", how="left"
    )
    df_merged["fraud_label"] = df_merged["fraud_label"].fillna(0)

    fc = df_merged.groupby("user_id")["fraud_label"].sum().reset_index(name="num_fraud_biz_owned")
    df_users = df_users.merge(fc, on="user_id", how="left")
    df_users["num_fraud_biz_owned"] = df_users["num_fraud_biz_owned"].fillna(0)
    return df_users

###############################################################################
# CONVERGENCE LOOP
###############################################################################
def measure_fraud_ratio(df, label_col="fraud_label"):
    return df[label_col].mean()

def in_range(val, target=0.50, tol=TOLERANCE):
    return (val >= target - tol) and (val <= target + tol)

def convergence_pass(
    df_users, df_biz, df_ip,
    df_user_biz, df_user_user, ip_user_map, user_ip_map,
    user_base_fraud, biz_base_fraud, ip_base_fraud,
    user_synergy, biz_synergy, ip_synergy
):
    """
    Single synergy labeling pass for users, businesses, IPs.
    Returns updated dataframes + measured fraud ratios.
    """
    # Label users & businesses in synergy
    df_users = label_users(
        df_users, df_biz, df_user_biz, df_user_user,
        user_base_fraud, user_synergy, ip_user_map, user_ip_map
    )
    df_biz = label_businesses(
        df_users, df_biz, df_user_biz,
        biz_base_fraud, biz_synergy
    )
    # Then label IPs after user labels
    df_ip = label_ips(
        df_ip, df_users, ip_user_map,
        ip_base_fraud, ip_synergy
    )

    # measure
    user_ratio = measure_fraud_ratio(df_users)
    biz_ratio  = measure_fraud_ratio(df_biz)
    ip_ratio   = measure_fraud_ratio(df_ip)
    return df_users, df_biz, df_ip, user_ratio, biz_ratio, ip_ratio

def adjust_base_rate(current_ratio, base_rate, synergy_factor):
    """
    If current_ratio > 0.5 + tol => decrease base_rate slightly
    If current_ratio < 0.5 - tol => increase base_rate slightly
    synergy_factor can also be tweaked, but let's keep it stable or do small nudge
    """
    target = 0.50
    if current_ratio > target + TOLERANCE:
        # too high => reduce base
        base_rate *= 0.95  # small decrement
    elif current_ratio < target - TOLERANCE:
        # too low => increase base
        base_rate *= 1.05
    return max(0, min(1, base_rate))

###############################################################################
# MAIN
###############################################################################
def main():
    parser = argparse.ArgumentParser(description="data-gen-v1 generator, converging near 50% fraud per node type.")
    parser.add_argument("--num-users", type=int, default=DEFAULT_NUM_USERS)
    parser.add_argument("--num-businesses", type=int, default=DEFAULT_NUM_BUSINESSES)
    parser.add_argument("--num-ips", type=int, default=DEFAULT_NUM_IPS)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--scenario", type=str, default="default",
                        choices=list(SCENARIO_CONFIG.keys()))
    parser.add_argument("--output-dir", type=str, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)
        Faker.seed(args.seed)
        np.random.seed(args.seed)
        print(f"[INFO] Seed set to {args.seed}")

    scenario_name = args.scenario
    scenario_params = get_scenario_params(scenario_name)

    user_base_fraud = scenario_params["user_base_fraud"]
    biz_base_fraud  = scenario_params["biz_base_fraud"]
    ip_base_fraud   = 0.10  # A starting guess for IP base fraud

    # synergy factors for each node type
    user_synergy = 1.0
    biz_synergy  = 1.0
    ip_synergy   = 1.0

    print("===== Data Generation (Synergy + Convergence) =====")
    print(f"Scenario: {scenario_name}")
    print(f"num_users={args.num_users}, num_businesses={args.num_businesses}, num_ips={args.num_ips}")
    print(f"Initial user_base_fraud={user_base_fraud:.3f}, biz_base_fraud={biz_base_fraud:.3f}, ip_base_fraud={ip_base_fraud:.3f}")

    # 1) Generate unlabeled users, businesses
    df_users = generate_unlabeled_users(args.num_users)
    df_biz   = generate_unlabeled_businesses(args.num_businesses)

    # 2) Generate IPs + user->ip edges
    df_ip = generate_ip_nodes(args.num_ips)
    df_user_ip = link_users_to_ips(df_users, df_ip, collision_ratio=0.20)

    # 3) user->user ring relationships
    df_user_user = create_user_user_relationships(df_users, ring_leader_fraction=0.005)

    # 4) user->biz relationships
    df_user_biz = link_users_to_businesses(df_users, df_biz, base_ownership_prob=0.40)

    # adjacency maps
    ip_user_map = df_user_ip.groupby("ip_id")["user_id"].apply(list).to_dict()
    user_ip_map = dict(zip(df_user_ip["user_id"], df_user_ip["ip_id"]))

    # 5) Convergence Loop
    print("\n--- Starting synergy convergence loop ---")
    converged = False
    for pass_idx in range(MAX_CONVERGENCE_PASSES):
        # do synergy pass
        df_users, df_biz, df_ip, ur, br, ir = convergence_pass(
            df_users, df_biz, df_ip,
            df_user_biz, df_user_user, ip_user_map, user_ip_map,
            user_base_fraud, biz_base_fraud, ip_base_fraud,
            user_synergy, biz_synergy, ip_synergy
        )
        print(f"Pass {pass_idx+1}: user_fraud={ur:.3f}, biz_fraud={br:.3f}, ip_fraud={ir:.3f}")

        # check if all are near 50%
        if in_range(ur) and in_range(br) and in_range(ir):
            converged = True
            print(f"[INFO] Converged near 50% after pass {pass_idx+1}.")
            break

        # adjust base rates if needed
        user_base_fraud = adjust_base_rate(ur, user_base_fraud, user_synergy)
        biz_base_fraud  = adjust_base_rate(br, biz_base_fraud, biz_synergy)
        ip_base_fraud   = adjust_base_rate(ir, ip_base_fraud, ip_synergy)

    if not converged:
        # do one last pass with final rates
        df_users, df_biz, df_ip, ur, br, ir = convergence_pass(
            df_users, df_biz, df_ip,
            df_user_biz, df_user_user, ip_user_map, user_ip_map,
            user_base_fraud, biz_base_fraud, ip_base_fraud,
            user_synergy, biz_synergy, ip_synergy
        )
        print(f"[WARN] Reached max passes. Final ~fraud: user={ur:.3f}, biz={br:.3f}, ip={ir:.3f}")

    # 6) Optional random label flip
    flips_u = flips_b = flips_ip = 0
    for i, row in df_users.iterrows():
        if random.random() < RANDOM_LABEL_FLIP_PROB:
            df_users.at[i, "fraud_label"] = 1 - (row["fraud_label"] or 0)
            flips_u += 1
    for i, row in df_biz.iterrows():
        if random.random() < RANDOM_LABEL_FLIP_PROB:
            df_biz.at[i, "fraud_label"] = 1 - (row["fraud_label"] or 0)
            flips_b += 1
    for i, row in df_ip.iterrows():
        if random.random() < RANDOM_LABEL_FLIP_PROB:
            df_ip.at[i, "fraud_label"] = 1 - (row["fraud_label"] or 0)
            flips_ip += 1

    if flips_u or flips_b or flips_ip:
        print(f"[INFO] Noise flips => user={flips_u}, biz={flips_b}, ip={flips_ip} flips")

    # 7) Enrich user features
    df_users = enrich_user_features(df_users, df_user_biz, df_biz)

    # 8) Save final CSVs
    scenario_dir = os.path.join(args.output_dir, scenario_name)
    os.makedirs(scenario_dir, exist_ok=True)
    print(f"-> Saving CSVs to {scenario_dir}")

    df_users.to_csv(os.path.join(scenario_dir, "synthetic_users.csv"), index=False)
    df_biz.to_csv(os.path.join(scenario_dir, "synthetic_businesses.csv"), index=False)
    df_ip.to_csv(os.path.join(scenario_dir, "ip_nodes.csv"), index=False)
    df_user_ip.to_csv(os.path.join(scenario_dir, "user_ip_relationships.csv"), index=False)
    df_user_user.to_csv(os.path.join(scenario_dir, "user_user_relationships.csv"), index=False)
    df_user_biz.to_csv(os.path.join(scenario_dir, "user_business_relationships.csv"), index=False)

    # 9) Final summary
    ur = measure_fraud_ratio(df_users)
    br = measure_fraud_ratio(df_biz)
    ir = measure_fraud_ratio(df_ip)
    print("\n===== Final Summary =====")
    print(f"Users:      {len(df_users):,d} => Fraud ratio: {ur:.2%}")
    print(f"Businesses: {len(df_biz):,d} => Fraud ratio: {br:.2%}")
    print(f"IPs:        {len(df_ip):,d} => Fraud ratio: {ir:.2%}")
    print("User->IP edges:", len(df_user_ip))
    print("User->User edges:", len(df_user_user))
    print("User->Biz edges:", len(df_user_biz))
    print("Done! Real synergy preserved, approximate 50% distribution via iterative convergence.")


if __name__ == "__main__":
    main()
