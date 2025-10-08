from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import requests
from dotenv import load_dotenv
import MySQLdb.cursors
from datetime import datetime
import traceback
from flask import session 
# import mysql.connector
# from mysql.connector import Error


# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)

# Configurações do MySQL (usando Flask-MySQLdb)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'adote-me'

mysql = MySQL(app)

# Configurações de upload
UPLOAD_FOLDER = 'static/imagens'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configurações de e-mail
email_sistema = os.getenv("EMAIL_SISTEMA")
senha_email = os.getenv("SENHA_EMAIL")

app.secret_key = 'sua-chave-secreta-aqui'  # Adicione esta linha


@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html', pagina='login') 


@app.route('/login-usuario', methods=['POST'])
def login_usuario():
    try:
        email = request.form['email']
        senha = request.form['senha']

        print(f"Tentativa de login: {email}")

        cur = mysql.connection.cursor()
        cur.execute("SELECT id, nome, email, senha, tipo FROM usuarios WHERE email = %s", (email,))
        usuario = cur.fetchone()
        cur.close()

        if usuario:
            senha_hash = usuario[3]
            senha_correta = check_password_hash(senha_hash, senha)
            
            if senha_correta:
                # ⭐⭐ CRIAR SESSÃO DO USUÁRIO ⭐⭐
                session['usuario_id'] = usuario[0]
                session['usuario_nome'] = usuario[1]
                session['usuario_email'] = usuario[2]
                session['usuario_tipo'] = usuario[4]
                session['logado'] = True
                
                # ⭐⭐ DEBUG DA SESSÃO CRIADA ⭐⭐
                print("=== SESSÃO CRIADA ===")
                print(f"Session após login: {dict(session)}")
                
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('home'))
            else:
                flash('Email ou senha incorretos.', 'error')
                return redirect(url_for('login'))
        else:
            flash('Email ou senha incorretos.', 'error')
            return redirect(url_for('login'))

    except Exception as e:
        print(f"ERRO NO LOGIN: {str(e)}")
        flash('Erro interno no servidor.', 'error')
        return redirect(url_for('login'))


@app.route('/cadastro', methods=['GET'])
def cadastro():
    return render_template('cadastro_user.html', pagina='cadastro_user')


@app.route('/cadastrar_usuario', methods=['POST'])
def cadastrar_usuario():
    try:
        print("=== INICIANDO CADASTRO DE USUÁRIO ===")
        
        # Dados pessoais
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('senha')
        confirmar_senha = request.form.get('confirmar_senha')
        telefone = request.form.get('telefone')
        
        print(f"Dados recebidos: {nome}, {email}, {telefone}")
        
        # Verificar campos obrigatórios
        if not all([nome, email, senha, confirmar_senha, telefone]):
            missing = []
            if not nome: missing.append('nome')
            if not email: missing.append('email')
            if not senha: missing.append('senha')
            if not confirmar_senha: missing.append('confirmar_senha')
            if not telefone: missing.append('telefone')
            
            flash(f'Campos obrigatórios faltando: {", ".join(missing)}', 'error')
            return redirect(url_for('cadastro'))

        # Endereço
        cep = request.form.get('cep', '')
        cidade = request.form.get('cidade', '')
        endereco_completo = request.form.get('endereco', '')
        numero = request.form.get('numero', '')
        
        # Montar endereço completo
        endereco = f"{endereco_completo}, {numero}, {cidade} - CEP: {cep}" if endereco_completo else ""

        # Tipo de usuário
        tipo = 'protetor' if request.form.get('protetor') else 'adotante'
        nome_organizacao = request.form.get('nome_organizacao', '')
        cnpj = request.form.get('cnpj', '')

        print(f"Tipo: {tipo}, Organização: {nome_organizacao}")

        # Validação de senha
        if senha != confirmar_senha:
            flash('As senhas não coincidem.', 'error')
            return redirect(url_for('cadastro'))

        # Verificar se email já existe
        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        if cur.fetchone():
            flash('Este email já está cadastrado.', 'error')
            cur.close()
            return redirect(url_for('cadastro'))

        # Criptografar senha
        senha_hash = generate_password_hash(senha)
        print("Senha criptografada com sucesso")

        # Inserir no banco
        try:
            cur.execute("""
                INSERT INTO usuarios (nome, email, senha, telefone, endereco, tipo, 
                                    data_cadastro, nome_organizacao, cnpj, verificado)
                VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s, %s, %s)
            """, (nome, email, senha_hash, telefone, endereco, tipo, nome_organizacao, cnpj, 0))
            
            mysql.connection.commit()
            cur.close()
            print("Usuário inserido no banco com sucesso!")
            
        except Exception as db_error:
            print(f"ERRO NO BANCO: {str(db_error)}")
            print(f"Traceback: {traceback.format_exc()}")
            flash(f'Erro no banco de dados: {str(db_error)}', 'error')
            return redirect(url_for('cadastro'))

        flash('Usuário cadastrado com sucesso! Faça login para continuar.', 'success')
        return redirect(url_for('login'))

    except Exception as e:
        print(f"ERRO GERAL NO CADASTRO: {str(e)}")
        print(f"TRACEBACK COMPLETO: {traceback.format_exc()}")
        flash(f'Erro interno no servidor: {str(e)}', 'error')
        return redirect(url_for('cadastro'))


