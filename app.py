from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
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
from datetime import datetime, timedelta
import traceback
import secrets
import google.generativeai as genai




# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)

# ========== CONFIGURAÇÕES ==========
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'adote-me'
app.secret_key = 'sua-chave-secreta-aqui'


mysql = MySQL(app)

# Configurações de upload
UPLOAD_FOLDER = 'static/imagens'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# ✅ ADICIONE ESTA FUNÇÃO:
def allowed_file(filename):
    """Verifica se o arquivo tem uma extensão permitida"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'webp'}


# Configurações de e-mail
email_sistema = os.getenv("EMAIL_SISTEMA")
senha_email = os.getenv("SENHA_EMAIL")

# Configurar a chave da API do Gemini
GEMINI_API_KEY = "AIzaSyBAJIxOHZcsF2aowxVdZTGQ9i8aUkQHFLg"
genai.configure(api_key=GEMINI_API_KEY)





# ========= Verificar/Adicionar colunas de recuperação de senha ==========
def verificar_colunas_recuperacao():
    """Verifica e cria as colunas necessárias para recuperação de senha"""
    try:
        with app.app_context():  # ⭐⭐ CORREÇÃO AQUI ⭐⭐
            cur = mysql.connection.cursor()
            
            # Tentar adicionar as colunas (ignora erro se já existirem)
            try:
                cur.execute("ALTER TABLE usuarios ADD COLUMN reset_token VARCHAR(100) NULL")
                print("✅ Coluna reset_token criada")
            except Exception:
                print("ℹ️ Coluna reset_token já existe")
            
            try:
                cur.execute("ALTER TABLE usuarios ADD COLUMN reset_token_expira DATETIME NULL")
                print("✅ Coluna reset_token_expira criada")
            except Exception:
                print("ℹ️ Coluna reset_token_expira já existe")
            
            mysql.connection.commit()
            cur.close()
            return True
            
    except Exception as e:
        print(f"❌ Erro ao verificar/criar colunas: {e}")
        return False

# ⭐⭐ CHAMADA NORMAL (agora funciona porque a função tem contexto) ⭐⭐
verificar_colunas_recuperacao()


# ========== Funções auxiliares ==========
def obter_usuario_atual():
    """Retorna os dados do usuário logado ou None se não estiver logado"""
    print(f"🔍 SESSÃO ATUAL: {dict(session)}")  # DEBUG
    
    if 'logado' in session and session['logado']:
        usuario_data = {
            'id': session.get('usuario_id'),
            'nome': session.get('usuario_nome'),
            'email': session.get('usuario_email'),
            'tipo': session.get('usuario_tipo')
        }
        print(f"✅ USUÁRIO LOGADO: {usuario_data}")
        return usuario_data
    
    print("❌ NENHUM USUÁRIO LOGADO")
    return None



def enviar_email(destinatario, assunto, corpo, remetente='joalinyfurtado87@gmail.com', senha='lfhykuryoifmstep'):
    """Envia e-mail usando SMTP do Gmail"""
    try:
        print(f"📧 Tentando enviar email para: {destinatario}")
        print(f"📧 Remetente: {remetente}")
        
        msg = MIMEMultipart()
        msg['From'] = remetente
        msg['To'] = destinatario
        msg['Subject'] = assunto
        msg.attach(MIMEText(corpo, 'plain', 'utf-8'))

        # Configuração mais robusta
        servidor = smtplib.SMTP('smtp.gmail.com', 587)
        servidor.set_debuglevel(1)  # Ativa debug
        servidor.ehlo()
        servidor.starttls()
        servidor.ehlo()
        servidor.login(remetente, senha)
        
        texto = msg.as_string()
        servidor.sendmail(remetente, destinatario, texto)
        servidor.quit()
        
        print(f"✅ E-mail enviado com sucesso para {destinatario}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Erro de autenticação: {e}")
        print("Verifique: 1) Senha de app está correta? 2) Verificação 2 etapas ativada?")
        return False
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail: {e}")
        return False



# ========== Rotas de autenticação e usuários ==========

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login do usuário"""
    return render_template('login.html', pagina='login')


@app.route('/login-usuario', methods=['POST'])
def login_usuario():
    """Processa o login do usuário"""
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
                # Cria sessão do usuário
                session['usuario_id'] = usuario[0]
                session['usuario_nome'] = usuario[1]
                session['usuario_email'] = usuario[2]
                session['usuario_tipo'] = usuario[4]
                session['logado'] = True
                
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
    """Página de cadastro de usuário"""
    return render_template('cadastro_user.html', pagina='cadastro_user')


@app.route('/cadastrar_usuario', methods=['POST'])
def cadastrar_usuario():
    """Processa o cadastro de novo usuário"""
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


@app.route('/logout')
def logout():
    """Faz logout do usuário limpando a sessão"""
    session.clear()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('home'))


@app.route('/minha-conta')
def minha_conta():
    """Página da conta do usuário logado"""
    usuario = obter_usuario_atual()
    if not usuario:
        flash('Faça login para acessar sua conta.', 'error')
        return redirect(url_for('login'))
    
    return render_template('minha_conta.html', usuario=usuario, pagina='minha-conta')



    # ========== Rotas de Recuperação de Senha ==========
