# test_xampp.py
import mysql.connector

try:
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',  # SENHA VAZIA para XAMPP
        port=3306
    )
    print("✅ Conectado ao XAMPP MySQL com sucesso!")
    connection.close()
except Exception as e:
    print(f"❌ Erro: {e}")