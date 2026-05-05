"""MongoDB client factory for web-ui persistence."""
from __future__ import annotations

import os

from pymongo import MongoClient
from pymongo.database import Database


def build_mongo_database() -> Database:
    """Create the MongoDB database used by web-ui."""
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    database_name = os.getenv("MONGODB_DATABASE", "guardian_web_ui")

    client: MongoClient = MongoClient(uri)
    return client[database_name]