@app.route('/esqueci-senha', methods=['GET', 'POST'])
def esqueci_senha():
    """Página para solicitar recuperação de senha"""
    if request.method == 'POST':
        email = request.form.get('email')
        print(f"📧 Solicitação de recuperação para: {email}")
        
        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT id, nome FROM usuarios WHERE email = %s", (email,))
            usuario = cur.fetchone()
            
            if usuario:
                # Gerar token único
                token = secrets.token_urlsafe(32)
                expira_em = datetime.now() + timedelta(hours=1)
                
                print(f"🔐 Token gerado: {token}")
                print(f"⏰ Expira em: {expira_em}")
                
                # Salvar token no banco
                cur.execute(
                    "UPDATE usuarios SET reset_token = %s, reset_token_expira = %s WHERE email = %s",
                    (token, expira_em, email)
                )
                mysql.connection.commit()
                cur.close()
                
                # Enviar e-mail com o link de recuperação
                link_recuperacao = url_for('redefinir_senha', token=token, _external=True)
                
                assunto = "Recuperação de Senha - Adote-me"
                corpo = f"""
                Olá {usuario[1]}!
                
                Recebemos uma solicitação para redefinir sua senha no Adote-me.
                
                Clique no link abaixo para criar uma nova senha:
                {link_recuperacao}
                
                Este link expira em 1 hora.
                
                Se você não solicitou esta recuperação, ignore este e-mail.
                
                Atenciosamente,
                Equipe Adote-me
                """
                
                print(f"🔗 Link de recuperação: {link_recuperacao}")
                
                # Tentar enviar e-mail
                if enviar_email(email, assunto, corpo):
                    # ⭐⭐ CORREÇÃO: Retornar JSON para requisições AJAX ⭐⭐
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return jsonify({'success': True, 'message': 'Enviamos um e-mail com instruções para redefinir sua senha.'})
                    flash('Enviamos um e-mail com instruções para redefinir sua senha.', 'success')
                    print("✅ E-mail de recuperação enviado com sucesso")
                else:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return jsonify({'success': False, 'message': 'Erro ao enviar e-mail. Tente novamente.'})
                    flash('Erro ao enviar e-mail. Tente novamente.', 'error')
                    print("❌ Falha no envio do e-mail")
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': 'E-mail não encontrado em nosso sistema.'})
                flash('E-mail não encontrado em nosso sistema.', 'error')
                print("❌ E-mail não encontrado no banco de dados")
            
            # ⭐⭐ CORREÇÃO: Só redirecionar se NÃO for AJAX ⭐⭐
            if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return redirect(url_for('login'))
            else:
                return jsonify({'success': True, 'message': 'Processamento concluído'})
            
        except Exception as e:
            print(f"❌ Erro no banco de dados: {e}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': 'Erro interno do sistema. Tente novamente.'})
            flash('Erro interno do sistema. Tente novamente.', 'error')
            return redirect(url_for('login'))
    
    # ⭐⭐ SE FOR GET, REDIRECIONAR PARA LOGIN ⭐⭐
    return redirect(url_for('login'))



@app.route('/redefinir-senha/<token>', methods=['GET', 'POST'])
def redefinir_senha(token):
    """Página para redefinir a senha usando o token"""
    try:
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT id, email, reset_token_expira FROM usuarios WHERE reset_token = %s",
            (token,)
        )
        usuario = cur.fetchone()
        
        if not usuario:
            flash('Token inválido ou expirado.', 'error')
            return redirect(url_for('esqueci_senha'))
        
        # ⭐⭐ CORREÇÃO: Usar datetime.now() corretamente ⭐⭐
        if usuario[2] < datetime.now():
            flash('Token expirado. Solicite uma nova recuperação.', 'error')
            return redirect(url_for('esqueci_senha'))
        
        if request.method == 'POST':
            nova_senha = request.form.get('nova_senha')
            confirmar_senha = request.form.get('confirmar_senha')
            
            if nova_senha != confirmar_senha:
                flash('As senhas não coincidem.', 'error')
                return redirect(url_for('redefinir_senha', token=token))
            
            if len(nova_senha) < 6:
                flash('A senha deve ter no mínimo 6 caracteres.', 'error')
                return redirect(url_for('redefinir_senha', token=token))
            
            # Atualizar senha e limpar token
            senha_hash = generate_password_hash(nova_senha)
            cur.execute(
                "UPDATE usuarios SET senha = %s, reset_token = NULL, reset_token_expira = NULL WHERE id = %s",
                (senha_hash, usuario[0])
            )
            mysql.connection.commit()
            cur.close()
            
            flash('Senha redefinida com sucesso! Faça login com sua nova senha.', 'success')
            return redirect(url_for('login'))
        
        cur.close()
        return render_template('redefinir_senha.html', token=token, pagina='redefinir_senha')
        
    except Exception as e:
        print(f"❌ Erro na redefinição de senha: {e}")
        flash('Erro interno do sistema. Tente novamente.', 'error')
        return redirect(url_for('esqueci_senha'))



    

# ========== Rotas de Pets ==========

