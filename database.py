import mysql.connector

def get_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Prasanthi@3103",
        database="house_rental"
    )
    return conn