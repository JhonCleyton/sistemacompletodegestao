from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from sqlalchemy import func, extract

app = Flask(__name__)

# Configurações de segurança
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sua-chave-secreta-temporaria')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configurações para produção
if os.environ.get('PRODUCTION'):
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'diretoria', 'financeiro', 'usuario', 'visualizador', 'gerente'
    nome_completo = db.Column(db.String(100))
    email = db.Column(db.String(120))
    data_criacao = db.Column(db.DateTime, default=datetime.now)
    ativo = db.Column(db.Boolean, default=True)
    criado_por_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    @property
    def is_diretoria(self):
        return self.role == 'diretoria'
        
    @property
    def is_financeiro(self):
        return self.role == 'financeiro'
        
    @property
    def is_visualizador(self):
        return self.role == 'visualizador'
        
    @property
    def can_create_notes(self):
        return self.role == 'usuario'
        
    @property
    def is_gerente(self):
        return self.role == 'gerente'

class HistoricoNota(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nota_id = db.Column(db.Integer, db.ForeignKey('nota.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    data_hora = db.Column(db.DateTime, default=datetime.now, nullable=False)
    tipo_alteracao = db.Column(db.String(50), nullable=False)  # 'criacao', 'edicao', 'autorizacao', etc
    descricao = db.Column(db.Text, nullable=False)
    
    # Relacionamentos
    nota = db.relationship('Nota', backref='historico')
    usuario = db.relationship('User')

class Nota(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.Integer, unique=True, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tipo_ave = db.Column(db.String(50), nullable=True)
    num_cargas = db.Column(db.Integer, nullable=True)
    ordem_carga = db.Column(db.String(10), nullable=True)
    data_abate = db.Column(db.DateTime, nullable=True)
    dia_semana = db.Column(db.String(20), nullable=True)
    motorista = db.Column(db.String(100), nullable=True)
    transportadora = db.Column(db.String(100), nullable=True)
    placa_veiculo = db.Column(db.String(20), nullable=True)
    qtd_caixas = db.Column(db.Integer, nullable=True)
    frete_status = db.Column(db.String(20), nullable=True)
    km_saida = db.Column(db.Float, nullable=True)
    km_chegada = db.Column(db.Float, nullable=True)
    valor_frete = db.Column(db.Float, nullable=True)
    pedagios = db.Column(db.Float, nullable=True)
    outras_despesas = db.Column(db.Float, nullable=True)
    produtor = db.Column(db.String(100), nullable=True)
    estado = db.Column(db.String(2), nullable=True)
    nota_fiscal = db.Column(db.String(50), nullable=True)
    data_nf = db.Column(db.DateTime, nullable=True)
    gta = db.Column(db.String(50), nullable=True)
    data_gta = db.Column(db.DateTime, nullable=True)
    aves_granja = db.Column(db.Integer, nullable=True)
    aves_mortas = db.Column(db.Integer, nullable=True)
    aves_recebidas = db.Column(db.Integer, nullable=True)
    aves_contador = db.Column(db.Integer, nullable=True)
    agenciador = db.Column(db.String(100), nullable=True)
    caixas_vazias = db.Column(db.Integer, default=0)
    peso_granja = db.Column(db.Float, nullable=True)
    peso_frigorifico = db.Column(db.Float, nullable=True)
    mortalidade_excesso = db.Column(db.Float, default=0)
    aves_molhadas_granja = db.Column(db.Float, default=0)
    aves_molhadas_chuva = db.Column(db.Float, default=0)
    quebra_maus_tratos = db.Column(db.Float, default=0)
    aves_papo_cheio = db.Column(db.Float, default=0)
    outras_quebras = db.Column(db.Float, default=0)
    descricao_quebras = db.Column(db.String(200))
    adiantamento_frete = db.Column(db.Float, default=0)
    valor_combustivel = db.Column(db.Float, default=0)  # Novo campo para preço do combustível
    valor_kg = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), default='incompleta')
    campos_pendentes = db.Column(db.String(200), nullable=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Campos de autorização da diretoria
    autorizado_por = db.Column(db.Integer, db.ForeignKey('user.id'))
    autorizado_por_usuario = db.relationship('User', foreign_keys=[autorizado_por])
    autorizada = db.Column(db.Boolean, default=False)
    data_autorizacao = db.Column(db.DateTime)
    assinatura_autorizador = db.Column(db.String(200))
    
    # Campos de verificação financeira
    verificado_por = db.Column(db.Integer, db.ForeignKey('user.id'))
    verificado_por_usuario = db.relationship('User', foreign_keys=[verificado_por])
    verificado_financeiro = db.Column(db.Boolean, default=False)
    aprovado_financeiro = db.Column(db.Boolean, default=False)
    data_aprovacao_financeiro = db.Column(db.DateTime)
    observacoes_financeiro = db.Column(db.String(500))
    requer_verificacao = db.Column(db.Boolean, default=False)
    em_edicao = db.Column(db.Boolean, default=False)
    
    # Campos de liberação do gerente
    liberado_gerente = db.Column(db.Boolean, default=False)
    liberado_por_gerente = db.Column(db.Integer, db.ForeignKey('user.id'))
    liberado_por_gerente_usuario = db.relationship('User', foreign_keys=[liberado_por_gerente])
    data_liberacao_gerente = db.Column(db.DateTime)

    @staticmethod
    def proximo_numero():
        ultimo_numero = db.session.query(db.func.max(Nota.numero)).scalar()
        return 1001 if ultimo_numero is None else ultimo_numero + 1

    def calcular_valor_total(self):
        # Peso no frigorífico menos todas as avarias
        peso_liquido = (self.peso_frigorifico or 0) - (
            (self.mortalidade_excesso or 0) +
            (self.aves_molhadas_granja or 0) +
            (self.aves_molhadas_chuva or 0) +
            (self.quebra_maus_tratos or 0) +
            (self.aves_papo_cheio or 0) +
            (self.outras_quebras or 0)
        )
        # Valor total é o peso líquido multiplicado pelo valor por kg
        return peso_liquido * (self.valor_kg or 0) if peso_liquido > 0 else 0

    def calcular_quebra_peso(self):
        # Diferença entre peso na granja e frigorífico
        return self.peso_granja - self.peso_frigorifico

    def calcular_valor_km(self):
        # Valor por km rodado
        km_total = self.km_chegada - self.km_saida
        if km_total > 0:
            return self.valor_frete / km_total
        return 0

    def verificar_completude(self):
        # Lista de campos obrigatórios
        campos_obrigatorios = [
            'numero', 'data_abate', 'tipo_ave', 'motorista',
            'placa_veiculo', 'peso_granja', 'peso_frigorifico',
            'valor_kg', 'valor_frete'
        ]
        
        for campo in campos_obrigatorios:
            valor = getattr(self, campo, None)
            if valor is None or (isinstance(valor, str) and not valor.strip()):
                return False
        return True

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def registrar_historico(nota, tipo_alteracao, descricao):
    historico = HistoricoNota(
        nota_id=nota.id,
        usuario_id=current_user.id,
        tipo_alteracao=tipo_alteracao,
        descricao=descricao
    )
    db.session.add(historico)
    db.session.commit()

# Rotas
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuário ou senha inválidos!', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    total_notas = Nota.query.count()
    notas_pendentes = Nota.query.filter_by(autorizada=False).count()
    notas_autorizadas = Nota.query.filter_by(autorizada=True).count()
    notas_financeiro = Nota.query.filter_by(autorizada=True, aprovado_financeiro=True).count()
    
    return render_template('dashboard.html',
                         total_notas=total_notas,
                         notas_pendentes=notas_pendentes,
                         notas_autorizadas=notas_autorizadas,
                         notas_financeiro=notas_financeiro)

@app.route('/nova_nota', methods=['GET', 'POST'])
@login_required
def nova_nota():
    if not current_user.can_create_notes:
        flash('Você não tem permissão para criar notas.', 'error')
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        # Verificar se algum campo obrigatório está vazio
        campos_obrigatorios = [
            'tipo_ave', 'num_cargas', 'ordem_carga', 'data_abate', 
            'motorista', 'transportadora', 'placa_veiculo', 'qtd_caixas',
            'frete_status', 'km_saida', 'km_chegada', 'valor_frete',
            'pedagios', 'outras_despesas', 'produtor', 'estado',
            'nota_fiscal', 'data_nf', 'gta', 'data_gta',
            'aves_granja', 'aves_mortas', 'aves_recebidas', 'aves_contador',
            'agenciador', 'peso_granja', 'peso_frigorifico', 'valor_kg'
        ]
        
        campos_vazios = []
        for campo in campos_obrigatorios:
            valor = request.form.get(campo, '').strip()
            if not valor:
                campos_vazios.append(campo)

        tem_campo_vazio = len(campos_vazios) > 0

        try:
            # Função auxiliar para converter valores numéricos
            def converter_numero(valor, tipo=float):
                try:
                    valor = valor.strip()
                    return tipo(valor) if valor else 0
                except (ValueError, AttributeError):
                    return 0

            nota = Nota(
                numero=Nota.proximo_numero(),
                usuario_id=current_user.id,  # Adicionar o ID do usuário atual
                tipo_ave=request.form.get('tipo_ave', ''),
                num_cargas=converter_numero(request.form.get('num_cargas', ''), int),
                ordem_carga=request.form.get('ordem_carga', ''),
                data_abate=datetime.strptime(request.form['data_abate'], '%Y-%m-%d') if request.form.get('data_abate') else None,
                dia_semana=datetime.strptime(request.form['data_abate'], '%Y-%m-%d').strftime('%A') if request.form.get('data_abate') else '',
                motorista=request.form.get('motorista', ''),
                transportadora=request.form.get('transportadora', ''),
                placa_veiculo=request.form.get('placa_veiculo', ''),
                qtd_caixas=converter_numero(request.form.get('qtd_caixas', ''), int),
                frete_status=request.form.get('frete_status', ''),
                km_saida=converter_numero(request.form.get('km_saida', '')),
                km_chegada=converter_numero(request.form.get('km_chegada', '')),
                valor_frete=converter_numero(request.form.get('valor_frete', '')),
                pedagios=converter_numero(request.form.get('pedagios', '')),
                outras_despesas=converter_numero(request.form.get('outras_despesas', '')),
                produtor=request.form.get('produtor', ''),
                estado=request.form.get('estado', ''),
                nota_fiscal=request.form.get('nota_fiscal', ''),
                data_nf=datetime.strptime(request.form['data_nf'], '%Y-%m-%d') if request.form.get('data_nf') else None,
                gta=request.form.get('gta', ''),
                data_gta=datetime.strptime(request.form['data_gta'], '%Y-%m-%d') if request.form.get('data_gta') else None,
                aves_granja=converter_numero(request.form.get('aves_granja', ''), int),
                aves_mortas=converter_numero(request.form.get('aves_mortas', ''), int),
                aves_recebidas=converter_numero(request.form.get('aves_recebidas', ''), int),
                aves_contador=converter_numero(request.form.get('aves_contador', ''), int),
                agenciador=request.form.get('agenciador', ''),
                caixas_vazias=converter_numero(request.form.get('caixas_vazias', ''), int),
                peso_granja=converter_numero(request.form.get('peso_granja', '')),
                peso_frigorifico=converter_numero(request.form.get('peso_frigorifico', '')),
                mortalidade_excesso=converter_numero(request.form.get('mortalidade_excesso', '')),
                aves_molhadas_granja=converter_numero(request.form.get('aves_molhadas_granja', '')),
                aves_molhadas_chuva=converter_numero(request.form.get('aves_molhadas_chuva', '')),
                quebra_maus_tratos=converter_numero(request.form.get('quebra_maus_tratos', '')),
                aves_papo_cheio=converter_numero(request.form.get('aves_papo_cheio', '')),
                outras_quebras=converter_numero(request.form.get('outras_quebras', '')),
                descricao_quebras=request.form.get('descricao_quebras', ''),
                adiantamento_frete=converter_numero(request.form.get('adiantamento_frete', '')),
                valor_combustivel=converter_numero(request.form.get('valor_combustivel', '')),
                valor_kg=converter_numero(request.form.get('valor_kg', '')),
                status='incompleta' if tem_campo_vazio else 'completa',
                campos_pendentes=', '.join(campos_vazios) if campos_vazios else None
            )
            
            db.session.add(nota)
            db.session.commit()
            
            registrar_historico(nota, 'criacao', f'Nota #{nota.numero} criada')
            
            if tem_campo_vazio:
                flash('Nota salva como incompleta. Campos pendentes: ' + ', '.join(campos_vazios), 'warning')
            else:
                flash('Nota criada com sucesso!', 'success')
            
            return redirect(url_for('lista_notas'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao salvar nota: {str(e)}', 'error')
            return redirect(url_for('nova_nota'))
    
    return render_template('nova_nota.html', novo_numero=Nota.proximo_numero())

@app.route('/ver_nota/<int:id>')
@login_required
def ver_nota(id):
    nota = Nota.query.get_or_404(id)
    return render_template('ver_nota.html', nota=nota)

@app.route('/editar_nota/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_nota(id):
    nota = Nota.query.get_or_404(id)
    
    # Permitir edição se a nota estiver incompleta ou se o usuário for o criador
    if nota.status != 'incompleta' and nota.usuario_id != current_user.id and not current_user.role in ['diretoria', 'gerente']:
        flash('Você não tem permissão para editar esta nota.', 'error')
        return redirect(url_for('ver_nota', id=id))
    
    # Verificar se a nota está autorizada pelo financeiro
    if nota.autorizada and current_user.role not in ['diretoria', 'gerente']:
        flash('Esta nota já foi autorizada e não pode ser editada.', 'error')
        return redirect(url_for('ver_nota', id=id))
    
    if request.method == 'POST':
        try:
            # Atualizar campos da nota
            nota.tipo_ave = request.form.get('tipo_ave')
            nota.num_cargas = request.form.get('num_cargas', type=int)
            nota.ordem_carga = request.form.get('ordem_carga')
            
            data_abate = request.form.get('data_abate')
            if data_abate:
                nota.data_abate = datetime.strptime(data_abate, '%Y-%m-%d')
            
            nota.dia_semana = request.form.get('dia_semana')
            nota.motorista = request.form.get('motorista')
            nota.transportadora = request.form.get('transportadora')
            nota.placa_veiculo = request.form.get('placa_veiculo')
            nota.qtd_caixas = request.form.get('qtd_caixas', type=int)
            nota.frete_status = request.form.get('frete_status')
            nota.km_saida = request.form.get('km_saida', type=float)
            nota.km_chegada = request.form.get('km_chegada', type=float)
            nota.valor_frete = request.form.get('valor_frete', type=float)
            nota.pedagios = request.form.get('pedagios', type=float)
            nota.outras_despesas = request.form.get('outras_despesas', type=float)
            nota.produtor = request.form.get('produtor')
            nota.estado = request.form.get('estado')
            nota.nota_fiscal = request.form.get('nota_fiscal')
            
            data_nf = request.form.get('data_nf')
            if data_nf:
                nota.data_nf = datetime.strptime(data_nf, '%Y-%m-%d')
            
            nota.gta = request.form.get('gta')
            
            data_gta = request.form.get('data_gta')
            if data_gta:
                nota.data_gta = datetime.strptime(data_gta, '%Y-%m-%d')
            
            nota.aves_granja = request.form.get('aves_granja', type=int)
            nota.aves_mortas = request.form.get('aves_mortas', type=int)
            nota.aves_recebidas = request.form.get('aves_recebidas', type=int)
            nota.aves_contador = request.form.get('aves_contador', type=int)
            nota.agenciador = request.form.get('agenciador')
            nota.caixas_vazias = request.form.get('caixas_vazias', type=int, default=0)
            nota.peso_granja = request.form.get('peso_granja', type=float)
            nota.peso_frigorifico = request.form.get('peso_frigorifico', type=float)
            nota.mortalidade_excesso = request.form.get('mortalidade_excesso', type=float, default=0)
            nota.aves_molhadas_granja = request.form.get('aves_molhadas_granja', type=float, default=0)
            nota.aves_molhadas_chuva = request.form.get('aves_molhadas_chuva', type=float, default=0)
            nota.quebra_maus_tratos = request.form.get('quebra_maus_tratos', type=float, default=0)
            nota.aves_papo_cheio = request.form.get('aves_papo_cheio', type=float, default=0)
            nota.outras_quebras = request.form.get('outras_quebras', type=float, default=0)
            nota.descricao_quebras = request.form.get('descricao_quebras', '')
            nota.valor_kg = request.form.get('valor_kg', type=float)
            nota.adiantamento_frete = request.form.get('adiantamento_frete', type=float, default=0)
            nota.valor_combustivel = request.form.get('valor_combustivel', type=float, default=0)
            
            # Verificar se todos os campos obrigatórios foram preenchidos
            campos_vazios = []
            campos_obrigatorios = [
                'tipo_ave', 'num_cargas', 'data_abate', 'motorista', 'transportadora',
                'placa_veiculo', 'qtd_caixas', 'produtor', 'nota_fiscal', 'data_nf',
                'gta', 'data_gta', 'aves_granja', 'peso_granja'
            ]
            
            for campo in campos_obrigatorios:
                valor = getattr(nota, campo)
                if valor is None or (isinstance(valor, str) and not valor.strip()):
                    campos_vazios.append(campo)
            
            if campos_vazios:
                nota.campos_pendentes = ', '.join(campos_vazios)
                nota.status = 'incompleta'
            else:
                nota.campos_pendentes = None
                nota.status = 'completa'
            
            # Registrar histórico
            registrar_historico(nota, 'edicao', 
                f'Nota editada por {current_user.username}')
            
            db.session.commit()
            flash('Nota atualizada com sucesso!', 'success')
            
            # Redirecionar com base no status da nota
            if nota.status == 'incompleta':
                return redirect(url_for('notas_incompletas'))
            else:
                return redirect(url_for('ver_nota', id=nota.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar a nota: {str(e)}', 'error')
    
    return render_template('editar_nota.html', nota=nota)

@app.route('/notas_incompletas')
@login_required
def notas_incompletas():
    # Buscar todas as notas incompletas independente do usuário
    notas = Nota.query.filter(
        (Nota.status == 'incompleta') |
        (Nota.campos_pendentes.isnot(None))
    ).order_by(Nota.data_criacao.desc()).all()
    
    return render_template('notas_incompletas.html', notas=notas)

@app.route('/autorizar_nota/<int:id>', methods=['GET', 'POST'])
@login_required
def autorizar_nota(id):
    if not current_user.is_diretoria:
        flash('Apenas diretoria pode autorizar notas.', 'error')
        return redirect(url_for('ver_nota', id=id))
        
    nota = Nota.query.get_or_404(id)
    if request.method == 'POST':
        senha = request.form.get('senha')
        assinatura = request.form.get('assinatura')
        user = User.query.get(current_user.id)
        
        if not user.check_password(senha):
            flash('Senha incorreta!', 'danger')
            return redirect(url_for('autorizar_nota', id=id))
            
        nota.autorizada = True
        nota.data_autorizacao = datetime.now()
        nota.autorizado_por = current_user.id
        nota.assinatura_autorizador = assinatura
        registrar_historico(nota, 'autorizacao', f'Nota #{nota.numero} autorizada pela diretoria')
        flash('Nota autorizada com sucesso!', 'success')
            
        db.session.commit()
        return redirect(url_for('lista_notas'))
        
    return render_template('autorizar_nota.html', nota=nota)

@app.route('/financeiro')
@login_required
def financeiro():
    if not current_user.is_financeiro:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('dashboard'))
        
    # Buscar apenas notas que foram autorizadas pela diretoria
    notas = Nota.query.filter_by(autorizada=True).order_by(Nota.data_autorizacao.desc()).all()
    return render_template('financeiro.html', notas=notas)

@app.route('/aprovar_financeiro/<int:id>', methods=['GET', 'POST'])
@login_required
def aprovar_financeiro(id):
    if not current_user.is_financeiro:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('dashboard'))
        
    nota = Nota.query.get_or_404(id)
    if request.method == 'POST':
        senha = request.form.get('senha')
        observacoes = request.form.get('observacoes')
        user = User.query.get(current_user.id)
        
        if not user.check_password(senha):
            flash('Senha incorreta!', 'danger')
            return redirect(url_for('aprovar_financeiro', id=id))
            
        nota.aprovado_financeiro = True
        nota.data_aprovacao_financeiro = datetime.now()
        nota.verificado_por = current_user.id
        nota.observacoes_financeiro = observacoes
        registrar_historico(nota, 'aprovacao_financeira', f'Nota #{nota.numero} aprovada pelo financeiro')
        
        db.session.commit()
        flash('Nota aprovada pelo financeiro com sucesso!', 'success')
        return redirect(url_for('financeiro'))
        
    return render_template('aprovar_financeiro.html', nota=nota)

@app.route('/aprovar_gerente/<int:id>', methods=['GET', 'POST'])
@login_required
def aprovar_gerente(id):
    if not current_user.is_gerente:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('dashboard'))
        
    nota = Nota.query.get_or_404(id)
    
    if request.method == 'POST':
        acao = request.form.get('acao')
        observacoes = request.form.get('observacoes', '')
        
        if acao == 'aprovar':
            nota.liberado_gerente = True
            nota.data_liberacao_gerente = datetime.now()
            nota.liberado_por_gerente = current_user.id
            nota.requer_verificacao = False
            nota.em_edicao = False  # Garante que a nota não está mais em edição
            registrar_historico(nota, 'aprovacao_gerente', f'Nota #{nota.numero} aprovada pelo gerente')
            flash('Nota verificada e aprovada com sucesso! Enviada para aprovação do financeiro.', 'success')
        elif acao == 'rejeitar':
            nota.em_edicao = True  # Permite nova edição
            nota.requer_verificacao = False
            nota.observacoes_financeiro = f"Rejeitado pelo gerente. Motivo: {observacoes}"
            registrar_historico(nota, 'rejeicao_gerente', f'Nota #{nota.numero} rejeitada pelo gerente. Motivo: {observacoes}')
            flash('Nota rejeitada. Retornada para edição.', 'info')
            
        db.session.commit()
        return redirect(url_for('gerente'))
        
    return render_template('aprovar_gerente.html', nota=nota)

@app.route('/buscar_notas')
@login_required
def buscar_notas():
    termo = request.args.get('termo', '')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    status = request.args.get('status', 'todas')
    
    query = Nota.query
    
    if termo:
        query = query.filter(
            db.or_(
                Nota.produtor.ilike(f'%{termo}%'),
                Nota.motorista.ilike(f'%{termo}%'),
                Nota.transportadora.ilike(f'%{termo}%'),
                Nota.nota_fiscal.ilike(f'%{termo}%'),
                Nota.gta.ilike(f'%{termo}%')
            )
        )
    
    if data_inicio:
        query = query.filter(Nota.data_criacao >= datetime.strptime(data_inicio, '%Y-%m-%d'))
    if data_fim:
        query = query.filter(Nota.data_criacao <= datetime.strptime(data_fim, '%Y-%m-%d') + timedelta(days=1))
        
    if status == 'pendente':
        query = query.filter_by(autorizada=False)
    elif status == 'autorizada':
        query = query.filter_by(autorizada=True)
    elif status == 'financeiro':
        query = query.filter_by(autorizada=True, aprovado_financeiro=True)
    elif status == 'incompleta':
        query = query.filter_by(status='incompleta')
        
    notas = query.order_by(Nota.data_criacao.desc()).all()
    
    return render_template('buscar_notas.html', 
                         notas=notas, 
                         termo=termo,
                         data_inicio=data_inicio,
                         data_fim=data_fim,
                         status=status)

@app.route('/lista_notas')
@login_required
def lista_notas():
    status = request.args.get('status', 'todas')
    query = Nota.query
    
    if status == 'pendente':
        query = query.filter_by(autorizada=False)
    elif status == 'autorizada':
        query = query.filter_by(autorizada=True)
    elif status == 'financeiro':
        query = query.filter_by(autorizada=True, verificado_financeiro=False)
        
    notas = query.order_by(Nota.data_criacao.desc()).all()
    
    return render_template('lista_notas.html', 
                         notas=notas,
                         status=status)

@app.route('/buscar_nota')
@login_required
def buscar_nota():
    return render_template('buscar_nota.html')

@app.route('/usuarios')
@login_required
def lista_usuarios():
    if not current_user.is_diretoria:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('dashboard'))
    
    usuarios = User.query.all()
    return render_template('usuarios.html', usuarios=usuarios)

@app.route('/novo_usuario', methods=['GET', 'POST'])
@login_required
def novo_usuario():
    if not current_user.is_diretoria:
        flash('Acesso negado!', 'error')
        return redirect(url_for('lista_usuarios'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        nome_completo = request.form['nome_completo']
        email = request.form['email']
        
        if User.query.filter_by(username=username).first():
            flash('Nome de usuário já existe!', 'error')
            return redirect(url_for('novo_usuario'))
            
        if role not in ['diretoria', 'financeiro', 'usuario', 'visualizador', 'gerente']:
            flash('Tipo de usuário inválido!', 'error')
            return redirect(url_for('novo_usuario'))
            
        user = User(
            username=username,
            role=role,
            nome_completo=nome_completo,
            email=email,
            criado_por_id=current_user.id
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Usuário criado com sucesso!', 'success')
        return redirect(url_for('lista_usuarios'))
        
    return render_template('novo_usuario.html')

@app.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_usuario(id):
    if not current_user.is_diretoria:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('dashboard'))
        
    user = User.query.get_or_404(id)
    
    if request.method == 'POST':
        user.username = request.form.get('username')
        user.role = request.form.get('role')
        user.nome_completo = request.form.get('nome_completo')
        user.email = request.form.get('email')
        user.ativo = 'ativo' in request.form
        
        password = request.form.get('password')
        if password:  # Só atualiza senha se foi fornecida
            user.set_password(password)
            
        db.session.commit()
        flash('Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('lista_usuarios'))
        
    return render_template('editar_usuario.html', user=user)

@app.route('/desativar_usuario/<int:id>')
@login_required
def desativar_usuario(id):
    if not current_user.is_diretoria:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('dashboard'))
        
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('Você não pode desativar seu próprio usuário!', 'danger')
        return redirect(url_for('lista_usuarios'))
        
    user.ativo = False
    db.session.commit()
    flash('Usuário desativado com sucesso!', 'success')
    return redirect(url_for('lista_usuarios'))

@app.route('/api/excluir_nota/<int:id>', methods=['DELETE'])
@login_required
def excluir_nota(id):
    try:
        nota = Nota.query.get_or_404(id)
        db.session.delete(nota)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/solicitar_verificacao/<int:id>', methods=['POST'])
@login_required
def solicitar_verificacao(id):
    if not current_user.is_financeiro:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('dashboard'))
        
    nota = Nota.query.get_or_404(id)
    if not nota.autorizada:
        flash('A nota precisa estar autorizada para solicitar verificação.', 'error')
        return redirect(url_for('ver_nota', id=id))
    
    observacoes = request.form.get('observacoes')
    if not observacoes:
        flash('É necessário incluir observações sobre o que precisa ser verificado.', 'error')
        return redirect(url_for('ver_nota', id=id))
    
    nota.requer_verificacao = True
    nota.em_edicao = True  # Nova flag para permitir edição
    nota.observacoes_financeiro = observacoes
    nota.verificado_financeiro = False
    nota.liberado_gerente = False
    db.session.commit()
    
    flash('Nota enviada para verificação. Os usuários poderão editar conforme solicitado.', 'success')
    return redirect(url_for('lista_notas'))

@app.route('/gerente')
@login_required
def gerente():
    if not current_user.is_gerente:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('dashboard'))
        
    notas = Nota.query.filter_by(requer_verificacao=True, liberado_gerente=False).all()
    return render_template('gerente.html', notas=notas)

@app.route('/liberar_nota/<int:id>', methods=['POST'])
@login_required
def liberar_nota(id):
    if not current_user.is_gerente:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('dashboard'))
        
    nota = Nota.query.get_or_404(id)
    nota.liberado_gerente = True
    nota.data_liberacao_gerente = datetime.now()
    nota.liberado_por_gerente = current_user.id
    db.session.commit()
    
    flash('Nota liberada para edição.', 'success')
    return redirect(url_for('gerente'))

@app.route('/historico_nota/<int:id>')
@login_required
def historico_nota(id):
    nota = Nota.query.get_or_404(id)
    return render_template('historico_nota.html', nota=nota)

@app.route('/dashboard_precos')
@login_required
def dashboard_precos():
    if not (current_user.is_financeiro or current_user.is_diretoria or current_user.is_gerente):
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('dashboard'))
    return render_template('dashboard_precos.html')

@app.route('/api/dados_dashboard')
@login_required
def dados_dashboard():
    if not (current_user.is_financeiro or current_user.is_diretoria or current_user.is_gerente):
        return jsonify({'error': 'Acesso não autorizado'}), 403
    tipo_periodo = request.args.get('tipo_periodo', 'mes')
    data_inicial = datetime.strptime(request.args.get('data_inicial'), '%Y-%m-%d')
    data_final = datetime.strptime(request.args.get('data_final'), '%Y-%m-%d')

    # Query base
    query = Nota.query.filter(
        Nota.data_abate.between(data_inicial, data_final)
    )

    # Calcular métricas
    metricas = {
        'media_frete': query.with_entities(func.avg(Nota.valor_frete)).scalar() or 0,
        'total_cargas': query.count(),
        'media_combustivel': query.with_entities(func.avg(Nota.valor_combustivel)).scalar() or 0,
        'custo_total': query.with_entities(
            func.sum(Nota.valor_frete + Nota.pedagios + Nota.valor_combustivel + Nota.outras_despesas)
        ).scalar() or 0
    }

    # Preparar dados para gráficos
    if tipo_periodo == 'dia':
        group_by = func.date(Nota.data_abate)
        format_label = lambda x: x.strftime('%d/%m/%Y')
    elif tipo_periodo == 'semana':
        group_by = func.strftime('%Y-%W', Nota.data_abate)
        format_label = lambda x: f'Semana {x[5:]}/{x[:4]}'
    else:  # mes
        group_by = func.strftime('%Y-%m', Nota.data_abate)
        format_label = lambda x: f'{x[5:]}/{x[:4]}'

    evolucao = db.session.query(
        group_by.label('periodo'),
        func.avg(Nota.valor_frete).label('media_frete'),
        func.count(Nota.id).label('total_cargas'),
        func.avg(Nota.valor_combustivel).label('media_combustivel'),
        func.sum(Nota.valor_frete + Nota.pedagios + Nota.valor_combustivel + Nota.outras_despesas).label('custo_total')
    ).filter(
        Nota.data_abate.between(data_inicial, data_final)
    ).group_by('periodo').all()

    # Calcular distribuição de custos
    custos_totais = db.session.query(
        func.sum(Nota.valor_frete).label('frete'),
        func.sum(Nota.pedagios).label('pedagios'),
        func.sum(Nota.valor_combustivel).label('combustivel'),
        func.sum(Nota.outras_despesas).label('outras_despesas')
    ).filter(
        Nota.data_abate.between(data_inicial, data_final)
    ).first()

    return jsonify({
        'metricas': metricas,
        'graficos': {
            'evolucao_precos': {
                'labels': [format_label(p[0]) for p in evolucao],
                'valores': [float(p[1]) for p in evolucao]
            },
            'distribuicao_custos': {
                'frete': float(custos_totais.frete or 0),
                'pedagios': float(custos_totais.pedagios or 0),
                'combustivel': float(custos_totais.combustivel or 0),
                'outras_despesas': float(custos_totais.outras_despesas or 0)
            }
        }
    })

def criar_usuarios_padrao():
    usuarios = [
        {
            'username': 'diretoria',
            'password': 'diretoria123',
            'role': 'diretoria',
            'nome_completo': 'Usuário Diretoria',
            'email': 'diretoria@empresa.com'
        },
        {
            'username': 'financeiro',
            'password': 'financeiro123',
            'role': 'financeiro',
            'nome_completo': 'Usuário Financeiro',
            'email': 'financeiro@empresa.com'
        },
        {
            'username': 'gerente',
            'password': 'gerente123',
            'role': 'gerente',
            'nome_completo': 'Usuário Gerente',
            'email': 'gerente@empresa.com'
        },
        {
            'username': 'usuario',
            'password': 'usuario123',
            'role': 'usuario',
            'nome_completo': 'Usuário Padrão',
            'email': 'usuario@empresa.com'
        },
        {
            'username': 'visualizador',
            'password': 'visualizador123',
            'role': 'visualizador',
            'nome_completo': 'Usuário Visualizador',
            'email': 'visualizador@empresa.com'
        }
    ]
    
    for user_data in usuarios:
        # Verificar se o usuário já existe
        if not User.query.filter_by(username=user_data['username']).first():
            user = User(
                username=user_data['username'],
                role=user_data['role'],
                nome_completo=user_data['nome_completo'],
                email=user_data['email'],
                ativo=True
            )
            user.set_password(user_data['password'])
            db.session.add(user)
    
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        criar_usuarios_padrao()
        
        # Criar usuário inicial da diretoria se não existir
        if not User.query.filter_by(username='diretoria').first():
            user = User(
                username='diretoria',
                role='diretoria',
                nome_completo='Administrador do Sistema',
                email='admin@empresa.com',
                ativo=True
            )
            user.set_password('diretoria123')
            db.session.add(user)
            db.session.commit()
            
    app.run(host='0.0.0.0', debug=True)