@app.route('/')
@app.route('/home')
def home():
    """Página inicial com lista de pets e carrossel de pets perdidos"""
    usuario = obter_usuario_atual()
    
    try:
        # Buscar pets do MySQL (já existente)
        cur1 = mysql.connection.cursor()  # Primeiro cursor
        cur1.execute("SELECT * FROM pets ORDER BY id DESC LIMIT 6")
        pets_data = cur1.fetchall()
        cur1.close()  # Fechar primeiro cursor
        
        # BUSCAR PETS PERDIDOS PARA O CARROSSEL (NOVO)
        cur2 = mysql.connection.cursor()  # Segundo cursor
        cur2.execute('''
            SELECT id, nome, especie, raca, local_desaparecimento, 
                   contato_telefone, foto_path, data_desaparecimento
            FROM pets_perdidos 
            WHERE status = 'perdido' 
            ORDER BY data_criacao DESC 
            LIMIT 8
        ''')
        pets_perdidos_carrossel_data = cur2.fetchall()
        cur2.close()  # Fechar segundo cursor
        
        # Formatar pets (já existente)
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
        
        # Formatar pets perdidos para o carrossel (NOVO)
        pets_perdidos_carrossel = []
        for pet in pets_perdidos_carrossel_data:
            pets_perdidos_carrossel.append({
                'id': pet[0],
                'nome': pet[1],
                'especie': pet[2],
                'raca': pet[3],
                'local_desaparecimento': pet[4],
                'contato_telefone': pet[5],
                'foto_path': pet[6],
                'data_desaparecimento': pet[7]
            })
        
        return render_template('home.html', 
                             usuario=usuario, 
                             pagina='home', 
                             pets=pets,
                             pets_perdidos_carrossel=pets_perdidos_carrossel)
                             
    except Exception as e:
        print(f"❌ Erro na página inicial: {e}")
        # Em caso de erro, retornar pelo menos os pets normais
        usuario = obter_usuario_atual()
        return render_template('home.html', 
                             usuario=usuario, 
                             pagina='home', 
                             pets=[],
                             pets_perdidos_carrossel=[])


@app.route('/adotar')
def adotar():
    """Página para visualizar todos os pets disponíveis para adoção"""
    usuario = obter_usuario_atual()
    especie = request.args.get('especie')
    idade = request.args.get('idade')

    cur = mysql.connection.cursor()

    # Montar a query com filtros
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


@app.route('/pet/<int:id>')
def detalhes_pet(id):
    """Página de detalhes de um pet específico"""
    usuario = obter_usuario_atual() 
    sucesso = request.args.get('sucesso', False)
    nome = request.args.get('nome', '')
    mostrar_modal_login = request.args.get('mostrar_modal_login') == 'true'  # ✅ NOVO
    
    
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
            mostrar_modal_login=mostrar_modal_login,  # ✅ NOVO
            usuario=usuario)
    else:
        return "Pet não encontrado", 404


