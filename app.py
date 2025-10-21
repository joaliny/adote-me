from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, current_app, g
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import traceback
import MySQLdb  
from itsdangerous import URLSafeTimedSerializer # senha
from unidecode import unidecode #blog
import re #blog
import google.generativeai as genai #geminiIA

# ===================== CARREGAR .ENV =====================
load_dotenv()

app = Flask(__name__)

# ===================== CONFIGURAÇÕES MYSQL =====================
def env(key, default=None):
    v = os.getenv(key)
    return v if v is not None and (v != "" or default is None) else default

app.config.update({
    "MYSQL_HOST": env("MYSQL_HOST", "127.0.0.1"),
    "MYSQL_PORT": int(env("MYSQL_PORT", "3306")),
    "MYSQL_USER": env("MYSQL_USER", "root"),
    "MYSQL_PASSWORD": env("MYSQL_PASSWORD", ""),
    "MYSQL_DB": env("MYSQL_DB", "adote-me"),
})

# Chave de sessão
app.secret_key = env("FLASK_SECRET_KEY", "sua-chave-secreta-aqui")
RESET_PASSWORD_SALT = 'reset-password-token' #Serializador para gerar tokens temporários e seguros
s = URLSafeTimedSerializer(app.secret_key)

# Extensão (iremos usar fallback se connection vier None)
mysql = MySQL(app)

# ===================== UPLOAD & E-MAIL =====================
UPLOAD_FOLDER = "static/imagens"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

email_sistema = env("EMAIL_SISTEMA", "meunovoamigopet.site@gmail.com")
senha_email = env("SENHA_EMAIL", "xlve lohz goev txxt")

# ===================== DB HELPERS (com fallback) =====================
def _db_cfg():
    return {
        "host": app.config["MYSQL_HOST"],
        "user": app.config["MYSQL_USER"],
        "passwd": app.config["MYSQL_PASSWORD"],
        "db": app.config["MYSQL_DB"],
        "port": int(app.config["MYSQL_PORT"]),
        "charset": "utf8mb4",
        "use_unicode": True,
    }

def _get_conn():
    """
    1) tenta usar a conexão da extensão (mysql.connection);
    2) se for None ou falhar, conecta direto via MySQLdb.
    Reaproveita a conexão por request usando flask.g.
    """
    conn = getattr(g, "_db_conn", None)
    if conn:
        return conn

    # 1) tentar via extensão
    try:
        ext_conn = getattr(mysql, "connection", None)
        if ext_conn is not None:
            test_cur = ext_conn.cursor()
            test_cur.execute("SELECT 1")
            test_cur.close()
            g._db_conn = ext_conn
            return ext_conn
    except Exception:
        pass  # cai para o fallback

    # 2) fallback direto
    cfg = _db_cfg()
    conn = MySQLdb.connect(**cfg)
    g._db_conn = conn
    return conn

def get_cursor():
    conn = _get_conn()
    return conn.cursor()

@app.teardown_appcontext
def _close_conn(exc):
    conn = getattr(g, "_db_conn", None)
    if conn:
        try:
            conn.close()
        except Exception:
            pass
        finally:
            g._db_conn = None

def slugify(text):
    """Cria um slug amigável a partir de um texto.""" #blog
    if not text:
        return ""
    # 1. Converte caracteres especiais (acentos)
    text = unidecode(text).lower()
    # 2. Remove caracteres não alfanuméricos (mantendo espaços e hífens)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    # 3. Substitui espaços e hífens múltiplos por um único hífen
    text = re.sub(r'[-\s]+', '-', text).strip('-')
    return text

# ===================== SESSÃO/EMAIL HELPERS =====================
def obter_usuario_atual():
    try:
        if session.get("logado"):
            return {
                "id": session.get("usuario_id"),
                "nome": session.get("usuario_nome"),
                "email": session.get("usuario_email"),
                "tipo": session.get("usuario_tipo"),
            }
        return None
    except Exception:
        return None

def enviar_email(destinatario, assunto, corpo, remetente=None, senha=None):
    remetente = remetente or email_sistema
    senha = senha or senha_email
    try:
        msg = MIMEMultipart()
        msg["From"] = remetente
        msg["To"] = destinatario
        msg["Subject"] = assunto
        msg.attach(MIMEText(corpo, "plain"))

        smtp = smtplib.SMTP("smtp.gmail.com", 587)
        smtp.starttls()
        smtp.login(remetente, senha)
        smtp.send_message(msg)
        smtp.quit()
        return True
    except Exception as e:
        current_app.logger.warning(f"Erro ao enviar e-mail: {e}")
        return False



# ===================== ROTAS – AUTENTICAÇÃO =====================
@app.route("/login", methods=["GET", "POST"])
def login():
    return render_template("login.html", pagina="login")

#ROTA DE LOGIN DO USUARIO
@app.route("/login-usuario", methods=["POST"])
def login_usuario():
    try:
        email = request.form["email"]
        senha = request.form["senha"]

        cur = get_cursor()
        cur.execute("SELECT id, nome, email, senha, tipo FROM usuarios WHERE email = %s", (email,))
        usuario = cur.fetchone()
        cur.close()

        if usuario and check_password_hash(usuario[3], senha):
            # 1. Configurar Sessão
            session["usuario_id"] = usuario[0]
            session["usuario_nome"] = usuario[1]
            session["usuario_email"] = usuario[2]
            session["usuario_tipo"] = usuario[4]
            session["logado"] = True
            flash("Login realizado com sucesso!", "success")
            
            # 2. Redirecionamento Inteligente
            tipo = usuario[4]
            if tipo == 'admin':
                return redirect(url_for("admin_dashboard"))
            elif tipo == 'protetor':
                return redirect(url_for("protetor_dashboard"))
            else:
                return redirect(url_for("home"))
        
        # Se o login falhar (fora do bloco 'if')
        flash("Email ou senha incorretos.", "error")
        return redirect(url_for("login"))

    except Exception as e:
        current_app.logger.error(f"ERRO NO LOGIN: {e}")
        flash("Erro interno no servidor.", "error")
        return redirect(url_for("login"))
    

