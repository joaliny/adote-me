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


                    -- NOVOS CAMPOS ADICIONADOS --
                    porte ENUM('pequeno', 'medio', 'grande'),
                    sexo ENUM('macho', 'femea'),
                    localizacao VARCHAR(255),
                    historia TEXT,
                    informacoes_saude TEXT,
                    -- FIM DOS NOVOS CAMPOS --

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

            # 6. Criar tabela de favoritos
            cursor.execute('''
               CREATE TABLE IF NOT EXISTS favoritos (
                   id INT AUTO_INCREMENT PRIMARY KEY,
                   usuario_id INT NOT NULL,
                   pet_id INT NOT NULL,
                   data_favoritado DATETIME DEFAULT CURRENT_TIMESTAMP,
                   FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
                   FOREIGN KEY (pet_id) REFERENCES pets(id) ON DELETE CASCADE,
                   UNIQUE KEY unique_favorito (usuario_id, pet_id)
                )
            ''')
            print("✅ Tabela 'favoritos' criada/verificada")
            
            # 7. Criar tabela de pets perdidos ← ADICIONE AQUI
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pets_perdidos (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    usuario_id INT NOT NULL,
                    nome VARCHAR(100) NOT NULL,
                    especie VARCHAR(50) NOT NULL,
                    raca VARCHAR(100),
                    cor VARCHAR(50),
                    porte ENUM('pequeno', 'medio', 'grande'),
                    sexo ENUM('macho', 'femea'),
                    idade VARCHAR(50),
                    caracteristicas TEXT,
                    data_desaparecimento DATE NOT NULL,
                    local_desaparecimento VARCHAR(255) NOT NULL,
                    referencia TEXT,
                    descricao TEXT NOT NULL,
                    microchip BOOLEAN DEFAULT FALSE,
                    coleira BOOLEAN DEFAULT FALSE,
                    vacinado BOOLEAN DEFAULT FALSE,
                    contato_nome VARCHAR(100) NOT NULL,
                    contato_telefone VARCHAR(20) NOT NULL,
                    contato_email VARCHAR(100),
                    foto_path VARCHAR(255),
                    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
                    data_encontrado DATETIME,
                    status ENUM('perdido', 'encontrado') DEFAULT 'perdido',
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
                )
            ''')
            print("✅ Tabela 'pets_perdidos' criada/verificada")

            # 8. Criar admin principal apenas se não existir nenhum admin
            criar_admin_principal(cursor)
            
            connection.commit()
            cursor.close()
            connection.close()
            
            print("🎉 Banco de dados inicializado com sucesso!")
            print("📊 Tabelas criadas: usuarios, pets, adocoes, favoritos, pets_perdidos")
            
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