#!/usr/bin/env python3
"""
full_data_generator.py

Generates synthetic user data, business data, assigns fraud labels,
and creates user-business relationships with enhanced realism:

  - Time-based patterns (bursts of signups in short windows).
  - Multiple user segments (each with different base fraud rates).
  - Rare 'sophisticated' fraud that looks legit but is labeled fraudulent.
  - Occasional 'false flags' where suspicious signals appear on legit users.
  - Optionally simulates multiple 'scenarios' (e.g., low-fraud or high-fraud).
  - Feature enrichment steps:
       * 'email_domain' for each user
       * 'ip_count' = how many users share the same IP
       * 'num_fraud_biz_owned' = how many fraudulent businesses each user owns
       * Additional phone vs. country correlations

Usage:
    python full_data_generator.py --num-users 1500000 --num-businesses 150000 --seed 123 --scenario high_fraud

Default arguments:
    NUM_USERS = 1,500,000
    NUM_BUSINESSES = 150,000
    SEED is None (fully random).
    SCENARIO is "default" if not specified.
"""

import random
import argparse
import pandas as pd
from faker import Faker
from datetime import timedelta, datetime

###############################################################################
# GLOBAL DEFAULTS & CONFIG
###############################################################################
DEFAULT_NUM_USERS = 1_500_000
DEFAULT_NUM_BUSINESSES = 150_000
MISSING_FIELD_PROB = 0.02  # 2% chance to null out certain fields
fake = Faker()

# Suspicious email domains (expandable)
ADDITIONAL_SUSP_DOMAINS = [
    "@throwaway.io",
    "@spamgourmet.com",
    "@sharklasers.com",
    "@guerrillamail.com",
    "@maildrop.cc"
]
SUSPICIOUS_EMAIL_DOMAINS = [
    "@tempmail.xyz",
    "@disposable.com",
    "@fakemail.com"
] + ADDITIONAL_SUSP_DOMAINS

# Example scenario-based baseline fraud rates:
SCENARIO_CONFIG = {
    "low_fraud":  {"user_base_fraud": 0.05, "biz_base_fraud": 0.05},
    "high_fraud": {"user_base_fraud": 0.30, "biz_base_fraud": 0.25},
    "default":    {"user_base_fraud": 0.15, "biz_base_fraud": 0.10},
}

# Provide some phone country correlations
COUNTRY_PHONE_PREFIXES = {
    "US": ["+1", "+000", "+999"],      # US often has +1, but we inject suspicious prefixes too
    "GB": ["+44", "+999", "+000"],
    "DE": ["+49", "+999"],
    "AU": ["+61", "+999"],
    # More can be added or randomized
}

###############################################################################
# CORE FRAUD LOGIC
###############################################################################

def assign_user_label(user_dict: dict, scenario_params: dict) -> int:
    """
    Assigns a binary fraud label (0=legit, 1=fraud) using layered heuristics.
    Allows scenario-based 'base_fraud' adjustments.
    Also introduces rare 'sophisticated' fraud and 'false flags'.
    """
    base_fraud = scenario_params.get("user_base_fraud", 0.15)

    # Start with a scenario-based base probability
    p = base_fraud

    # Basic signals
    email = (user_dict.get("email") or "").lower()
    if any(domain in email for domain in SUSPICIOUS_EMAIL_DOMAINS):
        p += 0.20

    phone = (user_dict.get("phone") or "")
    if len(phone) < 7:
        p += 0.10
    elif any(prefix in phone for prefix in ["+999", "666-666"]):
        p += 0.15

    signup_ip = (user_dict.get("signup_ip") or "")
    if signup_ip.startswith("192.168") or signup_ip.startswith("10."):
        p += 0.10

    # Time-based suspicious burst? If created_at is in an extremely narrow window, +X
    if user_dict.get("burst_signup", False):
        p += 0.15

    # Rare small additive factor
    if random.random() < 0.02:
        p += 0.05

    # Rare big red flag
    if random.random() < 0.01:
        p += 0.25

    # Introduce 'sophisticated' fraud cases: Looks legit, but is fraud
    # e.g., 1-2% of the total might have no typical signals but be forced to label=1
    # We'll do this only if p < 0.2 => meaning not many suspicious indicators
    if p < 0.2 and random.random() < 0.02:
        return 1  # forcibly mark as sophisticated fraud

    # Introduce 'false flag': user might have suspicious signals but is still legit
    # We give a ~2% chance to forcibly set label=0 if p > 0.4
    if p > 0.4 and random.random() < 0.02:
        return 0

    return 1 if random.random() < p else 0