@app.route("/minha-conta", methods=["GET", "POST"])
def minha_conta():
    usuario = obter_usuario_atual()
    if not usuario:
        flash("Faça login para acessar sua conta.", "error")
        return redirect(url_for("login"))

    cur = get_cursor()

    if request.method == "POST":
        # === Lógica de Atualização (POST) ===
        try:
            nome = request.form.get("nome").strip()
            telefone = request.form.get("telefone", "").strip()
            endereco = request.form.get("endereco", "").strip()
            
            # Campos opcionais para Protetor/Admin
            nome_organizacao = request.form.get("nome_organizacao", "").strip()
            cnpj = request.form.get("cnpj", "").strip()

            if not nome:
                flash("O nome é obrigatório.", "error")
                return redirect(url_for("minha_conta"))
            
            # Atualiza os dados no banco
            cur.execute(
                """
                UPDATE usuarios SET 
                nome = %s, telefone = %s, endereco = %s, 
                nome_organizacao = %s, cnpj = %s
                WHERE id = %s
                """,
                (nome, telefone, endereco, nome_organizacao, cnpj, usuario["id"]),
            )
            _get_conn().commit()
            
            # Atualiza a sessão (apenas nome, pois email/tipo não mudam aqui)
            session["usuario_nome"] = nome
            
            flash("Informações da conta atualizadas com sucesso!", "success")
            return redirect(url_for("minha_conta"))

        except Exception as e:
            current_app.logger.error(f"ERRO AO ATUALIZAR CONTA: {e}")
            flash("Erro interno ao atualizar a conta.", "error")
            return redirect(url_for("minha_conta"))

    # === Lógica de Exibição (GET) ===
    # Busca todos os dados atuais do usuário no DB para preencher o formulário
    cur.execute(
        "SELECT id, nome, email, telefone, endereco, tipo, nome_organizacao, cnpj FROM usuarios WHERE id = %s",
        (usuario["id"],)
    )
    dados_db = cur.fetchone()
    cur.close()

    if not dados_db:
        session.clear() # Limpa a sessão se o usuário não for encontrado
        flash("Sessão inválida. Faça login novamente.", "error")
        return redirect(url_for("login"))
    
    # Prepara os dados para o template
    dados_usuario = {
        "id": dados_db[0],
        "nome": dados_db[1],
        "email": dados_db[2],
        "telefone": dados_db[3] or "",
        "endereco": dados_db[4] or "",
        "tipo": dados_db[5],
        "nome_organizacao": dados_db[6] or "",
        "cnpj": dados_db[7] or "",
    }
    
    return render_template("minha_conta.html", usuario=dados_usuario, pagina="minha-conta")


# ===================== ROTAS – RECUPERAR SENHA  =====================
@app.route('/recuperar-senha', methods=['GET'])
def recuperar_senha_form():
    """ Exibe o formulário para o usuário digitar o e-mail """
    return render_template('recuperar_senha.html', pagina='recuperar-senha')


@app.route('/solicitar-reset-senha', methods=['POST'])
def solicitar_reset_senha():
    """ Processa o e-mail, gera o token e envia o link """
    email = request.form.get('email')
    
    if not email:
        flash('Por favor, informe um e-mail.', 'error')
        return redirect(url_for('recuperar_senha_form'))

    try:
        cur = get_cursor()
        # Busca o ID, nome e email no banco
        cur.execute("SELECT id, nome, email FROM usuarios WHERE email = %s", (email,))
        usuario = cur.fetchone()
        cur.close()

        if usuario:
            # Gerar o token de redefinição usando o ID do usuário, válido por 1 hora (3600s)
            user_id, nome, user_email = usuario
            token = s.dumps(user_id, salt=RESET_PASSWORD_SALT)
            
            # Construir o link completo para o formulário de reset
            reset_url = url_for('reset_senha_form', token=token, _external=True)
            
            assunto = "Redefinição de Senha - Adote-me"
            corpo = f"""Olá {nome},
            Você solicitou a redefinição de senha para sua conta Adote-me.
            Clique no link abaixo para criar uma nova senha:

            {reset_url}

            Este link é válido por 1 hora. Se você não solicitou esta redefinição, ignore este e-mail.

            Atenciosamente,
            Equipe Adote-me
            """
            
            if enviar_email(user_email, assunto, corpo):
                flash('Um link de redefinição de senha foi enviado para seu e-mail.', 'success')
            else:
                # Ocultar detalhes do erro para o usuário final por segurança
                flash('Ocorreu um erro ao tentar enviar o e-mail. Tente novamente mais tarde.', 'error')
        else:
            # Mensagem genérica por segurança (não diz se o e-mail existe ou não)
            flash('Se o e-mail estiver cadastrado, um link de redefinição foi enviado.', 'info')
            
    except Exception as e:
        current_app.logger.error(f"ERRO NO RESET DE SENHA (SOLICITAÇÃO): {e}")
        flash("Erro interno no servidor.", "error")
        
    return redirect(url_for('recuperar_senha_form'))