@app.route('/')
@app.route('/home')
def home():
    usuario = obter_usuario_atual()
    
    # Buscar pets do MySQL (sem a coluna 'disponivel')
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM pets ORDER BY id DESC LIMIT 6")
    pets_data = cur.fetchall()
    cur.close()
    
    # Formatar pets
    pets = []
    for pet in pets_data:
        pets.append({
            'id': pet[0],
            'nome': pet[1],
            'especie': pet[2],
            'idade': pet[3],
            'descricao': pet[4],
            'imagem_url': pet[5]
        })
    
    return render_template('home.html', usuario=usuario, pagina='home', pets=pets)


@app.route('/adotar')
def adotar():
    usuario = obter_usuario_atual()
    especie = request.args.get('especie')
    idade = request.args.get('idade')

    cur = mysql.connection.cursor()

    # Montar a query com filtros (sem a coluna 'disponivel')
    query = "SELECT * FROM pets WHERE 1=1"
    valores = []

    if especie:
        query += " AND especie LIKE %s"
        valores.append(f"%{especie}%")

    if idade:
        query += " AND idade <= %s"
        valores.append(idade)

    query += " ORDER BY id DESC"
    
    cur.execute(query, valores)
    pets_data = cur.fetchall()
    cur.close()

    # Formatar pets
    pets = []
    for pet in pets_data:
        pets.append({
            'id': pet[0],
            'nome': pet[1],
            'especie': pet[2],
            'idade': pet[3],
            'descricao': pet[4],
            'imagem_url': pet[5]
        })

    return render_template('adotar.html', pets=pets, pagina='adotar', usuario=usuario)


@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    usuario = obter_usuario_atual()

    if request.method == 'POST':
        nome = request.form['nome']
        especie = request.form['especie']
        idade = request.form['idade']
        descricao = request.form['descricao']

        imagem = request.files['imagem']
        if imagem.filename != '':
            nome_arquivo = secure_filename(imagem.filename)
            caminho_imagem = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)
            imagem.save(caminho_imagem)
            imagem_url = f"/static/imagens/{nome_arquivo}"
        else:
            imagem_url = ''

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO pets (nome, especie, idade, descricao, imagem_url) VALUES (%s, %s, %s, %s, %s)",
                    (nome, especie, idade, descricao, imagem_url))
        mysql.connection.commit()
        cur.close()

        return redirect('/home')

    return render_template('cadastrar.html', pagina='cadastrar', usuario=usuario)


