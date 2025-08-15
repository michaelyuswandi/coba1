import os
from app import app, db

print("--- Database Initializer ---")
print("This script will drop and recreate all tables based on current models.")

with app.app_context():
    print("Dropping all tables...")
    db.drop_all()
    print("Tables dropped.")

    print("Creating all tables...")
    db.create_all()
    print("Tables created successfully.")

print("Database initialization complete.")