@app.route('/reset-senha/<token>', methods=['GET'])
def reset_senha_form(token):
    """ Exibe o formulário para o usuário digitar a nova senha após clicar no link do e-mail """
    try:
        # Tenta carregar o ID do usuário (verifica validade e expiração do token)
        user_id = s.loads(token, salt=RESET_PASSWORD_SALT, max_age=3600)
    except:
        flash('Link de redefinição inválido ou expirado. Por favor, solicite um novo.', 'error')
        return redirect(url_for('recuperar_senha_form'))
        
    return render_template('reset_senha_form.html', token=token, pagina='reset-senha')


@app.route('/reset-senha/<token>', methods=['POST'])
def processar_reset_senha(token):
    """ Processa a nova senha e a atualiza no banco de dados """
    try:
        # Tenta carregar o ID do usuário novamente
        user_id = s.loads(token, salt=RESET_PASSWORD_SALT, max_age=3600)
    except:
        flash('Link de redefinição inválido ou expirado.', 'error')
        return redirect(url_for('recuperar_senha_form'))

    nova_senha = request.form.get('senha')
    confirmar_senha = request.form.get('confirmar_senha')
    
    if nova_senha != confirmar_senha:
        flash('As senhas não coincidem.', 'error')
        return redirect(url_for('reset_senha_form', token=token))
    
    if len(nova_senha) < 6:
        flash('A senha deve ter no mínimo 6 caracteres.', 'error')
        return redirect(url_for('reset_senha_form', token=token))

    try:
        # Criptografa a nova senha
        hashed_password = generate_password_hash(nova_senha)
        
        # Atualiza a senha no banco de dados
        cur = get_cursor()
        cur.execute("UPDATE usuarios SET senha = %s WHERE id = %s", (hashed_password, user_id))
        _get_conn().commit()
        cur.close()
        
        flash('Sua senha foi redefinida com sucesso! Faça login.', 'success')
        return redirect(url_for('login'))

    except Exception as e:
        current_app.logger.error(f"ERRO NO RESET DE SENHA (PROCESSAMENTO): {e}")
        flash("Erro interno ao redefinir a senha. Tente novamente.", "error")
        return redirect(url_for('reset_senha_form', token=token))
# ===================== FIM DAS ROTAS DE RECUPERAR SENHA =====================



@app.route("/cadastro", methods=["GET"])
def cadastro():
    return render_template("cadastro_user.html", pagina="cadastro_user")

# ROTA DE CADASTRO DE USUARIOS

@app.route("/cadastrar_usuario", methods=["POST"])
def cadastrar_usuario():
    try:
        # 1. COLETA DE DADOS OBRIGATÓRIOS DO FORMULÁRIO
        nome = request.form.get("nome")
        email = request.form.get("email")
        senha = request.form.get("senha")
        confirmar_senha = request.form.get("confirmar_senha")
        telefone = request.form.get("telefone")
        
        # Tipo de conta selecionado no formulário
        tipo = request.form.get("tipo_conta") 
        
        # 2. TRATAMENTO E LIMPEZA DE CPF/CNPJ
        # Remove pontos, traços e barras
        cpf_raw = request.form.get("cpf", "").replace('.', '').replace('-', '').strip()
        cnpj_raw = request.form.get("cnpj", "").replace('.', '').replace('/', '').replace('-', '').strip()

        # Determina qual dado usar e qual é obrigatório
        cpf = cpf_raw if tipo in ['adotante', 'protetor'] and cpf_raw else None
        cnpj = cnpj_raw if tipo == 'ong' and cnpj_raw else None

        # 3. VALIDAÇÕES BÁSICAS
        
        # Validação de campos comuns
        if not all([nome, email, senha, confirmar_senha, telefone, tipo]):
            flash("Preencha todos os campos obrigatórios.", "error")
            return redirect(url_for("cadastro"))

        # Validação do CPF ou CNPJ obrigatório
        if (tipo == 'ong' and not cnpj) or (tipo in ['adotante', 'protetor'] and not cpf):
             flash("CPF ou CNPJ é obrigatório para este tipo de cadastro.", "error")
             return redirect(url_for("cadastro"))

        if senha != confirmar_senha:
            flash("As senhas não coincidem.", "error")
            return redirect(url_for("cadastro"))
        
        # 4. COLETA DE DADOS OPCIONAIS/COMPLEMENTARES
        
        # Endereço (Mantendo a lógica de coleta de partes)
        cep = request.form.get("cep", "")
        cidade = request.form.get("cidade", "")
        endereco_completo = request.form.get("endereco", "")
        numero = request.form.get("numero", "")
        endereco = f"{endereco_completo}, {numero}, {cidade} - CEP: {cep}" if endereco_completo else ""

        nome_organizacao = request.form.get("nome_organizacao", "") 
        # Garante que 'nome_organizacao' só é relevante se for uma ONG
        nome_organizacao = nome_organizacao if tipo == 'ong' else None

        # 5. VALIDAÇÃO DE UNICIDADE (Banco de Dados)
        cur = get_cursor()
        
        # Verifica se Email já existe
        cur.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        if cur.fetchone():
            cur.close()
            flash("Este e-mail já está cadastrado.", "error")
            return redirect(url_for("cadastro"))
            
        # Verifica CPF/CNPJ se foi fornecido
        if cpf:
            cur.execute("SELECT id FROM usuarios WHERE cpf = %s", (cpf,))
            if cur.fetchone():
                cur.close()
                flash("Este CPF já está cadastrado.", "error")
                return redirect(url_for("cadastro"))
        
        if cnpj:
            cur.execute("SELECT id FROM usuarios WHERE cnpj = %s", (cnpj,))
            if cur.fetchone():
                cur.close()
                flash("Este CNPJ já está cadastrado.", "error")
                return redirect(url_for("cadastro"))

        # 6. INSERÇÃO NO BANCO DE DADOS
        
        senha_hash = generate_password_hash(senha)
        cur.execute(
            """
            INSERT INTO usuarios (nome, email, senha, telefone, endereco, tipo, cpf, cnpj,
                                  data_cadastro, nome_organizacao, verificado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s)
            """,
            (nome, email, senha_hash, telefone, endereco, tipo, cpf, cnpj, nome_organizacao, 0),
        )
        _get_conn().commit()
        cur.close()

        flash("Usuário cadastrado com sucesso! Faça login para continuar.", "success")
        return redirect(url_for("login"))

    except Exception as e:
        current_app.logger.error(f"ERRO GERAL NO CADASTRO: {e}\n{traceback.format_exc()}")
        flash("Erro interno no servidor.", "error")
        return redirect(url_for("cadastro"))
