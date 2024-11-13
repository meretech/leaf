import pyodbc

def create_connection():
    try:
        conn = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            'SERVER=localhost\\SQLEXPRESS;'
            'DATABASE=LeafAppDB;'
            'UID=sa;'
            'PWD=rafiq;'
        )
        print("Connection successful")
        return conn
    except Exception as e:
        print("Error connecting to database:", e)
        print(e)
        return None

#create_connection()