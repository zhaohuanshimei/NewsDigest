import os

API_PREFIX = "/api/v1"
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://news:news@localhost:5432/news_digest")