#FIM - ROTA CADASTRO

@app.route("/logout")
def logout():
    session.clear()
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for("home"))


# ===================== ROTAS – PETS =====================
@app.route("/")
@app.route("/home")
def home():
    usuario = obter_usuario_atual()
    cur = get_cursor()
    cur.execute("SELECT * FROM pets ORDER BY id DESC LIMIT 6")
    pets_data = cur.fetchall()
    cur.close()

    pets = [
        {"id": p[0], "nome": p[1], "especie": p[2], "idade": p[3], "descricao": p[4], "imagem_url": p[5]}
        for p in pets_data
    ]
    return render_template("home.html", usuario=usuario, pagina="home", pets=pets)

@app.route("/adotar")
def adotar():
    usuario = obter_usuario_atual()
    especie = request.args.get("especie")
    idade = request.args.get("idade")

    cur = get_cursor()
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

    pets = [
        {"id": p[0], "nome": p[1], "especie": p[2], "idade": p[3], "descricao": p[4], "imagem_url": p[5]}
        for p in pets_data
    ]
    return render_template("adotar.html", pets=pets, pagina="adotar", usuario=usuario)

@app.route("/pet/<int:id>")
def detalhes_pet(id):
    usuario = obter_usuario_atual()
    sucesso = request.args.get("sucesso", False)
    nome = request.args.get("nome", "")

    cur = get_cursor()
    cur.execute("SELECT * FROM pets WHERE id = %s", (id,))
    pet = cur.fetchone()
    cur.close()
    if not pet:
        return "Pet não encontrado", 404

    pet_detalhado = {
        "id": pet[0],
        "nome": pet[1],
        "especie": pet[2],
        "idade": pet[3],
        "descricao": pet[4],
        "imagem_url": pet[5],
    }
    return render_template(
        "detalhes_pet.html",
        pet=pet_detalhado,
        pagina="detalhes_pet",
        mostrar_modal=sucesso,
        nome=nome,
        usuario=usuario,
    )

@app.route("/cadastrar", methods=["GET", "POST"])
def cadastrar():
    usuario = obter_usuario_atual()
    if request.method == "POST":
        nome = request.form["nome"]
        especie = request.form["especie"]
        idade = request.form["idade"]
        descricao = request.form["descricao"]

        imagem = request.files["imagem"]
        if imagem and imagem.filename != "":
            nome_arquivo = secure_filename(imagem.filename)
            caminho_imagem = os.path.join(app.config["UPLOAD_FOLDER"], nome_arquivo)
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
            imagem.save(caminho_imagem)
            imagem_url = f"/static/imagens/{nome_arquivo}"
        else:
            imagem_url = ""

        cur = get_cursor()
        cur.execute(
            "INSERT INTO pets (nome, especie, idade, descricao, imagem_url) VALUES (%s, %s, %s, %s, %s)",
            (nome, especie, idade, descricao, imagem_url),
        )
        _get_conn().commit()
        cur.close()

        return redirect("/home")

    return render_template("cadastrar.html", pagina="cadastrar", usuario=usuario)

@app.route("/adotar/<int:id>", methods=["POST"])
def solicitar_adocao(id):
    usuario = obter_usuario_atual()
    if not usuario:
        flash("Você precisa fazer login ou se cadastrar para solicitar adoção.", "error")
        return redirect(url_for("login"))

    try:
        telefone = request.form.get("telefone", "").strip()
        mensagem = request.form.get("mensagem", "").strip()
        if not telefone:
            flash("Informe seu telefone.", "error")
            return redirect(url_for("detalhes_pet", id=id))
        if not mensagem:
            flash("Escreva uma mensagem sobre por que deseja adotar.", "error")
            return redirect(url_for("detalhes_pet", id=id))

        cur = get_cursor()
        cur.execute("SELECT id, nome, especie, idade FROM pets WHERE id = %s", (id,))
        pet = cur.fetchone()
        if not pet:
            cur.close()
            flash("Pet não encontrado.", "error")
            return redirect(url_for("adotar"))

        pet_nome, pet_especie, pet_idade = pet[1], pet[2], pet[3]

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS adocoes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                pet_id INT NOT NULL,
                usuario_id INT,
                nome VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL,
                telefone VARCHAR(20) NOT NULL,
                mensagem TEXT NOT NULL,
                data_solicitacao DATETIME DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20) DEFAULT 'pendente'
            )
            """
        )

        cur.execute(
            "INSERT INTO adocoes (pet_id, usuario_id, nome, email, telefone, mensagem) VALUES (%s, %s, %s, %s, %s, %s)",
            (id, usuario["id"], usuario["nome"], usuario["email"], telefone, mensagem),
        )
        _get_conn().commit()
        cur.close()

        try:
            assunto = f"✅ Solicitação de adoção - {pet_nome}"
            corpo = f"""Olá {usuario['nome']}!