@app.route('/adotar/<int:id>', methods=['POST'])
def solicitar_adocao(id):
    try:
        print("=== INICIANDO SOLICITAÇÃO DE ADOÇÃO ===")
        
        # Pegar dados do formulário
        nome = request.form.get('nome')
        email = request.form.get('email')
        telefone = request.form.get('telefone')
        mensagem = request.form.get('mensagem')

        print(f"Dados recebidos: {nome}, {email}, {telefone}, {mensagem}")

        # Verificar se todos os campos foram preenchidos
        if not all([nome, email, telefone, mensagem]):
            missing = []
            if not nome: missing.append('nome')
            if not email: missing.append('email')
            if not telefone: missing.append('telefone')
            if not mensagem: missing.append('mensagem')
            
            print(f"Campos faltando: {missing}")
            flash('Todos os campos são obrigatórios.', 'error')
            return redirect(url_for('detalhes_pet', id=id))

        print(f"Solicitação de adoção: Pet {id}, Por: {nome}")

        cur = mysql.connection.cursor()
        
        # ✅ CORREÇÃO: Criar tabela adocoes de forma mais simples (sem foreign key primeiro)
        try:
            cur.execute("""
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
            """)
            mysql.connection.commit()
            print("✅ Tabela adocoes verificada/criada com sucesso")
        except Exception as table_error:
            print(f"❌ Erro ao criar tabela: {table_error}")
            # Tentar versão mais simples sem status
            try:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS adocoes (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        pet_id INT NOT NULL,
                        nome VARCHAR(100) NOT NULL,
                        email VARCHAR(100) NOT NULL,
                        telefone VARCHAR(20) NOT NULL,
                        mensagem TEXT NOT NULL,
                        data_solicitacao DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                mysql.connection.commit()
                print("✅ Tabela adocoes criada (versão simplificada)")
            except Exception as simple_error:
                print(f"❌ Erro ao criar tabela simplificada: {simple_error}")
                flash('Erro no banco de dados.', 'error')
                return redirect(url_for('detalhes_pet', id=id))

        # Salvar no banco - VERSÃO SIMPLIFICADA
        try:
            # Primeiro, verificar se o pet existe
            cur.execute("SELECT id FROM pets WHERE id = %s", (id,))
            pet_existe = cur.fetchone()
            
            if not pet_existe:
                print(f"❌ Pet com ID {id} não existe")
                flash('Pet não encontrado.', 'error')
                return redirect(url_for('detalhes_pet', id=id))
            
            # Inserir a solicitação
            cur.execute("""
                INSERT INTO adocoes (pet_id, nome, email, telefone, mensagem) 
                VALUES (%s, %s, %s, %s, %s)
            """, (id, nome, email, telefone, mensagem))
            
            mysql.connection.commit()
            print("✅ Solicitação salva no banco com sucesso!")
            
        except Exception as insert_error:
            print(f"❌ Erro ao salvar no banco: {insert_error}")
            mysql.connection.rollback()
            
            # Tentar versão alternativa sem telefone
            try:
                cur.execute("""
                    INSERT INTO adocoes (pet_id, nome, email, mensagem) 
                    VALUES (%s, %s, %s, %s)
                """, (id, nome, email, mensagem))
                mysql.connection.commit()
                print("✅ Solicitação salva (sem telefone)")
            except Exception as alt_error:
                print(f"❌ Erro na inserção alternativa: {alt_error}")
                flash('Erro ao salvar solicitação no banco.', 'error')
                return redirect(url_for('detalhes_pet', id=id))

        # Buscar dados do pet para exibição
        try:
            cur.execute("SELECT * FROM pets WHERE id = %s", (id,))
            pet = cur.fetchone()
            cur.close()
            
            if pet:
                pet_detalhado = {
                    'id': pet[0],
                    'nome': pet[1],
                    'especie': pet[2],
                    'idade': pet[3],
                    'descricao': pet[4],
                    'imagem_url': pet[5]
                }
                print(f"Pet encontrado: {pet_detalhado['nome']}")
            else:
                print("❌ Pet não encontrado após inserção")
                flash('Erro ao buscar informações do pet.', 'error')
                return redirect(url_for('adotar'))
                
        except Exception as pet_error:
            print(f"Erro ao buscar pet: {pet_error}")
            cur.close()

        # Tentar enviar e-mail (opcional)
        try:
            assunto_adotante = "Confirmação de solicitação de adoção - Adote-me"
            corpo_adotante = f"""
            Olá {nome},

            Recebemos sua solicitação para adotar o pet {pet_detalhado['nome']}. 
            Em breve entraremos em contato com mais informações.

            📋 Detalhes da sua solicitação:
            • Pet: {pet_detalhado['nome']} ({pet_detalhado['especie']}, {pet_detalhado['idade']} anos)
            • Sua mensagem: {mensagem}
            • Seu telefone: {telefone}

            Aguarde nosso contato em até 48 horas.

            Obrigado por escolher adotar com responsabilidade! 🐾

            Atenciosamente,
            Equipe Adote-me
            """

            enviar_email(email, assunto_adotante, corpo_adotante)
            print("✅ E-mail enviado com sucesso!")
            
        except Exception as email_error:
            print(f"⚠️ Erro ao enviar e-mail: {email_error}")

        # ✅ Sucesso
        print("🎉 Solicitação processada com sucesso!")
        return redirect(url_for('detalhes_pet', id=id, sucesso=True, nome=nome))

    except Exception as e:
        print(f"❌ ERRO GERAL NA SOLICITAÇÃO: {str(e)}")
        import traceback
        print(f"TRACEBACK: {traceback.format_exc()}")
        flash('Erro interno ao processar solicitação. Tente novamente.', 'error')
        return redirect(url_for('detalhes_pet', id=id))


# E atualize a rota detalhes_pet para receber o parâmetro
@app.route('/pet/<int:id>')
def detalhes_pet(id):
    usuario = obter_usuario_atual() 
    sucesso = request.args.get('sucesso', False)
    nome = request.args.get('nome', '')
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM pets WHERE id = %s", (id,))
    pet = cur.fetchone()
    cur.close()

    if pet:
        pet_detalhado = {
            'id': pet[0],
            'nome': pet[1],
            'especie': pet[2],
            'idade': pet[3],
            'descricao': pet[4],
            'imagem_url': pet[5]
        }
        return render_template('detalhes_pet.html', 
                             pet=pet_detalhado, 
                             pagina='detalhes_pet',
                             mostrar_modal=sucesso,
                             nome=nome,
                             usuario=usuario)
    else:
        return "Pet não encontrado", 404


def enviar_email(destinatario, assunto, corpo, remetente='joalinyfurtado87@gmail.com', senha='lfhykuryoifmstep'):
    try:
        print(f"📧 Tentando enviar email para: {destinatario}")
        
        msg = MIMEMultipart()
        msg['From'] = remetente
        msg['To'] = destinatario
        msg['Subject'] = assunto
        msg.attach(MIMEText(corpo, 'plain'))

        servidor = smtplib.SMTP('smtp.gmail.com', 587)
        servidor.starttls()
        servidor.login(remetente, senha)
        servidor.send_message(msg)
        servidor.quit()
        
        print(f"✅ E-mail enviado com sucesso para {destinatario}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail: {e}")
        return False


@app.route('/ia-dicas', methods=['POST'])
def ia_dicas():
    data = request.get_json()
    pergunta = data.get('pergunta', '')

    try:
        resposta = requests.post("http://localhost:11434/api/generate", json={
            "model": "phi",
            "prompt": f"Responda em português do Brasil: {pergunta}",
            "stream": False
        })

        texto = resposta.json().get("response", "Erro ao gerar resposta.")
        return jsonify({'resposta': texto})
    except Exception as e:
        return jsonify({'resposta': f"Erro ao gerar resposta: {str(e)}"})


# Função para obter usuário atual - ADICIONE ISSO
def obter_usuario_atual():
    """Retorna os dados do usuário logado ou None se não estiver logado"""
    if 'logado' in session and session['logado']:
        return {
            'id': session.get('usuario_id'),
            'nome': session.get('usuario_nome'),
            'email': session.get('usuario_email'),
            'tipo': session.get('usuario_tipo')
        }
    return None


@app.route('/logout')
def logout():
    # Limpar a sessão
    session.clear()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('home'))


