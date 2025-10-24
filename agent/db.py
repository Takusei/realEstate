import os
from functools import lru_cache

import pymongo


@lru_cache(maxsize=1)
def get_collections():
    client = pymongo.MongoClient(os.environ["MONGO_URI"])
    db = client[os.environ.get("DB_NAME", "suumo")]
    coll_name = os.environ.get("MONGO_COLLECTION_NAME", "suumo")  # ← add this
    return db[coll_name], db["events"]
