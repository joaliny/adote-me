🐾 Adote-me - Sistema de Adoção de Animais
https://img.shields.io/badge/Python-3.8%252B-blue
https://img.shields.io/badge/Flask-2.3%252B-green
https://img.shields.io/badge/MySQL-8.0%252B-orange
https://img.shields.io/badge/Bootstrap-5.3-purple

Sistema web completo para conectar animais que precisam de um lar com pessoas dispostas a adotar com responsabilidade.

# 🎯 O Que é o Adote-me? 
O Adote-me é uma plataforma web que facilita o processo de adoção de animais, conectando:

🏠 Pessoas interessadas em adotar um pet
🏢 Protetores e ONGs que resgatam animais
🐕 Animais que precisam de um lar amoroso


# 🚀 Comece em 5 Minutos
Pré-requisitos Básicos

✅ Python 3.8+ - Baixar aqui
✅ MySQL 8.0+ - Baixar aqui
✅ Git - Baixar aqui

# 📥 Instalação Rápida (Passo a Passo)

1. 📋 Clone o Projeto
bash
git clone https://github.com/joaliny/adote-me.git
cd adote-me
2. 🏠 Crie um Ambiente Virtual (Protege seu Sistema)
bash

# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate

# 3. 📦 Instale as Dependências
bash
pip install -r requirements.txt

4. ⚙️ Configure o Banco de Dados
Primeiro, configure o MySQL:

sql
-- Abra o MySQL (MySQL Workbench ou linha de comando)
CREATE DATABASE adote_me;
CREATE USER 'adote_user'@'localhost' IDENTIFIED BY 'sua_senha_segura';
GRANT ALL PRIVILEGES ON adote_me.* TO 'adote_user'@'localhost';
FLUSH PRIVILEGES;
Depois, configure as variáveis de ambiente:

bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o arquivo .env com um editor de texto
# (Substitua pelas SUAS configurações)

5. 🗄️ Crie as Tabelas do Banco
bash
python init_db.py

6. 🎉 Execute o Sistema!
bash
python app.py

7. 🌐 Acesse no Navegador
text
http://localhost:5000

⚙️ Configuração do Ambiente
📝 Arquivo .env (Configure com SEUS dados)
env
# CONFIGURAÇÕES DO FLASK
SECRET_KEY=sua_chave_secreta_muito_segura

# CONFIGURAÇÕES DO MYSQL (USE OS MESMOS DO PASSO 4)
DB_HOST=localhost
DB_USER=adote_user
DB_PASSWORD=sua_senha_segura
DB_NAME=adote_me
DB_PORT=3306

# CONFIGURAÇÕES DE EMAIL (OPCIONAL)
EMAIL_SISTEMA=seu-email@gmail.com
SENHA_EMAIL=sua_senha_de_app

# 🗄️ Estrutura do Banco Criada
✅ usuarios - Cadastro de usuários e protetores
✅ pets - Animais disponíveis para adoção
✅ adocoes - Solicitações de adoção

🎮 Como Usar o Sistema
👤 Para Quem Quer Adotar
📝 Cadastre-se como "Adotante"

🔍 Explore animais disponíveis

💌 Envie solicitação para o pet que gostou

📞 Aguarde contato do protetor

🏢 Para Protetores/ONGs
📝 Cadastre-se como "Protetor/ONG"

🏢 Informe dados da organização

🐕 Cadastre animais para adoção

📋 Gerencie solicitações recebidas

# 🔧 Funcionalidades Principais

✅ Busca inteligente - Filtre por espécie, idade, localização
✅ Sistema seguro - Senhas criptografadas
✅ Interface responsiva - Funciona no celular e computador
✅ Processo de adoção - Do cadastro até o contato


# 📁 Estrutura do Projeto
text
adote-me/
├── 🐍 app.py                 # Aplicação principal
├── 🗄️ init_db.py            # Configura o banco de dados
├── 📋 requirements.txt       # Lista de dependências
├── 🔧 .env                  # Configurações (NÃO compartilhe!)
├── 🌐 templates/            # Páginas HTML
│   ├── base.html           # Layout principal
│   ├── home.html           # Página inicial
│   ├── cadastro_user.html  # Cadastro de usuários
│   ├── login.html          # Página de login
│   └── ...                 # Outras páginas
├── 🎨 static/              # Arquivos de estilo e imagens
│   ├── css/               # Estilos
│   └── imagens/           # Imagens do sistema
└── 📊 __pycache__/        # Arquivos temporários Python


# 🛠️ Para Desenvolvedores

🔄 Comandos Úteis
bash
# Desenvolvimento
python app.py                   # Roda o servidor
python init_db.py               # Recria o banco (cuidado!)

# Git
git status                      # Verifica mudanças
git add .                       # Prepara arquivos
git commit -m "mensagem"        # Salva mudanças
git push                        # Envia para GitHub

# 🌐 URLs Principais
Página	URL	Descrição

🏠 Início	/	Página principal
📝 Cadastro	/cadastro	Criar conta
🔐 Login	/login	Fazer login
🐕 Adotar	/adotar	Ver animais
➕ Cadastrar Pet	/cadastrar	Adicionar animal
🐛 Solução de Problemas Comuns
Erro: "Module not found"

bash
pip install -r requirements.txt
Erro: "Can't connect to MySQL"

Verifique se o MySQL está rodando

Confirme usuário/senha no .env

Erro: "Port already in use"

bash
# Use outra porta
python app.py --port 5001
🤝 Como Contribuir
Quer ajudar a melhorar o Adote-me? Siga estes passos:

🐙 Faça um Fork do projeto

🌿 Crie uma Branch: git checkout -b minha-melhoria

💾 Salve as Mudanças: git commit -m 'Adicionei nova funcionalidade'

📤 Envie: git push origin minha-melhoria

🔃 Abra um Pull Request



# 📞 Suporte e Dúvidas
Encontrou algum problema?

📚 Verifique esta documentação

🐛 Procure em Issues

❓ Crie uma Nova Issue

📄 Licença
Este projeto está sob a licença MIT. Veja o arquivo LICENSE para detalhes.

# 🎉 Próximos Passos
Agora que seu sistema está rodando:

🧪 Teste todas as funcionalidades

👥 Cadastre alguns usuários de exemplo

🐕 Adicione alguns pets

📱 Teste em diferentes dispositivos

Divirta-se ajudando animais a encontrarem um lar! 🐾💕