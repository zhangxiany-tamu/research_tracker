import sqlite3

# Add section column to existing database
def add_section_column():
    conn = sqlite3.connect('research_tracker.db')
    cursor = conn.cursor()
    
    # Check if column already exists
    cursor.execute("PRAGMA table_info(papers)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'section' not in columns:
        print("Adding section column to papers table...")
        cursor.execute("ALTER TABLE papers ADD COLUMN section VARCHAR(100)")
        conn.commit()
        print("Section column added successfully")
    else:
        print("Section column already exists")
    
    conn.close()

if __name__ == "__main__":
    add_section_column()