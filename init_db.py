import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

def create_database():
    try:
        print("🚀 Inicializando banco de dados Adote-me...")
        
        # Conectar ao MySQL (sem especificar o database)
        connection = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', ''),
            port=int(os.getenv('MYSQL_PORT', 3306))
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # 1. Criar database se não existir
            cursor.execute("CREATE DATABASE IF NOT EXISTS `adote-me`")
            print("✅ Database 'adote-me' criado/verificado")
            
            # 2. Usar o database
            cursor.execute("USE `adote-me`")
            
            # 3. Criar tabela de usuários
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nome VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    senha VARCHAR(255) NOT NULL,
                    telefone VARCHAR(20),
                    endereco TEXT,
                    tipo ENUM('adotante', 'protetor', 'admin') DEFAULT 'adotante',
                    data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP,
                    nome_organizacao VARCHAR(100),
                    cnpj VARCHAR(18),
                    verificado BOOLEAN DEFAULT FALSE
                )
            ''')
            print("✅ Tabela 'usuarios' criada/verificada")
            
            # 4. Criar tabela de pets
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pets (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nome VARCHAR(100) NOT NULL,
                    especie VARCHAR(50) NOT NULL,
                    idade INT,
                    descricao TEXT,
                    imagem_url VARCHAR(255),
                    usuario_id INT,
                    data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            print("✅ Tabela 'pets' criada/verificada")
            
            # 5. Criar tabela de adoções
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS adocoes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    pet_id INT NOT NULL,
                    nome VARCHAR(100) NOT NULL,
                    email VARCHAR(100) NOT NULL,
                    telefone VARCHAR(20) NOT NULL,
                    mensagem TEXT NOT NULL,
                    data_solicitacao DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(20) DEFAULT 'pendente'
                )
            ''')
            print("✅ Tabela 'adocoes' criada/verificada")
            
            connection.commit()
            cursor.close()
            connection.close()
            
            print("🎉 Banco de dados inicializado com sucesso!")
            print("📊 Tabelas criadas: usuarios, pets, adocoes")
            
    except Error as e:
        print(f"❌ Erro ao criar banco de dados: {e}")
    except Exception as e:
        print(f"❌ Erro geral: {e}")

if __name__ == "__main__":
    create_database()