@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    """Página para cadastrar novo pet"""
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
    """Processa a solicitação de adoção de um pet"""
    
    # ✅ VERIFICAR SE USUÁRIO ESTÁ LOGADO
    usuario = obter_usuario_atual()
    if not usuario:
        flash('Você precisa fazer login ou se cadastrar para solicitar adoção.', 'error')
        return redirect(url_for('detalhes_pet', id=id, mostrar_modal_login='true'))
    
    try:
        print("🐾 === INICIANDO SOLICITAÇÃO DE ADOÇÃO ===")
        print(f"👤 Usuário logado: {usuario}")
        print(f"🐕 Pet ID: {id}")
        
        # ✅ DADOS DO FORMULÁRIO COMPLETO
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        telefone = request.form.get('telefone', '').strip()
        mensagem = request.form.get('mensagem', '').strip()

        print(f"📝 Dados recebidos: {nome}, {email}, {telefone}")
        print(f"💬 Mensagem recebida: '{mensagem}'")

        # ✅ VALIDAÇÃO DOS CAMPOS
        if not all([nome, email, telefone, mensagem]):
            missing = []
            if not nome: missing.append('nome')
            if not email: missing.append('email')
            if not telefone: missing.append('telefone')
            if not mensagem: missing.append('mensagem')
            
            flash(f'Por favor, preencha todos os campos: {", ".join(missing)}', 'error')
            return redirect(url_for('detalhes_pet', id=id))

        print("✅ Todos os campos válidos")

        cur = mysql.connection.cursor()
        
        # ✅ VERIFICAR SE O PET EXISTE
        cur.execute("SELECT id, nome, especie, idade FROM pets WHERE id = %s", (id,))
        pet = cur.fetchone()
        
        if not pet:
            print(f"❌ Pet com ID {id} não encontrado")
            flash('Pet não encontrado.', 'error')
            cur.close()
            return redirect(url_for('adotar'))
        
        pet_nome = pet[1]
        pet_especie = pet[2]
        pet_idade = pet[3]
        print(f"✅ Pet encontrado: {pet_nome} ({pet_especie}, {pet_idade} anos)")

        # ✅ VERIFICAR/CRIAR TABELA ADOÇÕES
        try:
            cur.execute("""
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
            """)
            mysql.connection.commit()
            print("✅ Tabela 'adocoes' verificada/criada com sucesso")
            
        except Exception as e:
            print(f"❌ Erro ao verificar/criar tabela: {e}")
            flash('Erro no banco de dados.', 'error')
            cur.close()
            return redirect(url_for('detalhes_pet', id=id))

        # ✅ INSERIR SOLICITAÇÃO NO BANCO
        try:
            cur.execute("""
                INSERT INTO adocoes (pet_id, usuario_id, nome, email, telefone, mensagem) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (id, usuario['id'], nome, email, telefone, mensagem))
            
            mysql.connection.commit()
            adocao_id = cur.lastrowid
            print(f"✅ Solicitação inserida com ID: {adocao_id}")
            
        except Exception as e:
            print(f"❌ Erro ao inserir solicitação: {e}")
            mysql.connection.rollback()
            flash('Erro ao salvar solicitação no banco de dados.', 'error')
            cur.close()
            return redirect(url_for('detalhes_pet', id=id))

        cur.close()

        # ✅ TENTAR ENVIAR E-MAIL (OPCIONAL)
        try:
            assunto = f"✅ Solicitação de adoção - {pet_nome}"
            corpo = f"""
            Olá {nome}!

            🎉 Sua solicitação para adotar {pet_nome} foi recebida com sucesso!

            📋 Detalhes da sua solicitação:
            • 🐕 Pet: {pet_nome} ({pet_especie}, {pet_idade} anos)
            • 📧 Seu e-mail: {email}
            • 📞 Seu telefone: {telefone}
            • 💬 Sua mensagem: {mensagem}
            • 📅 Data: {datetime.now().strftime('%d/%m/%Y às %H:%M')}

            ⏰ Nossa equipe entrará em contato com você em até 48 horas.

            Obrigado por escolher adotar com responsabilidade! 🐾

            Atenciosamente,
            Equipe Adote-me
            """

            if enviar_email(email, assunto, corpo):
                print("✅ E-mail de confirmação enviado")
            else:
                print("⚠️ E-mail não enviado, mas solicitação salva")
                
        except Exception as e:
            print(f"⚠️ Erro ao enviar e-mail: {e}")

        # ✅ SUCESSO
        print("🎉 Solicitação de adoção processada com sucesso!")
        return redirect(url_for('detalhes_pet', id=id, sucesso='true', nome=nome))

    except Exception as e:
        print(f"❌ ERRO GERAL NA SOLICITAÇÃO: {str(e)}")
        print(f"TRACEBACK: {traceback.format_exc()}")
        flash('Erro interno ao processar solicitação. Tente novamente.', 'error')
        return redirect(url_for('detalhes_pet', id=id))



 # ========== Rotas de Minhas Adoções ==========

@app.route('/minhas-adocoes')
def minhas_adocoes():
    """Página com as adoções solicitadas pelo usuário"""
    usuario = obter_usuario_atual()
    if not usuario:
        flash('Faça login para ver suas adoções.', 'error')
        return redirect(url_for('login'))
    
    try:
        cur = mysql.connection.cursor()
        
        print(f"🔍 Buscando adoções para usuário ID: {usuario['id']}")
        
        # ✅ QUERY SIMPLIFICADA E CORRETA
        cur.execute("""
            SELECT 
                a.id, a.pet_id, a.nome, a.email, a.telefone, 
                a.mensagem, a.data_solicitacao, a.status,
                p.nome as pet_nome, p.especie, p.idade, p.imagem_url
            FROM adocoes a
            LEFT JOIN pets p ON a.pet_id = p.id
            WHERE a.usuario_id = %s
            ORDER BY a.data_solicitacao DESC
        """, (usuario['id'],))
        
        adocoes_data = cur.fetchall()
        cur.close()
        
        print(f"✅ Encontradas {len(adocoes_data)} adoções")
        
        # ✅ FORMATAÇÃO CORRETA DOS DADOS
        adocoes = []
        for adocao in adocoes_data:
            adocoes.append({
                'id': adocao[0],           # a.id
                'pet_id': adocao[1],       # a.pet_id
                'nome_solicitante': adocao[2],  # a.nome
                'email': adocao[3],        # a.email
                'telefone': adocao[4],     # a.telefone
                'mensagem': adocao[5],     # a.mensagem
                'data_solicitacao': adocao[6],  # a.data_solicitacao
                'status': adocao[7] or 'pendente',  # a.status
                'pet_nome': adocao[8],     # p.nome
                'pet_especie': adocao[9],  # p.especie
                'pet_idade': adocao[10],   # p.idade
                'pet_imagem': adocao[11]   # p.imagem_url
            })
            print(f"📋 Adoção encontrada: {adocao[8]} - Status: {adocao[7]}")
        
        return render_template('minhas_adocoes.html', 
                             usuario=usuario, 
                             pagina='minhas-adocoes', 
                             adocoes=adocoes,
                             total_adocoes=len(adocoes))
        
    except Exception as e:
        print(f"❌ Erro ao carregar adoções: {e}")
        import traceback
        print(f"📋 Traceback completo: {traceback.format_exc()}")
        flash('Erro ao carregar suas adoções.', 'error')
        return render_template('minhas_adocoes.html', 
                             usuario=usuario, 
                             pagina='minhas-adocoes', 
                             adocoes=[],
                             total_adocoes=0)


@app.route('/api/cancelar-adocao/<int:adocao_id>', methods=['POST'])
def cancelar_adocao(adocao_id):
    """Cancela uma solicitação de adoção"""
    usuario = obter_usuario_atual()
    if not usuario:
        return jsonify({'success': False, 'message': 'Faça login para cancelar adoções.'})
    
    try:
        cur = mysql.connection.cursor()
        
        # Verificar se a adoção pertence ao usuário
        cur.execute("""
            SELECT id FROM adocoes 
            WHERE id = %s AND usuario_id = %s
        """, (adocao_id, usuario['id']))
        
        adocao = cur.fetchone()
        
        if not adocao:
            return jsonify({'success': False, 'message': 'Adoção não encontrada.'})
        
        # Cancelar a adoção
        cur.execute("""
            UPDATE adocoes SET status = 'cancelada' 
            WHERE id = %s
        """, (adocao_id,))
        
        mysql.connection.commit()
        cur.close()
        
        return jsonify({
            'success': True,
            'message': 'Adoção cancelada com sucesso!'
        })
        
    except Exception as e:
        print(f"❌ Erro ao cancelar adoção: {e}")
        return jsonify({'success': False, 'message': 'Erro ao cancelar adoção.'})



# ========== Rotas do Dashboard Admin ==========

@app.route('/admin')
def admin_dashboard():
    """Dashboard principal do administrador"""
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
        return render_template('admin_dashboard.html', 
            usuario=usuario, 
            pagina='admin',
            total_usuarios=0,
            total_protetores=0,
            total_pets=0,
            total_adocoes=0)

@app.route('/admin/usuarios')
def admin_usuarios():
    """Página de administração para gerenciar todos os usuários com paginação"""
    usuario = obter_usuario_atual()
    
    # ✅ Verificar se é admin
    if not usuario or usuario.get('tipo') != 'admin':
        flash('Acesso negado. Área restrita para administradores.', 'error')
        return redirect('/home')
    
    try:
        # ✅ Configuração da paginação
        pagina = request.args.get('pagina', 1, type=int)
        por_pagina = 10
        
        # Calcular offset
        offset = (pagina - 1) * por_pagina
        
        cur = mysql.connection.cursor()
        
        # ✅ MODIFICADO: Contar total de TODOS os usuários (adotantes, protetores e admins)
        cur.execute("SELECT COUNT(*) FROM usuarios WHERE tipo IN ('adotante', 'protetor', 'admin')")
        total_usuarios = cur.fetchone()[0]
        
        # ✅ MODIFICADO: Buscar TODOS os usuários com paginação
        cur.execute("""
            SELECT id, nome, email, tipo, data_cadastro, telefone, verificado
            FROM usuarios 
            WHERE tipo IN ('adotante', 'protetor', 'admin')
            ORDER BY 
                CASE 
                    WHEN tipo = 'admin' THEN 1
                    WHEN tipo = 'protetor' THEN 2
                    WHEN tipo = 'adotante' THEN 3
                    ELSE 4
                END,
                data_cadastro DESC
            LIMIT %s OFFSET %s
        """, (por_pagina, offset))
        usuarios_data = cur.fetchall()
        cur.close()
        
        # Calcular total de páginas
        total_paginas = (total_usuarios + por_pagina - 1) // por_pagina
        
        # Formatar usuários
        usuarios = []
        for user in usuarios_data:
            usuarios.append({
                'id': user[0],
                'nome': user[1],
                'email': user[2],
                'tipo': user[3],
                'data_cadastro': user[4].strftime('%d/%m/%Y %H:%M') if user[4] else 'N/A',
                'telefone': user[5] or 'Não informado',
                'verificado': user[6]
            })
        
        print(f"✅ Página {pagina}: {len(usuarios)} de {total_usuarios} usuários")
        
        return render_template('admin_usuarios.html', 
                             usuario=usuario, 
                             usuarios=usuarios,
                             pagina_atual=pagina,
                             total_paginas=total_paginas,
                             total_usuarios=total_usuarios,
                             por_pagina=por_pagina,
                             pagina='admin_usuarios')
    
    except Exception as e:
        print(f"❌ Erro ao carregar usuários: {str(e)}")
        flash(f'Erro ao carregar usuários: {str(e)}', 'error')
        return redirect('/home')

# ✅ CORREÇÃO: Removido o espaço antes do @app.route
@app.route('/admin/usuario/<int:user_id>/excluir', methods=['DELETE'])
def excluir_usuario(user_id):
    """Excluir usuário e seus registros relacionados"""
    usuario = obter_usuario_atual()
    
    if not usuario or usuario.get('tipo') != 'admin':
        return jsonify({'success': False, 'message': 'Acesso negado'})
    
    try:
        cur = mysql.connection.cursor()
        
        # ✅ VERIFICAR SE É O PRÓPRIO USUÁRIO
        if user_id == usuario['id']:
            return jsonify({'success': False, 'message': 'Não é possível excluir a si mesmo'})
        
        # ✅ VERIFICAR SE O USUÁRIO É ADMIN
        cur.execute("SELECT tipo FROM usuarios WHERE id = %s", (user_id,))
        user_tipo = cur.fetchone()
        if user_tipo and user_tipo[0] == 'admin':
            return jsonify({'success': False, 'message': 'Não é possível excluir administradores'})
        
        # ✅ EXCLUIR REGISTROS RELACIONADOS NAS ADOÇÕES
        cur.execute("DELETE FROM adocoes WHERE usuario_id = %s", (user_id,))
        print(f"✅ Registros de adoções excluídos para usuário {user_id}")
        
        # ✅ EXCLUIR OUTROS REGISTROS RELACIONADOS (se houver outras tabelas)
        # Exemplo: cur.execute("DELETE FROM outra_tabela WHERE usuario_id = %s", (user_id,))
        
        # ✅ AGORA EXCLUIR O USUÁRIO
        cur.execute("DELETE FROM usuarios WHERE id = %s", (user_id,))
        
        mysql.connection.commit()
        cur.close()
        
        print(f"✅ Usuário {user_id} excluído com sucesso")
        return jsonify({'success': True, 'message': 'Usuário excluído com sucesso'})
        
    except Exception as e:
        mysql.connection.rollback()
        print(f"❌ Erro ao excluir usuário {user_id}: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro ao excluir usuário: {str(e)}'})



        


@app.route('/admin/protetores')
def admin_protetores():
    """Página de gerenciamento de protetores"""
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


@app.route('/admin/pets')
def admin_pets():
    """Página de gerenciamento de pets"""
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
    """Página de relatórios e estatísticas"""
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
    """Página de configurações do admin"""
    usuario = obter_usuario_atual()
    if not usuario or usuario['tipo'] != 'admin':
        flash('Acesso restrito a administradores.', 'error')
        return redirect(url_for('login'))
    
    return render_template('admin_configuracoes.html', 
        usuario=usuario, 
        pagina='admin')


@app.route('/protetor')
def protetor_dashboard():
    """Dashboard do protetor"""
    usuario = obter_usuario_atual()
    if not usuario or usuario['tipo'] != 'protetor':
        flash('Acesso restrito a protetores.', 'error')
        return redirect(url_for('login'))
    
    return render_template('protetor_dashboard.html', usuario=usuario, pagina='protetor')


# ========== Rotas de Utilitários ==========

@app.route('/criar-admin-teste')
def criar_admin_teste():
    """Rota para criar um usuário admin de teste"""
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



@app.route('/sobre')
def sobre():
    """Página sobre o sistema"""
    usuario = obter_usuario_atual()
    return render_template('sobre.html', usuario=usuario, pagina='sobre')


@app.route("/termos")
def termos():
    """Página de termos de uso"""
    referer = request.headers.get("Referer")
    return render_template("termos.html", pagina="termos", referer=referer)


@app.route("/privacidade")
def privacidade():
    """Página de política de privacidade"""
    referer = request.headers.get("Referer")
    return render_template("privacidade.html", pagina="privacidade", referer=referer)




# ========== ROTA DE IA PARA DICAS  ==========
@app.route('/ia-dicas', methods=['POST'])
def ia_dicas():
    """API para gerar dicas DIRETAS usando IA"""
    data = request.get_json()
    pergunta = data.get('pergunta', '').strip()
    
    if not pergunta:
        return jsonify({'resposta': 'Digite uma pergunta.'})
    
    if len(pergunta) < 2:
        return jsonify({'resposta': 'Pergunta muito curta.'})
    
    resposta = gerar_resposta_gemini(pergunta)
    return jsonify({'resposta': resposta})



def gerar_resposta_gemini(pergunta):
    """Gera resposta usando Google Gemini AI com modelos disponíveis"""
    try:
        # Modelos prioritários baseados na sua lista
        modelos_prioritarios = [
            'models/gemini-2.0-flash-001',      # Mais estável
            'models/gemini-2.0-flash',          # Versão atual
            'models/gemini-flash-latest',       # Sempre atualizado
        ]
        
        for modelo_nome in modelos_prioritarios:
            try:
                print(f"🔄 Tentando modelo: {modelo_nome}")
                model = genai.GenerativeModel(modelo_nome)
                
                prompt = f"""
                Você é um assistente direto e objetivo sobre adoção de animais e cuidados com pets.
                
                REGRAS IMPORTANTES:
                - Seja DIRETO e OBJETIVO
                - Responda APENAS o que foi perguntado
                - Não faça introduções longas
                - Não liste tópicos não solicitados
                - Use português do Brasil
                - Se for cálculo matemático, responda apenas o resultado
                - Mantenha as respostas curtas e úteis
                
                Pergunta: {pergunta}
                
                Resposta direta:
                """
                
                response = model.generate_content(prompt)
                
                if response.text:
                    print(f"✅ Resposta gerada com {modelo_nome}")
                    # Limpar possíveis introduções automáticas
                    resposta_limpa = response.text.strip()
                    # Remover saudações automáticas se existirem
                    if resposta_limpa.startswith(('Olá!', 'Oi!', 'Olá,', 'Oi,')):
                        # Encontrar onde começa a resposta real
                        linhas = resposta_limpa.split('\n')
                        for i, linha in enumerate(linhas):
                            if any(palavra in linha.lower() for palavra in ['resposta', 'resultado', 'é', 'são', '4+4', '8']):
                                resposta_limpa = '\n'.join(linhas[i:])
                                break
                    
                    return resposta_limpa
                    
            except Exception as e:
                print(f"❌ {modelo_nome} falhou: {str(e)[:100]}...")
                continue
        
        # Fallback se todos os modelos falharem
        return resposta_fallback(pergunta)
        
    except Exception as e:
        print(f"🔥 Erro geral: {e}")
        return "Erro temporário. Tente novamente."


        

# ========== ROTA SIMPLES PARA CADASTRAR PRIMEIRO ADMIN ==========

@app.route('/primeiro-admin', methods=['GET', 'POST'])
def primeiro_admin():
    """Rota simples para cadastrar o primeiro administrador"""
    
    if request.method == 'POST':
        try:
            # Dados do formulário
            nome = request.form.get('nome')
            email = request.form.get('email')
            telefone = request.form.get('telefone')
            senha = request.form.get('senha')
            confirmar_senha = request.form.get('confirmar_senha')
            
            # Validações básicas
            if not all([nome, email, telefone, senha, confirmar_senha]):
                flash('Todos os campos são obrigatórios.', 'error')
                return redirect(url_for('primeiro_admin'))
                
            if senha != confirmar_senha:
                flash('As senhas não coincidem.', 'error')
                return redirect(url_for('primeiro_admin'))
                
            if len(senha) < 6:
                flash('A senha deve ter no mínimo 6 caracteres.', 'error')
                return redirect(url_for('primeiro_admin'))

            # Verificar se email já existe
            cur = mysql.connection.cursor()
            cur.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
            if cur.fetchone():
                flash('Este email já está cadastrado.', 'error')
                cur.close()
                return redirect(url_for('primeiro_admin'))

            # Criptografar senha
            senha_hash = generate_password_hash(senha)

            # Inserir como admin
            cur.execute("""
                INSERT INTO usuarios (nome, email, senha, telefone, tipo, verificado, data_cadastro)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """, (nome, email, senha_hash, telefone, 'admin', True))
            
            mysql.connection.commit()
            cur.close()
            
            flash(f'✅ Administrador {nome} cadastrado com sucesso! Faça login para continuar.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            print(f"Erro: {e}")
            flash('Erro ao cadastrar administrador.', 'error')
            return redirect(url_for('primeiro_admin'))
    
    # GET - Mostrar formulário
    return render_template('cadastro_admin.html')



# ========== Rotas de Favoritos ==========

@app.route('/api/favoritar/<int:pet_id>', methods=['POST'])
def favoritar_pet(pet_id):
    """Adiciona ou remove um pet dos favoritos"""
    usuario = obter_usuario_atual()
    if not usuario:
        return jsonify({'success': False, 'message': 'Faça login para favoritar pets.'})
    
    try:
        cur = mysql.connection.cursor()
        
        # Verificar se já está favoritado
        cur.execute(
            "SELECT id FROM favoritos WHERE usuario_id = %s AND pet_id = %s",
            (usuario['id'], pet_id)
        )
        favorito_existente = cur.fetchone()
        
        if favorito_existente:
            # Remover dos favoritos
            cur.execute(
                "DELETE FROM favoritos WHERE usuario_id = %s AND pet_id = %s",
                (usuario['id'], pet_id)
            )
            action = 'removido'
            is_favorito = False
        else:
            # Adicionar aos favoritos
            cur.execute(
                "INSERT INTO favoritos (usuario_id, pet_id) VALUES (%s, %s)",
                (usuario['id'], pet_id)
            )
            action = 'adicionado'
            is_favorito = True
        
        mysql.connection.commit()
        cur.close()
        
        return jsonify({
            'success': True,
            'action': action,
            'is_favorito': is_favorito,
            'message': f'Pet {action} dos favoritos!'
        })
        
    except Exception as e:
        print(f"❌ Erro ao favoritar pet: {e}")
        return jsonify({'success': False, 'message': 'Erro ao processar favorito.'})


@app.route('/api/verificar-favorito/<int:pet_id>')
def verificar_favorito(pet_id):
    """Verifica se um pet está favoritado pelo usuário atual"""
    usuario = obter_usuario_atual()
    if not usuario:
        return jsonify({'is_favorito': False})
    
    try:
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT id FROM favoritos WHERE usuario_id = %s AND pet_id = %s",
            (usuario['id'], pet_id)
        )
        favorito = cur.fetchone()
        cur.close()
        
        return jsonify({'is_favorito': bool(favorito)})
        
    except Exception as e:
        print(f"❌ Erro ao verificar favorito: {e}")
        return jsonify({'is_favorito': False})


@app.route('/meus-favoritos')
def meus_favoritos():
    """Página com os pets favoritados pelo usuário"""
    usuario = obter_usuario_atual()
    if not usuario:
        flash('Faça login para ver seus favoritos.', 'error')
        return redirect(url_for('login'))
    
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT p.* 
            FROM pets p
            INNER JOIN favoritos f ON p.id = f.pet_id
            WHERE f.usuario_id = %s
            ORDER BY f.data_favoritado DESC
        """, (usuario['id'],))
        
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
        
        return render_template('meus_favoritos.html', 
                             usuario=usuario, 
                             pagina='meus-favoritos', 
                             pets=pets,
                             total_favoritos=len(pets))
        
    except Exception as e:
        print(f"❌ Erro ao carregar favoritos: {e}")
        flash('Erro ao carregar seus favoritos.', 'error')
        return render_template('meus_favoritos.html', 
                             usuario=usuario, 
                             pagina='meus-favoritos', 
                             pets=[],
                             total_favoritos=0)