Sua solicitação para adotar {pet_nome} foi recebida com sucesso.

• Pet: {pet_nome} ({pet_especie}, {pet_idade} anos)
• Mensagem: {mensagem}
• Telefone: {telefone}
• Data: {datetime.now().strftime('%d/%m/%Y às %H:%M')}

Entraremos em contato em até 48 horas.

Equipe Adote-me
"""
            enviar_email(usuario["email"], assunto, corpo)
        except Exception as e:
            current_app.logger.warning(f"Falha ao enviar e-mail: {e}")

        return redirect(url_for("detalhes_pet", id=id, sucesso="true", nome=usuario["nome"]))

    except Exception as e:
        current_app.logger.error(f"ERRO GERAL NA SOLICITAÇÃO: {e}\n{traceback.format_exc()}")
        flash("Erro interno ao processar solicitação. Tente novamente.", "error")
        return redirect(url_for("detalhes_pet", id=id))


# ===================== ROTAS – ADMIN =====================

@app.route("/admin")
def admin_dashboard():
    usuario = obter_usuario_atual()
    if not usuario or usuario["tipo"] != "admin":
        flash("Acesso restrito a administradores.", "error")
        return redirect(url_for("login"))
    try:
        cur = get_cursor()
        cur.execute("SELECT COUNT(*) FROM usuarios")
        total_usuarios = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM usuarios WHERE tipo = 'protetor'")
        total_protetores = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM pets")
        total_pets = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM adocoes")
        total_adocoes = cur.fetchone()[0]
        cur.close()
        return render_template(
            "admin_dashboard.html",
            usuario=usuario,
            pagina="admin",
            total_usuarios=total_usuarios,
            total_protetores=total_protetores,
            total_pets=total_pets,
            total_adocoes=total_adocoes,
        )
    except Exception as e:
        current_app.logger.error(f"Erro no dashboard admin: {e}")
        return render_template(
            "admin_dashboard.html",
            usuario=usuario,
            pagina="admin",
            total_usuarios=0,
            total_protetores=0,
            total_pets=0,
            total_adocoes=0,
        )


@app.route("/admin/protetores")
def admin_protetores():
    usuario = obter_usuario_atual()
    if not usuario or usuario["tipo"] != "admin":
        flash("Acesso restrito a administradores.", "error")
        return redirect(url_for("login"))
    try:
        cur = get_cursor()
        cur.execute(
            """
            SELECT id, nome, email, telefone, nome_organizacao, cnpj, data_cadastro, verificado
            FROM usuarios
            WHERE tipo = 'protetor'
            ORDER BY data_cadastro DESC
            """
        )
        protetores_data = cur.fetchall()
        cur.close()

        protetores = [
            {
                "id": r[0],
                "nome": r[1],
                "email": r[2],
                "telefone": r[3] or "Não informado",
                "nome_organizacao": r[4] or "Não informado",
                "cnpj": r[5] or "Não informado",
                "data_cadastro": r[6].strftime("%d/%m/%Y") if r[6] else "N/A",
                "verificado": "✅" if r[7] else "❌",
            }
            for r in protetores_data
        ]
        return render_template("admin_protetores.html", usuario=usuario, pagina="admin", protetores=protetores)
    except Exception as e:
        current_app.logger.error(f"Erro ao carregar protetores: {e}")
        flash("Erro ao carregar lista de protetores.", "error")
        return render_template("admin_protetores.html", usuario=usuario, pagina="admin", protetores=[])


@app.route("/admin/pets")
def admin_pets():
    usuario = obter_usuario_atual()
    if not usuario or usuario["tipo"] != "admin":
        flash("Acesso restrito a administradores.", "error")
        return redirect(url_for("login"))
    try:
        cur = get_cursor()
        cur.execute(
            """
            SELECT p.id, p.nome, p.especie, p.idade, p.descricao, p.imagem_url,
                   u.nome as protetor_nome, p.data_cadastro
            FROM pets p
            LEFT JOIN usuarios u ON p.usuario_id = u.id
            ORDER BY p.data_cadastro DESC
            """
        )
        pets_data = cur.fetchall()
        cur.close()

        pets = [
            {
                "id": r[0],
                "nome": r[1],
                "especie": r[2],
                "idade": r[3],
                "descricao": r[4] or "Sem descrição",
                "imagem_url": r[5] or "/static/imagens/pet-default.jpg",
                "protetor_nome": r[6] or "Sistema",
                "data_cadastro": r[7].strftime("%d/%m/%Y") if r[7] else "N/A",
            }
            for r in pets_data
        ]
        return render_template("admin_pets.html", usuario=usuario, pagina="admin", pets=pets)
    except Exception as e:
        current_app.logger.error(f"Erro ao carregar pets: {e}")
        flash("Erro ao carregar lista de pets.", "error")
        #return render_template("admin_pets.html", usuario=usuario, pagina="admin", pets=[])
        return redirect(url_for("admin_dashboard"))


@app.route("/admin/relatorios")
def admin_relatorios():
    usuario = obter_usuario_atual()
    if not usuario or usuario["tipo"] != "admin":
        flash("Acesso restrito a administradores.", "error")
        return redirect(url_for("login"))
    try:
        cur = get_cursor()
        cur.execute("SELECT COUNT(*) FROM usuarios WHERE tipo = 'adotante'")
        total_adotantes = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM adocoes WHERE status = 'pendente' OR status IS NULL")
        adocoes_pendentes = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM adocoes WHERE status = 'aprovada'")
        adocoes_aprovadas = cur.fetchone()[0]
        cur.execute("SELECT especie, COUNT(*) as total FROM pets GROUP BY especie ORDER BY total DESC")
        especies_stats = cur.fetchall()
        cur.close()

        especies_formatadas = [{"especie": e[0], "total": e[1]} for e in especies_stats]
        return render_template(
            "admin_relatorios.html",
            usuario=usuario,
            pagina="admin",
            total_adotantes=total_adotantes,
            adocoes_pendentes=adocoes_pendentes,
            adocoes_aprovadas=adocoes_aprovadas,
            especies_stats=especies_formatadas,
        )
    except Exception as e:
        current_app.logger.error(f"Erro ao carregar relatórios: {e}")
        flash("Erro ao carregar relatórios.", "error")
        return render_template(
            "admin_relatorios.html",
            usuario=usuario,
            pagina="admin",
            total_adotantes=0,
            adocoes_pendentes=0,
            adocoes_aprovadas=0,
            especies_stats=[],
        )


@app.route("/admin/configuracoes")
def admin_configuracoes():
    usuario = obter_usuario_atual()
    if not usuario or usuario["tipo"] != "admin":
        flash("Acesso restrito a administradores.", "error")
        return redirect(url_for("login"))
    return render_template("admin_configuracoes.html", usuario=usuario, pagina="admin")

@app.route("/protetor")
def protetor_dashboard():
    usuario = obter_usuario_atual()
    if not usuario or usuario["tipo"] != "protetor":
        flash("Acesso restrito a protetores.", "error")
        return redirect(url_for("login"))
    return render_template("protetor_dashboard.html", usuario=usuario, pagina="protetor")


@app.route("/admin/blog/nova", methods=["GET", "POST"])
def admin_nova_postagem():
    usuario = obter_usuario_atual()
    # 1. Verifica permissão
    if not usuario or usuario["tipo"] not in ["admin", "protetor"]:
        flash("Acesso restrito.", "error")
        return redirect(url_for("login"))
    
    if request.method == "POST":
        try:
            autor_id = usuario["id"]
            titulo = request.form["titulo"].strip()
            subtitulo = request.form.get("subtitulo", "").strip()
            conteudo = request.form["conteudo"].strip()
            categoria = request.form["categoria"].strip()
            # imagem_url (removido daqui)
            
            if not all([titulo, conteudo, categoria]):
                flash("Título, Conteúdo e Categoria são obrigatórios.", "error")
                return redirect(url_for("admin_nova_postagem"))

            # === NOVO CÓDIGO PARA PROCESSAR A IMAGEM ===
            imagem_url = ""
            imagem_capa = request.files.get("imagem_capa")
            
            if imagem_capa and imagem_capa.filename != '':
                # Cria um nome de arquivo seguro
                nome_arquivo = secure_filename(imagem_capa.filename)
                
                # Definir um subdiretório para blog, se desejar, para organizar
                BLOG_UPLOAD_FOLDER = os.path.join(app.config["UPLOAD_FOLDER"], "blog")
                
                # Garante que o diretório exista
                os.makedirs(BLOG_UPLOAD_FOLDER, exist_ok=True)
                
                # Salva a imagem no novo subdiretório
                caminho_imagem = os.path.join(BLOG_UPLOAD_FOLDER, nome_arquivo)
                imagem_capa.save(caminho_imagem)
                
                # URL pública da imagem
                imagem_url = f"/static/imagens/blog/{nome_arquivo}"


            # Cria o slug (Mantenha a função slugify e importações)
            slug = slugify(titulo)

            # Salva no DB
            cur = get_cursor()
            cur.execute(
                """
                INSERT INTO postagens (titulo, subtitulo, conteudo, imagem_url, autor_id, categoria, slug)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (titulo, subtitulo, conteudo, imagem_url, autor_id, categoria, slug)
            )
            _get_conn().commit()
            cur.close()

            flash("Postagem criada com sucesso!", "success")
            return redirect(url_for("post_detalhe", slug=slug)) # Redireciona para o post
            
        except Exception as e:
            current_app.logger.error(f"ERRO AO CRIAR POST: {e}")
            flash("Erro ao salvar postagem.", "error")
            return redirect(url_for("admin_nova_postagem"))
    
    # Renderiza o formulário (GET)
    return render_template("admin_nova_postagem.html", usuario=usuario, pagina="admin")



