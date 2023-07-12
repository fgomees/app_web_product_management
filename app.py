from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, logout_user, LoginManager, current_user, login_required




app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///../database/projeto.db"
app.config['SECRET_KEY'] = "flavio_gomes"
db = SQLAlchemy(app)

login_manager = LoginManager(app)



@login_manager.user_loader
def get_user(user_id):
    return User.query.filter_by(id=user_id).first()


#Classe dos utilizadores
class User(db.Model, UserMixin):
    __tablename__= 'users'
    id = db.Column(db.Integer, autoincrement = True, primary_key=True)
    username = db.Column(db.String, nullable = False)
    password = db.Column(db.String, nullable=False)
    access_level = db.Column(db.String, nullable = False)


    def __init__(self, username, password, access_level):
        self.username = username
        self.password = generate_password_hash(password)
        self.access_level = access_level

    def verify_password(self,pwd):
        return check_password_hash(self.password,pwd)

    @property
    def is_admin(self):
        return self.access_level == 1

    @property
    def is_user(self):
        return self.access_level == 2

    @property
    def is_fornecedor(self):
        return self.access_level == 3


#dashboard para reencaminhar cada tipo de utilizador
@app.route('/dashboard')

@login_required
def dashboard():
    if current_user.is_admin:
        produto = Produto.query.all()
        return render_template('admin.html',  produto = produto)
    elif current_user.is_user:
        return render_template('user.html')
    elif current_user.is_fornecedor:
        return render_template('fornecedor.html')
    else:
        return render_template('index.html')



#logout
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))



#página inicial
@app.route('/')
def home():
    todos_os_produtos = Produto.query.all()
    db.session.commit()




    return render_template("index_2.html", produtos = todos_os_produtos)



#registo novos users, apenas acessivel pelo admin
@app.route('/registo', methods = ['GET', 'POST'])
def registo():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        access_level = request.form['access_level']

        user = User(username, password, access_level)
        db.session.add(user)
        db.session.commit()

    return render_template('registo.html')


#página login
@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        pwd = request.form['password']

        user = User.query.filter_by(username=username).first()


        if not user or not user.verify_password(pwd):
            return redirect(url_for('login'))


        login_user(user)


        return redirect(url_for('dashboard'))

    return render_template("login.html")



#Produtos
class Produto(db.Model, UserMixin):
    __tablename__= 'produtos'
    id = db.Column(db.Integer, autoincrement = True, primary_key=True)
    descricao = db.Column(db.String, nullable = False)
    quantidade = db.Column(db.Integer, nullable=False, unique = True)
    localizacao = db.Column(db.String, nullable = False)
    preco_compra = db.Column(db.Integer, nullable=False)
    iva = db.Column(db.Integer, nullable=False)
    qtd_recomendada = db.Column(db.Integer, nullable=False)
    preco_venda = db.Column(db.Integer, nullable=False)


    def __init__(self, descricao, quantidade, localizacao, qtd_rmd):
        self.descricao = descricao
        self.localizacao = localizacao
        self.quantidade = quantidade
        self.preco_compra = 0
        self.iva = 0
        self.qtd_recomendada = qtd_rmd

    def has_alert(self):
        return self.quantidade < 0.1 * self.qtd_recomendada



#registar um novo produto
@app.route('/novo_produto', methods = ['GET', 'POST'])
def novo_produto():
    if request.method == 'POST':
        descricao = request.form['descricao']
        localizacao= request.form['localizacao']
        preco = 0
        quantidade = 0
        iva = request.form['iva']
        qtd_recomendada = request.form['qtd_rmd']


        produto = Produto(descricao, quantidade ,localizacao, preco, iva,qtd_recomendada)

        db.session.add(produto)
        db.session.commit()

    return render_template('novo_produto.html')





#Compras

class Compra(db.Model):
    __tablename__= 'compras'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=False)
    id_fornecedor = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco_sem_iva = db.Column(db.Float, nullable=False)
    iva = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)


    def __init__(self, produto_id, id_forn,preco_s_iva,iva,  quantidade):

        self.produto_id = produto_id
        self.id_fornecedor = id_forn
        self.preco_sem_iva = preco_s_iva
        self.iva = iva
        self.quantidade = quantidade
        self.total = (preco_s_iva*iva)*quantidade


@app.route('/compra', methods=['GET', 'POST'])
def compra():
    if request.method == 'POST':
        produto_id = request.form['produto_id']
        fornecedor = request.form['fornecedor']
        preco = float(request.form['preco'])
        iva = float(request.form['iva'])
        quantidade = float(request.form['quantidade'])



        produto = Produto.query.filter_by(id=produto_id).first()

        # Registra na tabela de compras
        compra = Compra(produto_id, fornecedor, preco, iva, quantidade)
        db.session.add(compra)

        # Atualizar os valores
        produto.quantidade += quantidade
        produto.iva = iva
        produto.preco_compra = preco
        produto.preco_venda = preco*1.30 #valor de venda sem iva

        db.session.commit()


        return redirect(url_for('compra'))

    produto_id = request.args.get('id')
    produto = Produto.query.filter_by(id=produto_id).first()
    lista_produtos = Produto.query.all()

    return render_template('compra.html', produto=produto, lista_produtos=lista_produtos )



