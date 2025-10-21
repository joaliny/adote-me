import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

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
                cpf VARCHAR(14) UNIQUE,                 -- CPF (para adotantes/protetores individuais)
                cnpj VARCHAR(18) UNIQUE,                -- CNPJ (para ONGs/Instituições)
                tipo ENUM('adotante', 'protetor', 'ong', 'admin') DEFAULT 'adotante', -- NOVO TIPO: 'ong'
                data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP,
                nome_organizacao VARCHAR(100),
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
                    data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                )
            ''')
            print("✅ Tabela 'pets' criada/verificada")
            
            # 5. Criar tabela de adoções
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS adocoes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    pet_id INT NOT NULL,
                    usuario_id INT,
                    nome VARCHAR(100) NOT NULL,
                    email VARCHAR(100) NOT NULL,
                    telefone VARCHAR(20) NOT NULL,
                    mensagem TEXT NOT NULL,
                    data_solicitacao DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(20) DEFAULT 'pendente',
                    FOREIGN KEY (pet_id) REFERENCES pets(id),
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                )
            ''')
            print("✅ Tabela 'adocoes' criada/verificada")

            # Criar tabela de postagens do Blog (NOVO PASSO)
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS postagens (
            id INT AUTO_INCREMENT PRIMARY KEY,
            titulo VARCHAR(255) NOT NULL,
            subtitulo VARCHAR(255),
            conteudo TEXT NOT NULL,
            imagem_url VARCHAR(255),
            autor_id INT,
            categoria VARCHAR(50),
            data_publicacao DATETIME DEFAULT CURRENT_TIMESTAMP,
            slug VARCHAR(255) UNIQUE NOT NULL,
            FOREIGN KEY (autor_id) REFERENCES usuarios(id)
            )
            ''')
            
            # 6. Criar admin principal apenas se não existir nenhum admin
            criar_admin_principal(cursor)
            
            connection.commit()
            cursor.close()
            connection.close()
            
            print("🎉 Banco de dados inicializado com sucesso!")
            print("📊 Tabelas criadas: usuarios, pets, adocoes")
            
    except Error as e:
        print(f"❌ Erro ao criar banco de dados: {e}")
    except Exception as e:
        print(f"❌ Erro geral: {e}")

def criar_admin_principal(cursor):
    """Cria um admin principal apenas se não existir nenhum admin"""
    try:
        # Verificar se já existe algum admin
        cursor.execute("SELECT id FROM usuarios WHERE tipo = 'admin' LIMIT 1")
        admin_existente = cursor.fetchone()
        
        if admin_existente:
            print("✅ Já existem administradores no sistema")
            return
        
        # Dados do admin principal
        admin_email = "admin@adote.me"
        admin_senha = "123456"
        admin_nome = "Administrador Principal"
        
        # Criptografar senha
        senha_hash = generate_password_hash(admin_senha)
        
        # Inserir usuário admin principal
        cursor.execute('''
            INSERT INTO usuarios 
            (nome, email, senha, tipo, telefone, verificado, data_cadastro)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
        ''', (
            admin_nome, 
            admin_email, 
            senha_hash, 
            'admin', 
            '(92) 99999-9999', 
            True
        ))
        
        print("👑 Admin principal criado com sucesso!")
        print(f"   📧 Email: {admin_email}")
        print(f"   🔑 Senha: {admin_senha}")
        print("   ⚠️  Use estas credenciais para acessar o sistema")
        
    except Error as e:
        print(f"❌ Erro ao criar admin principal: {e}")
    except Exception as e:
        print(f"❌ Erro geral ao criar admin: {e}")

if __name__ == "__main__":
    create_database()