@app.route('/criar-admin-teste')
def criar_admin_teste():
    try:
        cur = mysql.connection.cursor()
        
        # Senha simples para teste
        senha = "123"
        senha_hash = generate_password_hash(senha)

        # Deletar se já existir
        cur.execute("DELETE FROM usuarios WHERE email = 'admin@teste.com'")

        # Inserir admin
        cur.execute("""
            INSERT INTO usuarios (nome, email, senha, tipo, telefone, data_cadastro, verificado) 
            VALUES (%s, %s, %s, %s, %s, NOW(), %s)
        """, ('Admin Teste', 'admin@teste.com', senha_hash, 'admin', '(92) 98888-8888', 1))

        mysql.connection.commit()
        cur.close()

        return """
        <h1>✅ Admin criado com sucesso!</h1>
        <p><strong>Email:</strong> admin@teste.com</p>
        <p><strong>Senha:</strong> 123</p>
        <p><a href="/login">Fazer login agora</a></p>
        """
    except Exception as e:
        return f"Erro: {str(e)}"


# ========== ROTAS DO DASHBOARD ==========

# @app.route('/admin')
# def admin_dashboard():
#     usuario = obter_usuario_atual()
#     if not usuario or usuario['tipo'] != 'admin':
#         flash('Acesso restrito a administradores.', 'error')
#         return redirect(url_for('login'))