def assign_business_label(business_dict: dict, scenario_params: dict) -> int:
    """
    Similar approach for businesses. 
    Scenario-based base fraud, plus heuristics.
    """
    base_fraud = scenario_params.get("biz_base_fraud", 0.10)
    p = base_fraud

    name = (business_dict.get("business_name") or "").lower()
    if any(kw in name for kw in ["test", "fake", "shell", "phantom", "bogus", "shady"]):
        p += 0.15

    watchlist_countries = ["NK", "IR", "SY", "CU", "AF", "SO", "LY"]
    reg_country = (business_dict.get("registration_country") or "").upper()
    if reg_country in watchlist_countries:
        p += 0.20

    # If incorporation_date is very recent => suspicious
    if random.random() < 0.03:
        p += 0.10

    # Rare forced 'sophisticated' biz fraud with normal signals
    if p < 0.2 and random.random() < 0.02:
        return 1

    # Rare 'false flag' scenario
    if p > 0.4 and random.random() < 0.02:
        return 0

    return 1 if random.random() < p else 0

###############################################################################
# IP & DEVICE LOGIC
###############################################################################

def generate_ip_pool(total_users: int, collision_ratio: float = 0.20):
    """
    Creates repeated IP addresses for ~collision_ratio fraction of users.
    We'll also produce a small fraction that share both IP & device for
    advanced collisions.
    """
    num_repeated_ips = int(total_users * collision_ratio)
    collision_ips = [fake.ipv4_public() for _ in range(500)]

    collision_mapping = {}
    for i in range(num_repeated_ips):
        ip_choice = random.choice(collision_ips)
        collision_mapping[i + 1] = {
            "ip": ip_choice,
            "device_id": fake.lexify(text="device_????????")  # Some random device ID
        }
    return collision_mapping

###############################################################################
# USER GENERATION
###############################################################################

def generate_user_data(user_id: int, collision_map: dict, scenario_params: dict, base_start: datetime) -> dict:
    """
    If user_id is in collision_map, reuse IP + device_id. Otherwise random new.
    Include time-based burst logic & multi-segment phone correlation.
    """
    profile = fake.simple_profile()
    collision_entry = collision_map.get(user_id)

    if collision_entry:
        signup_ip = collision_entry["ip"]
        device_id = collision_entry["device_id"]
    else:
        signup_ip = fake.ipv4_public()
        device_id = fake.lexify(text="device_????????")

    # Possibly correlate phone prefix with country_code
    # If no match, fallback to suspicious or random phone
    country_code = fake.country_code()  # e.g. 'US', 'GB', 'DE'
    possible_prefixes = COUNTRY_PHONE_PREFIXES.get(country_code, [])
    if not possible_prefixes:
        # fallback
        possible_prefixes = [
            fake.msisdn()[:3],  # random chunk
            "+999", "+000", "666-666"
        ]
    prefix_choice = random.choice(possible_prefixes)
    phone_chosen = prefix_choice + str(random.randint(1000000, 9999999))  # simplistic append

    # Time-based signup. Some fraction in a suspicious burst window
    # Base start ~90 days ago. We'll pick a random offset in days/hours.
    days_offset = random.randint(0, 90)
    suspicious_burst = False
    if random.random() < 0.05:
        # 5% chance to put them in a "burst" minute window
        suspicious_burst = True
        created_at = base_start + timedelta(days=days_offset, seconds=random.randint(0, 60))
    else:
        # normal distribution up to 24h in that day
        created_at = base_start + timedelta(days=days_offset, seconds=random.randint(0, 86400))

    user = {
        "user_id": user_id,
        "name": profile["name"],
        "email": profile["mail"],
        "username": profile["username"],
        "birthdate": profile["birthdate"].isoformat() if profile["birthdate"] else None,
        "gender": profile["sex"],
        "signup_ip": signup_ip,
        "device_id": device_id,
        "phone": phone_chosen,
        "country_code": country_code,
        "created_at": created_at,
        "burst_signup": suspicious_burst,  # for labeling logic
    }

    # Random missing fields
    fields_to_consider = ["name", "email", "phone", "country_code"]
    for field in fields_to_consider:
        if random.random() < MISSING_FIELD_PROB:
            user[field] = None

    # Fraud label
    user["fraud_label"] = assign_user_label(user, scenario_params)
    return user