# ========== Rotas de Pets Perdidos ==========
@app.route('/divulgar-perdido')
def divulgar_perdido():
    if 'usuario_id' not in session:
        flash('Você precisa estar logado para divulgar um pet perdido.', 'warning')
        return redirect('/login')
    
    usuario = obter_usuario_atual()  # ← ADICIONE ESTA LINHA
    return render_template('divulgar_perdido.html', pagina='divulgar_perdido', usuario=usuario)

@app.route('/divulgar-perdido', methods=['POST'])
def processar_divulgar_perdido():
    if 'usuario_id' not in session:
        flash('Você precisa estar logado.', 'error')
        return redirect('/login')
        
    
    try:
        # Dados básicos do pet
        nome = request.form.get('nome')
        especie = request.form.get('especie')
        raca = request.form.get('raca', '')
        cor = request.form.get('cor', '')
        porte = request.form.get('porte', '')
        sexo = request.form.get('sexo', '')
        idade = request.form.get('idade', '')
        caracteristicas = request.form.get('caracteristicas', '')
        
        # Detalhes do desaparecimento
        data_desaparecimento = request.form.get('data_desaparecimento')
        local = request.form.get('local')
        referencia = request.form.get('referencia', '')
        descricao = request.form.get('descricao')
        
        # Características especiais
        microchip = 1 if request.form.get('microchip') else 0
        coleira = 1 if request.form.get('coleira') else 0
        vacinado = 1 if request.form.get('vacinado') else 0
        
        # Contato
        contato_nome = request.form.get('contato_nome')
        contato_telefone = request.form.get('contato_telefone')
        contato_email = request.form.get('contato_email', '')
        
        # ✅ Processar imagem COM FUNÇÃO DEFINIDA
        foto_path = None
        if 'foto' in request.files:
            file = request.files['foto']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                foto_path = unique_filename
                print(f"✅ Foto salva: {foto_path}")
            else:
                print("⚠️ Nenhuma foto válida enviada")
        
        # Inserir no banco de dados
        cur = mysql.connection.cursor()
        
        cur.execute('''
            INSERT INTO pets_perdidos 
            (usuario_id, nome, especie, raca, cor, porte, sexo, idade, caracteristicas,
             data_desaparecimento, local_desaparecimento, referencia, descricao,
             microchip, coleira, vacinado, contato_nome, contato_telefone, contato_email,
             foto_path, data_criacao, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (session['usuario_id'], nome, especie, raca, cor, porte, sexo, idade, caracteristicas,
              data_desaparecimento, local, referencia, descricao,
              microchip, coleira, vacinado, contato_nome, contato_telefone, contato_email,
              foto_path, datetime.now(), 'perdido'))
        
        mysql.connection.commit()
        cur.close()
        
        flash('Pet perdido divulgado com sucesso! A comunidade vai ajudar a encontrar.', 'success')
        return redirect('/pets-perdidos')
        
    except Exception as e:
        print(f"❌ Erro detalhado: {traceback.format_exc()}")
        flash(f'Erro ao divulgar pet: {str(e)}', 'error')
        return redirect('/divulgar-perdido')

@app.route('/pets-perdidos')
def pets_perdidos():
    """Página para listar todos os pets perdidos"""
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)  # ← MUDE AQUI
        cur.execute('''
            SELECT 
                pp.id, pp.usuario_id, pp.nome, pp.especie, pp.raca, pp.cor, pp.porte, 
                pp.sexo, pp.idade, pp.caracteristicas, pp.data_desaparecimento, 
                pp.local_desaparecimento, pp.referencia, pp.descricao, pp.microchip, 
                pp.coleira, pp.vacinado, pp.contato_nome, pp.contato_telefone, 
                pp.contato_email, pp.foto_path, pp.data_criacao, pp.status,
                u.nome as usuario_nome
            FROM pets_perdidos pp
            LEFT JOIN usuarios u ON pp.usuario_id = u.id
            WHERE pp.status = "perdido"
            ORDER BY pp.data_criacao DESC
        ''')
        
        pets_perdidos = cur.fetchall()  # ← AGORA JÁ VEM COMO DICIONÁRIO
        cur.close()
        
        usuario = obter_usuario_atual()
        return render_template('pets_perdidos.html', 
                             pets_perdidos=pets_perdidos, 
                             usuario=usuario,
                             pagina='pets_perdidos')
        
    except Exception as e:
        print(f"❌ Erro ao carregar pets perdidos: {e}")
        flash('Erro ao carregar lista de pets perdidos.', 'error')
        return render_template('pets_perdidos.html', 
                             pets_perdidos=[], 
                             usuario=obter_usuario_atual(),
                             pagina='pets_perdidos')
                             

@app.route('/pet-encontrado/<int:pet_id>')
def marcar_como_encontrado(pet_id):
    if 'usuario_id' not in session:
        flash('Você precisa estar logado.', 'error')
        return redirect('/login')
    
    try:
        cur = mysql.connection.cursor()
        
        # Verificar se o usuário é o dono do anúncio
        cur.execute('SELECT usuario_id FROM pets_perdidos WHERE id = %s', (pet_id,))
        pet = cur.fetchone()
        
        if pet and pet[0] == session['usuario_id']:
            cur.execute('''
                UPDATE pets_perdidos 
                SET status = "encontrado", data_encontrado = %s
                WHERE id = %s
            ''', (datetime.now(), pet_id))
            
            mysql.connection.commit()
            flash('Que bom que encontrou seu pet! 🎉', 'success')
        else:
            flash('Você não tem permissão para esta ação.', 'error')
        
        cur.close()
        return redirect('/pets-perdidos')
        
    except Exception as e:
        flash(f'Erro ao marcar pet como encontrado: {str(e)}', 'error')
        return redirect('/pets-perdidos')





        
     

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)