# ===================== UTILITÁRIOS =====================

@app.route("/criar-admin-teste")
def criar_admin_teste():
    try:
        cur = get_cursor()
        senha_hash = generate_password_hash("123")
        cur.execute("DELETE FROM usuarios WHERE email = 'admin@teste.com'")
        cur.execute(
            """
            INSERT INTO usuarios (nome, email, senha, tipo, telefone, data_cadastro, verificado)
            VALUES (%s, %s, %s, %s, %s, NOW(), %s)
            """,
            ("Admin Teste", "admin@teste.com", senha_hash, "admin", "(92) 98888-8888", 1),
        )
        _get_conn().commit()
        cur.close()
        return """
        <h1>✅ Admin criado com sucesso!</h1>
        <p><strong>Email:</strong> admin@teste.com</p>
        <p><strong>Senha:</strong> 123</p>
        <p><a href="/login">Fazer login agora</a></p>
        """
    except Exception as e:
        return f"Erro: {str(e)}"


#ROTA DE DICAS COM A IA DO GEMINI

@app.route("/ia-dicas", methods=["POST"])
def ia_dicas():
    data = request.get_json()
    pergunta = data.get("pergunta", "")
    
    try:
        # 1. Configurar a chave API (Essa linha é essencial e está correta!)
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

        # 2. Chamar a API usando o objeto 'genai' diretamente (CORREÇÃO AQUI)
        # Antigo: response = client.models.generate_content(...)
        response = genai.GenerativeModel('gemini-2.5-flash').generate_content(
            contents=[f"Responda em português do Brasil e foque em dicas de cuidado para pets: {pergunta}"],
        )
        
        # 3. Processar a resposta
        texto = response.text
        return jsonify({"resposta": texto})
        
    except Exception as e:
        current_app.logger.error(f"ERRO API GEMINI: {e}")
        return jsonify({
            "resposta": f"Erro ao gerar resposta da IA. Detalhe: {str(e)}"
        })