#     return render_template('admin_dashboard.html', usuario=usuario, pagina='admin')

# @app.route('/admin/protetores')
# def admin_protetores():
#     usuario = obter_usuario_atual()
#     if not usuario or usuario['tipo'] != 'admin':
#         flash('Acesso restrito a administradores.', 'error')
#         return redirect(url_for('login'))

#     return "Página de Gerenciar Protetores - Em desenvolvimento"

# @app.route('/protetor')
# def protetor_dashboard():
#     usuario = obter_usuario_atual()
#     if not usuario or usuario['tipo'] != 'protetor':
#         flash('Acesso restrito a protetores.', 'error')
#         return redirect(url_for('login'))

#     return render_template('protetor_dashboard.html', usuario=usuario, pagina='protetor')

# @app.route('/minha-conta')
# def minha_conta():
#     usuario = obter_usuario_atual()
#     if not usuario:
#         flash('Faça login para acessar sua conta.', 'error')
#         return redirect(url_for('login'))

#     return render_template('minha_conta.html', usuario=usuario, pagina='minha-conta')


@app.route('/admin')
def admin_dashboard():
    usuario = obter_usuario_atual()
    if not usuario or usuario['tipo'] != 'admin':
        flash('Acesso restrito a administradores.', 'error')
        return redirect(url_for('login'))
    
    try:
        cur = mysql.connection.cursor()
        
        # Buscar estatísticas em tempo real
        cur.execute("SELECT COUNT(*) FROM usuarios")
        total_usuarios = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM usuarios WHERE tipo = 'protetor'")
        total_protetores = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM pets")
        total_pets = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM adocoes")
        total_adocoes = cur.fetchone()[0]
        
        cur.close()
        
        return render_template('admin_dashboard.html', 
                             usuario=usuario, 
                             pagina='admin',
                             total_usuarios=total_usuarios,
                             total_protetores=total_protetores,
                             total_pets=total_pets,
                             total_adocoes=total_adocoes)
                             
    except Exception as e:
        print(f"❌ Erro no dashboard admin: {e}")
        # Se der erro, retorna sem estatísticas
        return render_template('admin_dashboard.html', 
                             usuario=usuario, 
                             pagina='admin',
                             total_usuarios=0,
                             total_protetores=0,
                             total_pets=0,
                             total_adocoes=0)

@app.route('/admin/protetores')
def admin_protetores():
    usuario = obter_usuario_atual()
    if not usuario or usuario['tipo'] != 'admin':
        flash('Acesso restrito a administradores.', 'error')
        return redirect(url_for('login'))
    
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT id, nome, email, telefone, nome_organizacao, cnpj, data_cadastro, verificado 
            FROM usuarios 
            WHERE tipo = 'protetor' 
            ORDER BY data_cadastro DESC
        """)
        protetores_data = cur.fetchall()
        cur.close()
        
        # Formatar dados
        protetores = []
        for protetor in protetores_data:
            protetores.append({
                'id': protetor[0],
                'nome': protetor[1],
                'email': protetor[2],
                'telefone': protetor[3] or 'Não informado',
                'nome_organizacao': protetor[4] or 'Não informado',
                'cnpj': protetor[5] or 'Não informado',
                'data_cadastro': protetor[6].strftime('%d/%m/%Y') if protetor[6] else 'N/A',
                'verificado': '✅' if protetor[7] else '❌'
            })
        
        return render_template('admin_protetores.html', 
                             usuario=usuario, 
                             pagina='admin',
                             protetores=protetores)
                             
    except Exception as e:
        print(f"❌ Erro ao carregar protetores: {e}")
        flash('Erro ao carregar lista de protetores.', 'error')
        return render_template('admin_protetores.html', 
                             usuario=usuario, 
                             pagina='admin',
                             protetores=[])

# Adicione estas novas rotas
@app.route('/admin/pets')
def admin_pets():
    usuario = obter_usuario_atual()
    if not usuario or usuario['tipo'] != 'admin':
        flash('Acesso restrito a administradores.', 'error')
        return redirect(url_for('login'))
    
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT p.id, p.nome, p.especie, p.idade, p.descricao, p.imagem_url, 
                   u.nome as protetor_nome, p.data_cadastro 
            FROM pets p 
            LEFT JOIN usuarios u ON p.usuario_id = u.id 
            ORDER BY p.data_cadastro DESC
        """)
        pets_data = cur.fetchall()
        cur.close()
        
        pets = []
        for pet in pets_data:
            pets.append({
                'id': pet[0],
                'nome': pet[1],
                'especie': pet[2],
                'idade': pet[3],
                'descricao': pet[4] or 'Sem descrição',
                'imagem_url': pet[5] or '/static/imagens/pet-default.jpg',
                'protetor_nome': pet[6] or 'Sistema',
                'data_cadastro': pet[7].strftime('%d/%m/%Y') if pet[7] else 'N/A'
            })
        
        return render_template('admin_pets.html', 
                             usuario=usuario, 
                             pagina='admin',
                             pets=pets)
                             
    except Exception as e:
        print(f"❌ Erro ao carregar pets: {e}")
        flash('Erro ao carregar lista de pets.', 'error')
        return render_template('admin_pets.html', 
                             usuario=usuario, 
                             pagina='admin',
                             pets=[])

