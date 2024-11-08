class CollectionQueries:
    @staticmethod
    def check_collection_exists():
        return "SELECT COUNT(*) AS count FROM collection WHERE collection_name = %s"
    
    @staticmethod
    def insert_collection():
        return "INSERT INTO collection (collection_id, collection_name, description) VALUES (%s,%s,%s)"
    
    @staticmethod
    def check_collection_by_id():
        return "SELECT COUNT(*) AS count FROM collection WHERE collection_id = %s"
    
    @staticmethod
    def delete_resources_by_collection_id():
        return "DELETE FROM resources WHERE collection_id = %s"
    
    @staticmethod
    def delete_collection_by_id():
        return "DELETE FROM collection WHERE collection_id = %s"

    @staticmethod
    def get_all_collections():
        return "SELECT collection_id, collection_name, description FROM collection"