# ROTA SOBRE

@app.route("/sobre")
def sobre():
    usuario = obter_usuario_atual()
    return render_template("sobre.html", usuario=usuario)


@app.route("/blog")
def blog():
    usuario = obter_usuario_atual()
    cur = get_cursor()
    posts = []
    
    # Parâmetros de Filtro/Busca
    search_query = request.args.get("q", "").strip()
    category_filter = request.args.get("categoria", "").strip()
    
    # 1. Definir a Consulta SQL Base
    query = """
        SELECT 
            p.id, p.titulo, p.subtitulo, p.conteudo, p.imagem_url, 
            p.data_publicacao, p.slug, u.nome as autor_nome, p.categoria
        FROM postagens p
        JOIN usuarios u ON p.autor_id = u.id
        WHERE 1=1
    """
    valores = []

    # 2. Adicionar Filtro de Categoria
    if category_filter:
        query += " AND p.categoria = %s"
        valores.append(category_filter)
        
    # 3. Adicionar Filtro de Busca (Título e Conteúdo)
    if search_query:
        # Use LIKE para buscar no título OU no conteúdo
        query += " AND (p.titulo LIKE %s OR p.conteudo LIKE %s)"
        valores.append(f"%{search_query}%")
        valores.append(f"%{search_query}%")

    # 4. Ordenação (Mais recentes primeiro)
    query += " ORDER BY p.data_publicacao DESC"

    try:
        cur.execute(query, valores)
        posts_data = cur.fetchall()
        
        for row in posts_data:
            resumo = row[3][:250] + "..." if len(row[3]) > 250 else row[3]
            
            #Verifica se a data de publicação (row[5]) não é None
            data_publicacao = row[5]
            data_formatada = data_publicacao.strftime('%d de %B, %Y') if data_publicacao else 'N/A'
            
            posts.append({
                "id": row[0],
                "titulo": row[1],
                "subtitulo": row[2],
                "resumo": resumo,
                "imagem_url": row[4],
                "data_publicacao": data_formatada, # Usa a data formatada segura
                "slug": row[6],
                "autor_nome": row[7],
                "categoria": row[8],
            })
            
    except Exception as e:
        current_app.logger.error(f"ERRO AO CARREGAR LISTA DO BLOG: {e}")
        flash("Não foi possível carregar as postagens no momento.", "error")
        return redirect(url_for("home"))
    finally:
        cur.close()

    # Passa as categorias únicas para o filtro no template
    categorias = ['Cuidados Pet', 'Histórias de Sucesso', 'Novidades', 'Eventos']
    
    return render_template(
        "blog.html", 
        posts=posts, 
        usuario=usuario, 
        pagina="blog",
        categorias=categorias,
        search_query=search_query,
        category_filter=category_filter
    )

@app.route("/blog/post/<string:slug>") #Esta rota usa o slug (o texto amigável na URL, como como-adotar-um-gato) para buscar o post específico
def post_detalhe(slug):
    usuario = obter_usuario_atual()
    cur = get_cursor()
    post = None
    
    try:
        # Busca a postagem específica pelo slug
        cur.execute(
            """
            SELECT 
                p.id, p.titulo, p.subtitulo, p.conteudo, p.imagem_url, 
                p.data_publicacao, p.categoria, u.nome as autor_nome
            FROM postagens p
            JOIN usuarios u ON p.autor_id = u.id
            WHERE p.slug = %s
            """,
            (slug,)
        )
        post_data = cur.fetchone()

        if post_data:
            post = {
                "id": post_data[0],
                "titulo": post_data[1],
                "subtitulo": post_data[2],
                "conteudo": post_data[3],
                "imagem_url": post_data[4],
                "data_publicacao": post_data[5].strftime('%d de %B, %Y') if post_data[5] else 'N/A',
                "categoria": post_data[6],
                "autor_nome": post_data[7],
            }
        else:
            flash("Postagem não encontrada.", "error")
            # Redireciona para a lista do blog se o post não existir
            return redirect(url_for("blog")) 
            
    except Exception as e:
        current_app.logger.error(f"ERRO AO CARREGAR DETALHE DO POST: {e}")
        flash("Erro ao carregar o conteúdo da postagem.", "error")
        return redirect(url_for("blog"))
    finally:
        cur.close()

    return render_template("post_detalhe.html", post=post, usuario=usuario, pagina="blog")



@app.route("/termos")
def termos():
    referer = request.headers.get("Referer")
    return render_template("termos.html", pagina="termos", referer=referer)


@app.route("/privacidade")
def privacidade():
    referer = request.headers.get("Referer")
    return render_template("privacidade.html", pagina="privacidade", referer=referer)



