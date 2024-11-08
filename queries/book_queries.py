class BookQueries:
    @staticmethod
    def check_book_exists():
        return "SELECT * FROM books WHERE book_name = %s AND author = %s"
    
    @staticmethod
    def insert_book():
        return """
            INSERT INTO books (book_name, author, total_copies, available_copies, contributors)
            VALUES (%s, %s, %s, %s, %s)
        """
    
    @staticmethod
    def update_book():
        return """
            UPDATE books
            SET total_copies = %s, available_copies = %s, contributors = %s
            WHERE book_name = %s AND author = %s
        """
    
    @staticmethod
    def get_all_books():
        return "SELECT book_name, author, total_copies, available_copies, contributors, borrowers FROM books"
    
    @staticmethod
    def get_book_details():
        return "SELECT available_copies, borrowers FROM books WHERE book_name = %s"
    
    @staticmethod
    def update_borrowers():
        return "UPDATE books SET available_copies = %s, borrowers = %s WHERE book_name = %s"
    
    @staticmethod
    def delete_book():
        return "DELETE FROM books WHERE book_name = %s"
    
    @staticmethod
    def update_copies():
        return """
            UPDATE books 
            SET available_copies = available_copies - 1, total_copies = total_copies - 1 
            WHERE book_name = %s
        """
    
    @staticmethod
    def search_books():
        return "SELECT book_name, author FROM books WHERE book_name LIKE %s"
