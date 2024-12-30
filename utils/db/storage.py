import sqlite3 as lite

class DatabaseManager(object):

    def __init__(self, path):
        self.conn = lite.connect(path)
        self.conn.execute('pragma foreign_keys = on')
        self.conn.commit()
        self.cur = self.conn.cursor()
    
    def create_tables(self):
        # Create tables if they don't exist
        tables = [
            '''CREATE TABLE IF NOT EXISTS products (
                idx text, 
                title text, 
                body text, 
                photo blob, 
                price int, 
                tag text
            )''',
            '''CREATE TABLE IF NOT EXISTS orders (
                cid int, 
                usr_name text, 
                usr_address text, 
                products text, 
                photo blob, 
                comment text, 
                status TEXT DEFAULT 'pending', 
                order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usr_username TEXT
            )''',
            '''CREATE TABLE IF NOT EXISTS cart (
                cid int, 
                idx text, 
                quantity int
            )''',
            '''CREATE TABLE IF NOT EXISTS categories (
                idx text, 
                title text
            )''',
            '''CREATE TABLE IF NOT EXISTS notification (
                cid int, 
                notification TEXT
            )''',
            '''CREATE TABLE IF NOT EXISTS questions (
                cid int, 
                question text
            )'''
        ]
        
        # Execute each table creation query
        for table_query in tables:
            self.query(table_query)

    def query(self, arg, values=None):
        if values == None:
            self.cur.execute(arg)
        else:
            self.cur.execute(arg, values)
        self.conn.commit()

    def fetchone(self, arg, values=None):
        if values == None:
            self.cur.execute(arg)
        else:
            self.cur.execute(arg, values)
        return self.cur.fetchone()

    def fetchall(self, arg, values=None):
        if values == None:
            self.cur.execute(arg)
        else:
            self.cur.execute(arg, values)
        return self.cur.fetchall()

    def __del__(self):
        self.conn.close()


