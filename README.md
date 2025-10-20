# 🐾 Adote-me - Sistema de Adoção de Animais
Sistema web completo para conectar animais que precisam de um lar com pessoas dispostas a adotar com responsabilidade.

# 🎯 O Que é o Adote-me? 
O Adote-me é uma plataforma web que facilita o processo de adoção de animais, conectando:

* 🏠 Pessoas interessadas em adotar um pet
* 🏢 Protetores e ONGs que resgatam animais
* 🐕 Animais que precisam de um lar amoroso


# 🚀 Pré-requisitos Básicos

✅ Python 3.11+
✅ Servidor MySQL (via XAMPP, WAMP ou nativo)
✅ Git 

# 📥 Instalação Rápida (Passo a Passo)

1. 📋 Clone o Projeto
```bash
git clone https://github.com/joaliny/adote-me.git
cd adote-me
```
3. 🏠 Crie um Ambiente Virtual (Protege seu Sistema)

* Windows
```bash
python -m venv venv
venv\Scripts\activate
```
* Linux/Mac
```bash
python3 -m venv venv
source venv/bin/activate
```

# 3. 📦 Instale as Dependências
```bash
pip install -r requirements.txt
```

# 4. ⚙️ Configura o Arquivo .env
Crie um arquivo `.env` na raiz do projeto e configure suas credenciais (com suas configurações):
```env
    # Configurações do Banco de Dados
    MYSQL_HOST=127.0.0.1
    MYSQL_PORT=3306
    MYSQL_USER=root
    MYSQL_PASSWORD=
    MYSQL_DB=adote_me

    # Chave Secreta do Flask
    FLASK_SECRET_KEY=sua-chave-secreta-aqui

    # Configurações do E-mail (Gmail)
    EMAIL_SISTEMA=seuemail@gmail.com
    SENHA_EMAIL=sua-senha-de-app-aqui

    # IMPORTANTE: Use uma Senha de App do Google, não a senha da conta.
```
    

# 4. ⚙️ Configure o Banco de Dados
Este comando cria o banco de dados, tabelas e usuários:

```bash
python init_db.py
```

# 6. 🎉 Execute o Sistema!
```bash
python app.py
```

# 7. 🌐 Acesse no Navegador
```
http://localhost:5000
```

# 📝 Link para cadastrar usuário Administrador
```
http://localhost:5000/primeiro-admin
```

# 🔧 Funcionalidades Principais

* ✅ Busca inteligente - Filtre por espécie, idade, localização
* ✅ Sistema seguro - Senhas criptografadas
* ✅ Interface responsiva - Funciona no celular e computador
* ✅ Processo de adoção - Do cadastro até o contato


# 📁 Estrutura do Projeto
```text
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
```

# 🛠️ Para Desenvolvedores

🔄 Comandos Úteis
```bash
# Desenvolvimento
python app.py                   # Roda o servidor
python init_db.py               # Recria o banco (cuidado!)

# Git
git status                      # Verifica mudanças
git add .                       # Prepara arquivos
git commit -m "mensagem"        # Salva mudanças
git push                        # Envia para GitHub
```

# 🌐 URLs Principais
Páginas	URL e	Descrição
```txt
🏠 Início	/	Página principal
📝 Cadastro	/cadastro	Criar conta
🔐 Login	/login	Fazer login
🐕 Adotar	/adotar	Ver animais
➕ Cadastrar Pet	/cadastrar	Adicionar animal
🐛 Solução de Problemas Comuns

```

* Erro: "Can't connect to MySQL"
```bash
Verifique se o MySQL está rodando
Confirme usuário/senha no .env
```

* Erro: "Port already in use"

```bash
# Use outra porta
python app.py --port 5001
```

# 🤝 Como Contribuir: Quer ajudar a melhorar o Adote-me? Siga estes passos:

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