def generate_user_dataset(num_users: int, scenario_params: dict) -> pd.DataFrame:
    collision_map = generate_ip_pool(num_users, collision_ratio=0.20)
    # We'll define a base reference date ~90 days ago
    base_start = datetime.now() - timedelta(days=90)

    users = []
    for i in range(num_users):
        user_data = generate_user_data(i + 1, collision_map, scenario_params, base_start)
        users.append(user_data)
    return pd.DataFrame(users)

###############################################################################
# BUSINESS GENERATION
###############################################################################

def generate_business_data(biz_id: int, scenario_params: dict) -> dict:
    """
    Introduce correlation between registration_country, name, and suspicious signals.
    """
    biz_name = random.choice([
        fake.company(),
        fake.company_suffix(),
        "FakeCo " + fake.word(),
        fake.bs(),
        "Phantom Inc " + fake.color_name(),
    ])

    reg_country = fake.country_code()
    biz = {
        "business_id": biz_id,
        "business_name": biz_name,
        "registration_country": reg_country,
        "incorporation_date": fake.date_between(start_date="-15y", end_date="today"),
        "owner_name": fake.name(),
    }

    # Random missing fields
    if random.random() < MISSING_FIELD_PROB:
        biz["owner_name"] = None
    if random.random() < MISSING_FIELD_PROB:
        biz["registration_country"] = None

    # Fraud label
    biz["fraud_label"] = assign_business_label(biz, scenario_params)
    return biz

def generate_business_dataset(num_businesses: int, scenario_params: dict) -> pd.DataFrame:
    businesses = []
    for i in range(num_businesses):
        biz_data = generate_business_data(i + 1, scenario_params)
        businesses.append(biz_data)
    return pd.DataFrame(businesses)

###############################################################################
# RELATIONSHIP GENERATION
###############################################################################

def link_users_to_businesses(
    df_users: pd.DataFrame,
    df_businesses: pd.DataFrame,
    ownership_probability: float = 0.4,
    max_businesses_per_user: int = 10
) -> pd.DataFrame:
    """
    Creates user-business relationships. Each user has a 'ownership_probability'
    chance to own 1..max_businesses_per_user. For advanced realism, you could
    also let multiple users share the same business. 
    """
    relationships = []
    user_ids = df_users["user_id"].tolist()
    biz_ids = df_businesses["business_id"].tolist()

    for user_id in user_ids:
        if random.random() < ownership_probability:
            num_biz_owned = random.randint(1, max_businesses_per_user)
            chosen_biz_ids = random.sample(biz_ids, min(num_biz_owned, len(biz_ids)))
            for b_id in chosen_biz_ids:
                relationships.append({"user_id": user_id, "business_id": b_id})

    return pd.DataFrame(relationships)

###############################################################################
# FEATURE ENRICHMENT
###############################################################################

