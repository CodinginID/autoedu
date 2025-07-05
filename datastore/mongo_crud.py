from pymongo.collection import Collection

# CREATE
def create_one(collection: Collection, data: dict) -> str:
    result = collection.insert_one(data)
    return str(result.inserted_id)

# READ ONE by filter
def get_one(collection: Collection, query: dict, projection=None) -> dict:
    return collection.find_one(query, projection)

# READ MANY
def get_many(collection: Collection, query: dict = {}, projection=None) -> list:
    return list(collection.find(query, projection))

# UPDATE ONE
def update_one(collection: Collection, filter: dict, update: dict) -> bool:
    result = collection.update_one(filter, {'$set': update})
    return result.modified_count > 0

# DELETE ONE
def delete_one(collection: Collection, filter: dict) -> bool:
    result = collection.delete_one(filter)
    return result.deleted_count > 0

# DELETE MANY
def delete_many(collection: Collection, filter: dict) -> bool:
    result = collection.delete_many(filter)
    return result.deleted_count > 0