@app.route('/admin/relatorios')
def admin_relatorios():
    usuario = obter_usuario_atual()
    if not usuario or usuario['tipo'] != 'admin':
        flash('Acesso restrito a administradores.', 'error')
        return redirect(url_for('login'))
    
    try:
        cur = mysql.connection.cursor()
        
        # Estatísticas para relatórios
        cur.execute("SELECT COUNT(*) FROM usuarios WHERE tipo = 'adotante'")
        total_adotantes = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM adocoes WHERE status = 'pendente' OR status IS NULL")
        adocoes_pendentes = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM adocoes WHERE status = 'aprovada'")
        adocoes_aprovadas = cur.fetchone()[0]
        
        cur.execute("""
            SELECT especie, COUNT(*) as total 
            FROM pets 
            GROUP BY especie 
            ORDER BY total DESC
        """)
        especies_stats = cur.fetchall()
        
        cur.close()
        
        # Formatar estatísticas de espécies
        especies_formatadas = []
        for especie in especies_stats:
            especies_formatadas.append({
                'especie': especie[0],
                'total': especie[1]
            })
        
        return render_template('admin_relatorios.html', 
                             usuario=usuario, 
                             pagina='admin',
                             total_adotantes=total_adotantes,
                             adocoes_pendentes=adocoes_pendentes,
                             adocoes_aprovadas=adocoes_aprovadas,
                             especies_stats=especies_formatadas)
                             
    except Exception as e:
        print(f"❌ Erro ao carregar relatórios: {e}")
        flash('Erro ao carregar relatórios.', 'error')
        return render_template('admin_relatorios.html', 
                             usuario=usuario, 
                             pagina='admin',
                             total_adotantes=0,
                             adocoes_pendentes=0,
                             adocoes_aprovadas=0,
                             especies_stats=[])

@app.route('/admin/configuracoes')
def admin_configuracoes():
    usuario = obter_usuario_atual()
    if not usuario or usuario['tipo'] != 'admin':
        flash('Acesso restrito a administradores.', 'error')
        return redirect(url_for('login'))
    
    return render_template('admin_configuracoes.html', 
                         usuario=usuario, 
                         pagina='admin')

# Suas rotas existentes (mantenha estas)
@app.route('/protetor')
def protetor_dashboard():
    usuario = obter_usuario_atual()
    if not usuario or usuario['tipo'] != 'protetor':
        flash('Acesso restrito a protetores.', 'error')
        return redirect(url_for('login'))
    
    return render_template('protetor_dashboard.html', usuario=usuario, pagina='protetor')

@app.route('/minha-conta')
def minha_conta():
    usuario = obter_usuario_atual()
    if not usuario:
        flash('Faça login para acessar sua conta.', 'error')
        return redirect(url_for('login'))
    
    return render_template('minha_conta.html', usuario=usuario, pagina='minha-conta')


@app.route('/sobre')
def sobre():
    usuario = obter_usuario_atual()
    return render_template('sobre.html', usuario=usuario)


@app.route("/termos")
def termos():
    referer = request.headers.get("Referer")
    return render_template("termos.html", pagina="termos", referer=referer)


@app.route("/privacidade")
def privacidade():
    referer = request.headers.get("Referer")
    return render_template("privacidade.html", pagina="privacidade", referer=referer)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