def enrich_user_features(df_users, df_relationships, df_businesses):
    """
    1) email_domain: separate out from 'email'
    2) ip_count: how many users share the same IP
    3) num_fraud_biz_owned: how many fraudulent businesses each user owns
    """
    # 1) Email domain
    df_users['email_domain'] = df_users['email'].apply(
        lambda x: x.split('@')[-1] if x and '@' in str(x) else 'missing'
    )

    # 2) IP frequency
    ip_counts = df_users.groupby('signup_ip')['user_id'].transform('count')
    df_users['ip_count'] = ip_counts

    # 3) num_fraud_biz_owned
    df_userbiz = df_relationships.merge(
        df_businesses[['business_id','fraud_label']], on='business_id', how='left'
    )
    user_fraud_biz_count = df_userbiz.groupby('user_id')['fraud_label'].sum().reset_index(name='num_fraud_biz_owned')
    df_users = df_users.merge(user_fraud_biz_count, on='user_id', how='left')
    df_users['num_fraud_biz_owned'] = df_users['num_fraud_biz_owned'].fillna(0)

    return df_users

###############################################################################
# MAIN SCRIPT
###############################################################################

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic users & businesses with fraud labels (enhanced).")
    parser.add_argument("--num-users", type=int, default=DEFAULT_NUM_USERS, help="Number of users to generate.")
    parser.add_argument("--num-businesses", type=int, default=DEFAULT_NUM_BUSINESSES, help="Number of businesses to generate.")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility. Default=None for no seed.")
    parser.add_argument("--scenario", type=str, default="default", choices=["default", "low_fraud", "high_fraud"],
                        help="Scenario-based config for base fraud rates.")
    args = parser.parse_args()

    # Optional seed for reproducibility
    if args.seed is not None:
        print(f"[INFO] Setting random seed to {args.seed}")
        random.seed(args.seed)
        Faker.seed(args.seed)

    # Determine scenario-based parameters
    scenario = args.scenario
    scenario_params = SCENARIO_CONFIG.get(scenario, SCENARIO_CONFIG["default"])

    num_users = args.num_users
    num_businesses = args.num_businesses

    print(f"===== Synthetic Data Generation (Scenario: {scenario}) =====")
    print(f"User base fraud: {scenario_params['user_base_fraud']} | Biz base fraud: {scenario_params['biz_base_fraud']}")
    print(f"Generating {num_users} users, {num_businesses} businesses...")

    print("-> Creating user dataset...")
    df_users = generate_user_dataset(num_users, scenario_params)
    df_users.to_csv("synthetic_users.csv", index=False)
    print(f"[DONE] synthetic_users.csv with {len(df_users)} records.")

    print("-> Creating business dataset...")
    df_businesses = generate_business_dataset(num_businesses, scenario_params)
    df_businesses.to_csv("synthetic_businesses.csv", index=False)
    print(f"[DONE] synthetic_businesses.csv with {len(df_businesses)} records.")

    print("-> Linking users to businesses via relationships...")
    df_relationships = link_users_to_businesses(
        df_users,
        df_businesses,
        ownership_probability=0.40,
        max_businesses_per_user=10
    )
    df_relationships.to_csv("user_business_relationships.csv", index=False)
    print(f"[DONE] user_business_relationships.csv with {len(df_relationships)} records.")

    print("-> Enriching user dataset (email_domain, ip_count, num_fraud_biz_owned)...")
    df_users_enriched = enrich_user_features(df_users, df_relationships, df_businesses)
    df_users_enriched.to_csv("synthetic_users_enriched.csv", index=False)
    print("[DONE] synthetic_users_enriched.csv generated.")

    # Optional summary stats
    user_fraud_ratio = df_users_enriched['fraud_label'].mean()
    business_fraud_ratio = df_businesses['fraud_label'].mean()

    print("\n===== Summary Stats =====")
    print(f"User Fraud Ratio: {user_fraud_ratio:.2%}")
    print(f"Business Fraud Ratio: {business_fraud_ratio:.2%}")
    print("All CSV files generated successfully. Enjoy your advanced synthetic dataset!")

if __name__ == "__main__":
    main()
