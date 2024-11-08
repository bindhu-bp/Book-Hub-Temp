class ResourceQueries:
    @staticmethod
    def check_resource_exists():
        return "SELECT COUNT(*) AS count FROM resources WHERE link = %s AND collection_id = %s"
    
    @staticmethod
    def insert_resource():
        return "INSERT INTO resources (resource_id, resource_name, link, description, collection_id) VALUES (%s,%s, %s, %s, %s)"
    
    @staticmethod
    def get_resources_by_collection():
        return "SELECT resource_id, resource_name, link, description FROM resources WHERE collection_id = %s"
    
    @staticmethod
    def delete_resource():
        return "DELETE FROM resources WHERE collection_id = %s AND resource_id = %s"
