# 🐾 Adote-me - Sistema de Adoção de Animais

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.3%2B-green)
![MySQL](https://img.shields.io/badge/MySQL-8.0%2B-orange)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple)

Sistema web para facilitar a adoção de animais, conectando protetores/ONGs a pessoas interessadas em adotar pets.

## 📋 Índice

- [Funcionalidades](#funcionalidades)
- [Tecnologias](#tecnologias)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Uso](#uso)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [API Endpoints](#api-endpoints)
- [Contribuição](#contribuição)
- [Licença](#licença)

## 🚀 Funcionalidades

### 👤 Para Usuários Comuns
- ✅ Cadastro e autenticação de usuários
- ✅ Busca de animais disponíveis para adoção
- ✅ Perfil de usuário com dados pessoais
<!-- - ✅ Sistema de favoritos -->
- ✅ Filtros avançados para busca

### 🏢 Para Protetores/ONGs
- ✅ Cadastro como protetor/ONG
- ✅ Cadastro de animais para adoção
- ✅ Gerenciamento de animais cadastrados
- ✅ Dashboard administrativo
- ✅ Controle de solicitações de adoção

### 🛠️ Administrativas
- ✅ Interface responsiva com Bootstrap
- ✅ Sistema de segurança com hash de senhas
- ✅ Validação de formulários
- ✅ Mensagens flash para feedback
- ✅ Banco de dados MySQL

## 💻 Tecnologias

**Backend:**
- Python 3.8+
- Flask 2.3+
- MySQL 8.0+
- Werkzeug (security)

**Frontend:**
- HTML5, CSS3, JavaScript
- Bootstrap 5.3
- Jinja2 Templates

**Ferramentas:**
- pip (gerenciador de pacotes)
- mysql-connector-python
- python-dotenv

## 📦 Pré-requisitos

Antes de começar, verifique se você tem instalado:

- Python 3.8 ou superior
- MySQL 8.0 ou superior
- pip (gerenciador de pacotes Python)
- Git (para controle de versão)

## 🛠️ Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/adote-me.git
cd adote-me

2. Crie um ambiente virtual (recomendado)
bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate

3. Instale as dependências
bash
pip install -r requirements.txt

4. Configure o banco de dados
sql
-- Crie o banco de dados
CREATE DATABASE adote_me;

-- Ou execute o script de inicialização
python init_db.py

5. Configure as variáveis de ambiente
Crie um arquivo .env na raiz do projeto:

env
# Configurações do Banco de Dados
DB_HOST=localhost
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_NAME=adote_me
DB_PORT=3306

# Configurações do Flask
SECRET_KEY=sua_chave_secreta_muito_segura_aqui
DEBUG=True

# Configurações de Email (opcional)
EMAIL_SERVER=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=seu_email@gmail.com
EMAIL_PASSWORD=sua_senha_de_app

6. Execute a aplicação
bash
python app.py
A aplicação estará disponível em: http://localhost:5000

⚙️ Configuração
Configuração do MySQL
Instale o MySQL Server

Crie um usuário e banco de dados:

sql
CREATE DATABASE adote_me;
CREATE USER 'adote_user'@'localhost' IDENTIFIED BY 'sua_senha_segura';
GRANT ALL PRIVILEGES ON adote_me.* TO 'adote_user'@'localhost';
FLUSH PRIVILEGES;
Variáveis de Ambiente Obrigatórias
Variável    Descrição   Exemplo
DB_HOST Host do MySQL   localhost
DB_USER Usuário do MySQL    root
DB_PASSWORD Senha do MySQL  sua_senha
DB_NAME Nome do banco   adote_me
SECRET_KEY  Chave do Flask  chave-muito-secreta

🎯 Uso
Primeiro Acesso
Acesse a aplicação: http://localhost:5000

Cadastre-se: Clique em "Criar Conta" no menu

Complete seu perfil: Preencha dados pessoais e endereço

Explore animais: Navegue pelos animais disponíveis

Para Protetores/ONGs
Marque a opção: Durante o cadastro, marque "Sou protetor/ONG"

Preencha dados da organização: Informe nome e CNPJ (opcional)

Acesse o dashboard: Após login, acesse a área administrativa

Cadastre animais: Adicione fotos e informações dos pets

Funcionalidades Principais
Busca: Filtre por espécie, raça, idade, localização

Favoritos: Salve animais de interesse

Perfil: Gerencie suas informações pessoais

Solicitações: Envie pedidos de adoção

📁 Estrutura do Projeto
text
adote-me/
│
├── app.py                 # Aplicação principal Flask
├── database.py            # Configuração do banco de dados
├── requirements.txt       # Dependências do projeto
├── .env                  # Variáveis de ambiente
├── init_db.py   
│        # Script de inicialização do BD
├── templates/            # Templates HTML
│   ├── base.html         # Template base
│   ├── cadastro.html     # Página de cadastro
│   ├── login.html        # Página de login
│   ├── index.html        # Página inicial
│   └── dashboard/        # Templates do dashboard
│
├── static/               # Arquivos estáticos
│   ├── css/
│   ├── js/
│   ├── images/
│   └── uploads/
└──

🔌 API Endpoints
Autenticação
Método  Endpoint    Descrição
POST    /cadastrar_usuario  Cadastra novo usuário
POST    /login  Autentica usuário
GET /logout Encerra sessão
Usuários
Método  Endpoint    Descrição
GET /perfil Visualiza perfil
PUT /perfil/editar  Edita perfil
GET /usuarios   Lista usuários (admin)
Animais
Método  Endpoint    Descrição
GET /animais    Lista animais
POST    /animais/cadastrar  Cadastra animal
GET /animais/<id>   Detalhes do animal
PUT /animais/<id>/editar    Edita animal
🤝 Contribuição
Contribuições são sempre bem-vindas! Para contribuir:

Fork o projeto

Crie uma branch para sua feature (git checkout -b feature/AmazingFeature)

Commit suas mudanças (git commit -m 'Add some AmazingFeature')

Push para a branch (git push origin feature/AmazingFeature)

Abra um Pull Request

Padrões de Código
Siga o estilo PEP 8 para Python

Use commits semânticos

Documente novas funcionalidades

Teste suas alterações

📝 Licença
Este projeto está sob a licença MIT. Veja o arquivo LICENSE para detalhes.




