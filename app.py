from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Настройки для загрузки файлов
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['AVATAR_FOLDER'] = 'static/avatars'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'svg'}

# Создаем папки если их нет
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['AVATAR_FOLDER'], exist_ok=True)
os.makedirs('static/images', exist_ok=True)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# ==================== МОДЕЛИ БАЗЫ ДАННЫХ ====================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    avatar = db.Column(db.String(200), default='default_avatar.png')
    full_name = db.Column(db.String(100), default='')
    phone = db.Column(db.String(20), default='')
    address = db.Column(db.String(200), default='')
    bio = db.Column(db.Text, default='')
    orders = db.relationship('Order', backref='user', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(200), default='default.jpg')
    stock = db.Column(db.Integer, default=0)
    category = db.Column(db.String(50), default='flowers')
    discount = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending')
    address = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    product = db.relationship('Product', backref='order_items')

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_discounted_price(product):
    if product.discount and product.discount > 0:
        return product.price * (1 - product.discount / 100)
    return product.price

# ==================== СОЗДАНИЕ БАЗЫ ДАННЫХ ====================

with app.app_context():
    db.create_all()
    
    # Создаем тестового пользователя если нет
    if not User.query.filter_by(username='user').first():
        user = User(
            username='user',
            email='user@example.com',
            password=bcrypt.generate_password_hash('user123').decode('utf-8'),
            full_name='Иван Петров',
            phone='+7 (999) 888-77-66',
            bio='Люблю цветы и природу'
        )
        db.session.add(user)
        print("👤 Создан тестовый пользователь: user / user123")
    
    # Создаем товары только если их нет
    if Product.query.count() == 0:
        test_products = [
            Product(name='Красная Роза', description='Красивые красные розы - символ любви и страсти', price=299, stock=50, category='roses', discount=10),
            Product(name='Белая Лилия', description='Элегантные белые лилии со свежим ароматом', price=349, stock=30, category='lilies', discount=0),
            Product(name='Желтый Тюльпан', description='Яркие желтые тюльпаны, которые приносят радость', price=249, stock=45, category='tulips', discount=15),
            Product(name='Смешанный Букет', description='Красивая смесь сезонных цветов. Отличный подарок', price=499, stock=25, category='bouquet', discount=0),
            Product(name='Розовый Пион', description='Нежные розовые пионы с сладким ароматом', price=399, stock=20, category='flowers', discount=20),
            Product(name='Орхидея', description='Экзотическая орхидея - символ красоты и изысканности', price=599, stock=15, category='flowers', discount=0),
        ]
        for product in test_products:
            db.session.add(product)
        print(f"📦 Добавлено {len(test_products)} тестовых товаров")
    
    db.session.commit()
    
    print("=" * 50)
    print("✅ База данных готова!")
    print("👤 Пользователь: user / user123")
    print("=" * 50)

# ==================== МАРШРУТЫ ====================

@app.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)

@app.route('/product/<int:id>')
def product_detail(id):
    product = Product.query.get_or_404(id)
    return render_template('product_detail.html', product=product)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        
        if User.query.filter_by(username=username).first():
            flash('Имя пользователя уже существует', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email уже зарегистрирован', 'danger')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Регистрация успешна! Теперь вы можете войти.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            flash(f'С возвращением, {username}!', 'success')
            return redirect(url_for('index'))  # Всегда на главную, даже если админ
        else:
            flash('Неверное имя пользователя или пароль', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из аккаунта', 'info')
    return redirect(url_for('index'))

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в аккаунт', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        user.full_name = request.form.get('full_name', '')
        user.phone = request.form.get('phone', '')
        user.address = request.form.get('address', '')
        user.bio = request.form.get('bio', '')
        
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and allowed_file(file.filename):
                if user.avatar != 'default_avatar.png':
                    old_path = os.path.join(app.config['AVATAR_FOLDER'], user.avatar)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename
                file.save(os.path.join(app.config['AVATAR_FOLDER'], filename))
                user.avatar = filename
        
        db.session.commit()
        flash('Профиль успешно обновлен!', 'success')
        return redirect(url_for('account'))
    
    return render_template('edit_profile.html', user=user)

@app.route('/account')
def account():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в аккаунт', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()
    return render_template('account.html', user=user, orders=orders)

@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    if 'user_id' not in session:
        flash('Войдите в аккаунт, чтобы добавить товары в корзину', 'warning')
        return redirect(url_for('login'))
    
    if 'cart' not in session:
        session['cart'] = {}
    
    cart = session['cart']
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    session['cart'] = cart
    session.modified = True
    
    product = Product.query.get(product_id)
    flash(f'{product.name} добавлен в корзину!', 'success')
    return redirect(request.referrer or url_for('index'))

@app.route('/cart')
def cart():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    cart_items = []
    total = 0
    
    if 'cart' in session:
        for product_id, quantity in session['cart'].items():
            product = Product.query.get(int(product_id))
            if product:
                price = get_discounted_price(product)
                subtotal = price * quantity
                total += subtotal
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'subtotal': subtotal,
                    'discounted_price': price
                })
    
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/update_cart', methods=['POST'])
def update_cart():
    for key, value in request.form.items():
        if key.startswith('quantity_'):
            product_id = key.split('_')[1]
            quantity = int(value)
            
            if quantity <= 0:
                if 'cart' in session and product_id in session['cart']:
                    del session['cart'][product_id]
            else:
                if 'cart' not in session:
                    session['cart'] = {}
                session['cart'][product_id] = quantity
    
    session.modified = True
    flash('Корзина обновлена!', 'success')
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['POST'])
def checkout():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if 'cart' not in session or not session['cart']:
        flash('Корзина пуста', 'warning')
        return redirect(url_for('cart'))
    
    total = 0
    order_items = []
    
    for product_id, quantity in session['cart'].items():
        product = Product.query.get(int(product_id))
        if product and product.stock >= quantity:
            price = get_discounted_price(product)
            subtotal = price * quantity
            total += subtotal
            order_items.append((product, quantity, price))
        else:
            flash(f'Недостаточно товара: {product.name}', 'danger')
            return redirect(url_for('cart'))
    
    order = Order(
        user_id=session['user_id'],
        total_amount=total,
        status='pending',
        address=request.form.get('address', '')
    )
    db.session.add(order)
    db.session.commit()
    
    for product, quantity, price in order_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=quantity,
            price=price
        )
        db.session.add(order_item)
        product.stock -= quantity
    
    db.session.commit()
    session.pop('cart', None)
    
    flash(f'Заказ успешно оформлен! Сумма: {total:.2f} ₽', 'success')
    return redirect(url_for('account'))

if __name__ == '__main__':
    app.run(debug=True)