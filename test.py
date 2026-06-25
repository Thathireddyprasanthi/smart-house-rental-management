import mysql.connector

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Prasanthi@3103"
    )

    print("Connected Successfully!")

except Exception as e:
    print("Error:", e)