# ===================== PRIMEIRO ADMIN =====================
@app.route("/primeiro-admin", methods=["GET", "POST"])
def primeiro_admin():
    if request.method == "POST":
        try:
            nome = request.form.get("nome")
            email = request.form.get("email")
            telefone = request.form.get("telefone")
            senha = request.form.get("senha")
            confirmar_senha = request.form.get("confirmar_senha")

            if not all([nome, email, telefone, senha, confirmar_senha]):
                flash("Todos os campos são obrigatórios.", "error")
                return redirect(url_for("primeiro_admin"))
            if senha != confirmar_senha:
                flash("As senhas não coincidem.", "error")
                return redirect(url_for("primeiro_admin"))
            if len(senha) < 6:
                flash("A senha deve ter no mínimo 6 caracteres.", "error")
                return redirect(url_for("primeiro_admin"))

            cur = get_cursor()
            cur.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
            if cur.fetchone():
                cur.close()
                flash("Este email já está cadastrado.", "error")
                return redirect(url_for("primeiro_admin"))

            senha_hash = generate_password_hash(senha)
            cur.execute(
                """
                INSERT INTO usuarios (nome, email, senha, telefone, tipo, verificado, data_cadastro)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                """,
                (nome, email, senha_hash, telefone, "admin", True),
            )
            _get_conn().commit()
            cur.close()

            flash(f"✅ Administrador {nome} cadastrado com sucesso! Faça login para continuar.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            current_app.logger.error(f"Erro: {e}")
            flash("Erro ao cadastrar administrador.", "error")
            return redirect(url_for("primeiro_admin"))
    return render_template("cadastro_admin.html")

#ROTA PARA REMOVER PETS (ADMIN)
@app.route("/admin/remover-pet/<int:pet_id>", methods=["POST"])
def admin_remover_pet(pet_id):
    usuario = obter_usuario_atual()
    # Verifica permissão
    if not usuario or usuario["tipo"] != "admin":
        flash("Acesso restrito a administradores.", "error")
        return redirect(url_for("login"))
    
    try:
        cur = get_cursor()
        
        # 1. Obter o URL da imagem para exclusão no sistema de arquivos
        cur.execute("SELECT imagem_url FROM pets WHERE id = %s", (pet_id,))
        imagem_url_db = cur.fetchone()
        
        # Opcional: Remover adoções relacionadas primeiro (se a FK não for CASCADE)
        cur.execute("DELETE FROM adocoes WHERE pet_id = %s", (pet_id,))

        # 2. Remover o registro do banco de dados
        cur.execute("DELETE FROM pets WHERE id = %s", (pet_id,))
        _get_conn().commit()
        cur.close()

        # 3. Remover o arquivo físico
        if imagem_url_db and imagem_url_db[0]:
            # Retira o '/static/' do caminho para montar o caminho absoluto no sistema
            caminho_relativo = imagem_url_db[0].lstrip('/')
            caminho_arquivo = os.path.join(current_app.root_path, caminho_relativo)
            
            if os.path.exists(caminho_arquivo):
                os.remove(caminho_arquivo)
        
        flash(f"Pet ID {pet_id} removido com sucesso.", "success")
    except Exception as e:
        current_app.logger.error(f"ERRO AO REMOVER PET: {e}")
        flash("Erro ao remover o pet.", "error")
        
    return redirect(url_for("admin_pets"))


#ROTA PARA EDITAR UM PET (ADMIN)
@app.route("/admin/editar-pet/<int:pet_id>", methods=["GET", "POST"])
def admin_editar_pet(pet_id):
    usuario = obter_usuario_atual()
    # Verifica permissão (Admin ou Protetor)
    if not usuario or usuario["tipo"] not in ["admin", "protetor"]:
        flash("Acesso restrito.", "error")
        return redirect(url_for("login"))
    
    cur = get_cursor()
    
    if request.method == "POST":
        # === Lógica de Atualização ===
        try:
            nome = request.form["nome"]
            especie = request.form["especie"]
            idade = request.form["idade"]
            descricao = request.form["descricao"]
            
            imagem = request.files["imagem"]
            imagem_url_nova = None
            
            if imagem and imagem.filename != "":
                # Processamento do novo upload
                nome_arquivo = secure_filename(imagem.filename)
                caminho_imagem = os.path.join(app.config["UPLOAD_FOLDER"], nome_arquivo)
                os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
                imagem.save(caminho_imagem)
                imagem_url_nova = f"/static/imagens/{nome_arquivo}"
            
            # 1. Se houver uma nova imagem, atualiza o URL
            if imagem_url_nova:
                update_query = "UPDATE pets SET nome=%s, especie=%s, idade=%s, descricao=%s, imagem_url=%s WHERE id=%s"
                cur.execute(update_query, (nome, especie, idade, descricao, imagem_url_nova, pet_id))
            # 2. Se não houver nova imagem, atualiza sem alterar o URL existente
            else:
                update_query = "UPDATE pets SET nome=%s, especie=%s, idade=%s, descricao=%s WHERE id=%s"
                cur.execute(update_query, (nome, especie, idade, descricao, pet_id))
            
            _get_conn().commit()
            flash("Pet atualizado com sucesso!", "success")
            return redirect(url_for("admin_pets"))

        except Exception as e:
            current_app.logger.error(f"ERRO AO ATUALIZAR PET: {e}")
            flash("Erro ao atualizar o pet.", "error")
            
    # === Lógica de Exibição (GET) ===
    cur.execute("SELECT id, nome, especie, idade, descricao, imagem_url FROM pets WHERE id = %s", (pet_id,))
    pet_data = cur.fetchone()
    cur.close()
    
    if not pet_data:
        flash("Pet não encontrado.", "error")
        return redirect(url_for("admin_pets"))

    # Monta o dicionário para o template
    pet = {
        "id": pet_data[0], "nome": pet_data[1], "especie": pet_data[2], 
        "idade": pet_data[3], "descricao": pet_data[4], "imagem_url": pet_data[5]
    }
    
    return render_template("admin_editar_pet.html", pet=pet, usuario=usuario, pagina="admin")


# ===================== MAIN =====================

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)