#vendas

class Venda(db.Model):
    __tablename__ = 'vendas'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=False)
    id_user = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    preco_venda = db.Column(db.Float, nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Float, nullable=False)

    def __init__(self, produto_id, id_user, preco_venda, quantidade):
        self.produto_id = produto_id
        self.id_user = id_user
        self.preco_venda = preco_venda
        self.quantidade = quantidade
        self.total = preco_venda * quantidade




@app.route('/venda', methods=['GET', 'POST'])
@login_required
def venda():
    if request.method == 'POST':
        produto_id = request.form['produto_id']
        quantidade = float(request.form['quantidade'])

        produto = Produto.query.filter_by(id=produto_id).first()

        if produto and quantidade <= produto.quantidade:
            # Calcula o preço de venda multiplicando o preço de compra por 2
            preco_venda = produto.preco_compra * 2

            # Registra na tabela de vendas
            venda = Venda(produto_id, current_user.id, preco_venda, quantidade)
            db.session.add(venda)

            # Atualiza a quantidade do produto
            produto.quantidade -= quantidade

            db.session.commit()

            return redirect(url_for('venda'))

    produto_id = request.args.get('id')
    produto = Produto.query.filter_by(id=produto_id).first()
    lista_produtos = Produto.query.all()

    return render_template('venda.html', produto=produto, lista_produtos=lista_produtos)






from matplotlib import pyplot as plt

#gráfico de vendas
@app.route('/grafico_compras')
def grafico_compras():

    # consulta SQL para selecionar a quantidade de cada produto comprado pelo usuário logado
    compras = db.session.query(Produto.descricao, db.func.sum(Compra.quantidade)). \
        join(Compra, Compra.produto_id == Produto.id). \
        filter(Compra.id_fornecedor == current_user.id). \
        group_by(Produto.descricao). \
        order_by(db.func.sum(Compra.quantidade).desc()). \
        all()


    labels = [row[0] for row in compras]
    values = [row[1] for row in compras]

    plt.bar(labels, values)
    plt.title('Quantidade de vendas por produto')
    plt.xlabel('Produtos')
    plt.ylabel('Quantidade')
    plt.title('Produtos comprados pelo usuário')
    plt.show()

    return redirect(url_for('dashboard'))




@app.route('/grafico_vendas')
def grafico_vendas():
    # Consulta SQL para selecionar a quantidade de cada produto vendido pelo usuário logado
    vendas = db.session.query(Produto.descricao, db.func.sum(Venda.quantidade)). \
        join(Venda, Venda.produto_id == Produto.id). \
        filter(Venda.id_user == current_user.id). \
        group_by(Produto.descricao). \
        order_by(db.func.sum(Venda.quantidade).desc()). \
        all()

    labels = [row[0] for row in vendas]
    values = [row[1] for row in vendas]

    plt.bar(labels, values)
    plt.title('Quantidade de vendas por produto')
    plt.xlabel('Produtos')
    plt.ylabel('Quantidade')
    plt.show()

    return redirect(url_for('dashboard'))


@app.route('/grafico_comparativo')
def grafico_comparativo():
    # Consulta base de dados para calcular a soma total do dinheiro gasto em compras
    total_compras = db.session.query(db.func.sum(Compra.total)).first()[0]

    # Consulta base de dados para calcular a soma total do dinheiro obtido com as vendas
    total_vendas = db.session.query(db.func.sum(Venda.total)).first()[0]

    labels = ['Compras', 'Vendas']
    values = [total_compras, total_vendas]

    plt.bar(labels, values)
    plt.title('Finanças')
    plt.xlabel('Operação')
    plt.ylabel('Dinheiro')
    plt.show()

    return redirect(url_for('dashboard'))

#lista de produtos disponiveis


from datetime import datetime

@app.route('/produtos_disponiveis')
def produtos_disponiveis():
    produtos = Produto.query.all()
    produtos_disponiveis = []

    for produto in produtos:
        # Consulta SQL para obter a última compra desse produto
        ultima_compra = Compra.query.filter_by(produto_id=produto.id).order_by(Compra.id.desc()).first()

        # Verificar se houve alguma compra registrada para o produto
        if ultima_compra:
            # Calcular o preço de venda multiplicando o preço de compra por 2
            preco_venda = ultima_compra.preco_sem_iva * 2
        else:
            # Se não houver compras registradas, definir o preço de venda como 0
            preco_venda = 0

        # Verificar se o produto está disponível com base na quantidade
        if produto.quantidade > 0:
            # Criar um dicionário com as informações do produto disponível
            produto_disponivel = {
                'descricao': produto.descricao,
                'preco_venda': preco_venda,
                'quantidade': produto.quantidade,
                'data_disponibilidade': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            produtos_disponiveis.append(produto_disponivel)

    return render_template('produtos_disponiveis.html', produtos=produtos_disponiveis)







if __name__ == '__main__':
    app.run(debug=True)