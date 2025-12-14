from gcrs.db.database import get_engine, init_db

engine = get_engine()
print("connection successful")

init_db()
print("database initialized")