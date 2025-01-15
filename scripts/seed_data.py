"""
seed_data.py

Populates the VeriShield project's local database with realistic dummy data for Users and Businesses.
Utilizes the Faker library to generate names, emails, addresses, etc.
This script also demonstrates how to seed Neo4j (optional) with basic user/business relationships.
"""

import sys
import os
import random
from faker import Faker
from passlib.context import CryptContext

# Adjust Python path to recognize 'app' package if needed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database import SessionLocal, engine, Base, driver
from backend.app.models import User, Business

# Initialize Faker
fake = Faker()
# If you want consistent results each run, uncomment:
# Faker.seed(1234)

# Initialize password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_users(db, num_users=10):
    """
    Generate a specified number of user records with realistic names and emails.
    Some users might be 'verified', others not.
    """
    user_objects = []
    for _ in range(num_users):
        email = fake.unique.email()
        password_hash = pwd_context.hash("DefaultPass123")  # or randomize if you like
        is_verified = random.choice([True, False])  # 50% chance user is verified

        user = User(
            email=email,
            password_hash=password_hash,
            is_verified=is_verified
        )
        db.add(user)
        user_objects.append(user)

    db.commit()  # Commit all new users so we have valid IDs
    for user in user_objects:
        db.refresh(user)  # Refresh to get the auto-generated ID

    return user_objects


def generate_businesses(db, users, num_businesses=15):
    """
    Generate businesses and optionally assign them to random users.
    Some businesses might be verified, others not.
    """
    business_objects = []
    for _ in range(num_businesses):
        name = fake.unique.company()
        is_verified = random.choice([True, False])

        # Randomly pick an owner (or None)
        owner = random.choice(users + [None]) if users else None
        owner_id = owner.id if owner else None

        biz = Business(
            name=name,
            is_verified=is_verified,
            owner_id=owner_id
        )
        db.add(biz)
        business_objects.append(biz)

    db.commit()
    for biz in business_objects:
        db.refresh(biz)

    return business_objects


def seed_postgres_data(db, num_users=10, num_businesses=15):
    """
    Creates tables (if not existing), seeds 'users' and 'businesses' in PostgreSQL.
    Returns lists of created user and business objects.
    """
    print("Creating (if not exists) all tables...")
    Base.metadata.create_all(bind=engine)

    print(f"Generating {num_users} users...")
    users = generate_users(db, num_users=num_users)

    print(f"Generating {num_businesses} businesses...")
    businesses = generate_businesses(db, users, num_businesses=num_businesses)

    print("PostgreSQL seeding complete!")
    return users, businesses


def seed_neo4j_data(users, businesses):
    """
    OPTIONAL: Demonstrates how to seed basic relationships in Neo4j.
    For example: Create (:User {email: ...}) nodes and link them to 
    (:Business {name: ...}) via (:User)-[:OWNS]->(:Business).

    Requires that you have a 'driver' from your Neo4j config in app.database.
    """
    with driver.session() as session:
        # Clear existing data (CAUTION: in dev only)
        session.run("MATCH (n) DETACH DELETE n")
        print("Neo4j: All existing nodes/relationships cleared. (Dev only)")

        # Create user nodes
        for user in users:
            session.run(
                """
                CREATE (u:User {userId: $userId, email: $email, isVerified: $isVerified})
                """,
                userId=user.id, email=user.email, isVerified=user.is_verified
            )

        # Create business nodes
        for biz in businesses:
            session.run(
                """
                CREATE (b:Business {bizId: $bizId, name: $name, isVerified: $isVerified})
                """,
                bizId=biz.id, name=biz.name, isVerified=biz.is_verified
            )

        # Create relationships: for each business that has an owner
        # link the corresponding user node
        for biz in businesses:
            if biz.owner_id:
                session.run(
                    """
                    MATCH (u:User {userId: $ownerId}), (b:Business {bizId: $bizId})
                    CREATE (u)-[:OWNS]->(b)
                    """,
                    ownerId=biz.owner_id, bizId=biz.id
                )

        print("Neo4j seeding complete!")


def seed(num_users=10, num_businesses=15, seed_neo4j=False):
    """
    Main function to orchestrate seeding PostgreSQL + optional Neo4j.
    """
    db = SessionLocal()
    try:
        # Seed Postgres
        users, businesses = seed_postgres_data(db, num_users, num_businesses)

        # Seed Neo4j if needed
        if seed_neo4j:
            seed_neo4j_data(users, businesses)

        print("Done seeding data!")
    finally:
        db.close()


if __name__ == "__main__":
    # Example usage:
    # python seed_data.py  --> seeds default amounts of data (10 users, 15 businesses) in Postgres, skip Neo4j
    # python seed_data.py 20 30 True  --> seeds 20 users, 30 businesses, plus Neo4j
    import argparse

    parser = argparse.ArgumentParser(description="Seed the database with sample data.")
    parser.add_argument("num_users", nargs="?", type=int, default=10, help="Number of users to generate.")
    parser.add_argument("num_businesses", nargs="?", type=int, default=15, help="Number of businesses to generate.")
    parser.add_argument("seed_neo4j", nargs="?", type=bool, default=False, help="Whether to seed Neo4j data (True/False).")

    args = parser.parse_args()

    seed(num_users=args.num_users, num_businesses=args.num_businesses, seed_neo4j=args.seed_neo4j)
