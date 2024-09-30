import os
import sqlite3
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Database initialization
def initialize_db():
    db_path = 'documents.db'
    # Remove the existing database file if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
        logging.info("Existing database removed.")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Create new tables
        cursor.execute('''CREATE TABLE IF NOT EXISTS folders
                          (id INTEGER PRIMARY KEY, foldername TEXT UNIQUE, parent_id INTEGER,
                          FOREIGN KEY (parent_id) REFERENCES folders(id))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS documents
                          (id INTEGER PRIMARY KEY, filename TEXT, content TEXT, folder_id INTEGER,
                          FOREIGN KEY (folder_id) REFERENCES folders(id))''')
        conn.commit()
        conn.close()
        logging.info("Database initialized and tables created.")
    except sqlite3.Error as e:
        logging.error(f"Database initialization failed: {e}")

# Event handler for file system changes
class FileChangeHandler(FileSystemEventHandler):
    def __init__(self):
        pass

    def on_modified(self, event):
        if not event.is_directory:
            logging.info(f'Modified file: {event.src_path}')
            self.update_db(event.src_path)

    def on_created(self, event):
        if not event.is_directory:
            logging.info(f'Created file: {event.src_path}')
            self.update_db(event.src_path)

    def on_deleted(self, event):
        if not event.is_directory:
            logging.info(f'Deleted file: {event.src_path}')
            self.delete_from_db(event.src_path)

    def update_db(self, file_path):
        try:
            with open(file_path, 'r') as file:
                content = file.read()
            filename = os.path.basename(file_path)
            folderpath = os.path.dirname(file_path)
            foldername = os.path.basename(folderpath)
            parent_folderpath = os.path.dirname(folderpath)
            parent_foldername = os.path.basename(parent_folderpath) if parent_folderpath else None

            conn = sqlite3.connect('documents.db')
            cursor = conn.cursor()

            # Insert or ignore the parent folder
            if parent_foldername:
                cursor.execute('''INSERT OR IGNORE INTO folders (foldername) VALUES (?)''', (parent_foldername,))
                cursor.execute('''SELECT id FROM folders WHERE foldername = ?''', (parent_foldername,))
                parent_id = cursor.fetchone()[0]
            else:
                parent_id = None

            # Insert or ignore the folder with parent_id
            cursor.execute('''INSERT OR IGNORE INTO folders (foldername, parent_id) VALUES (?, ?)''', (foldername, parent_id))
            # Get the folder_id
            cursor.execute('''SELECT id FROM folders WHERE foldername = ?''', (foldername,))
            folder_id = cursor.fetchone()[0]

            # Insert or replace the document
            cursor.execute('''INSERT OR REPLACE INTO documents (filename, content, folder_id)
                              VALUES (?, ?, ?)''', (filename, content, folder_id))
            conn.commit()
            conn.close()
            logging.info(f'Updated database with file: {filename} in folder: {foldername}')
        except Exception as e:
            logging.error(f"Failed to update database for file {file_path}: {e}")

    def delete_from_db(self, file_path):
        try:
            filename = os.path.basename(file_path)
            conn = sqlite3.connect('documents.db')
            cursor = conn.cursor()
            cursor.execute('''DELETE FROM documents WHERE filename = ?''', (filename,))
            conn.commit()
            conn.close()
            logging.info(f'Removed file from database: {filename}')
        except Exception as e:
            logging.error(f"Failed to delete from database for file {file_path}: {e}")

# Function to query the database and retrieve document contents
def get_documents():
    try:
        conn = sqlite3.connect('documents.db')
        cursor = conn.cursor()
        cursor.execute('''SELECT d.filename, d.content, f.foldername 
                          FROM documents d 
                          JOIN folders f ON d.folder_id = f.id''')
        documents = cursor.fetchall()
        conn.close()
        return documents
    except sqlite3.Error as e:
        logging.error(f"Failed to retrieve documents from database: {e}")
        return []

# Main function to set up the observer
def main():
    initialize_db()
    path = r'C:\Users\matth\Coding\Axiomatic secret work\dynamic-sql\Documents'
    event_handler = FileChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    logging.info(f'Starting to monitor: {path}')
    try:
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
    # Example usage of get_documents function
    documents = get_documents()
    for filename, content, foldername in documents:
        print(f'Filename: {filename}\nFolder: {foldername}\nContent:\n{content}\n')