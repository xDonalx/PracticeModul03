from flask import Flask, redirect, url_for, request, flash, session, render_template
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = '0c03969c43eecf41b62f80ba59250e43'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:\\Users\\lllBB\\PycharmProjects\\pythonProject3\\b_store20.db'
app.config['UPLOAD_FOLDER'] = 'static/images'
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    profile_picture = db.Column(db.String(150), nullable=True)
    first_name = db.Column(db.String(150), nullable=True)
    last_name = db.Column(db.String(150), nullable=True)
    patronymic = db.Column(db.String(150), nullable=True)
    address = db.Column(db.String(250), nullable=True)
    phone_number = db.Column(db.String(50), nullable=True)
    about_me = db.Column(db.Text, nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    favorites = db.relationship('Favorite', backref='user', lazy=True)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(150), nullable=False)
    favorites = db.relationship('Favorite', backref='product', lazy=True)


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(150), nullable=True)


class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


with app.app_context():
    db.create_all()


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('products'))
        flash('Неверное имя пользователя или пароль!')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))


@app.route('/products')
def products():
    products_list = Product.query.all()
    return render_template('products.html', products=products_list)


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    is_favorite = False

    if 'user_id' in session:
        is_favorite = Favorite.query.filter_by(
            user_id=session['user_id'],
            product_id=product.id
        ).first() is not None

    return render_template('product_detail.html',
                           product=product,
                           is_favorite=is_favorite)


@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if 'user_id' not in session:
        flash('Войдите в систему')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if not user.is_admin:
        flash('Только администраторы могут добавлять товары')
        return redirect(url_for('products'))

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        image = request.files['image']

        if not name or not description or not price:
            flash('Заполните все обязательные поля')
            return redirect(url_for('add_product'))

        try:
            price = float(price)
            if price <= 0:
                flash('Цена должна быть больше нуля')
                return redirect(url_for('add_product'))
        except ValueError:
            flash('Введите корректную цену')
            return redirect(url_for('add_product'))

        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)

            new_product = Product(
                name=name,
                description=description,
                price=price,
                image=filename
            )
            db.session.add(new_product)
            db.session.commit()
            flash('Товар успешно добавлен!')
            return redirect(url_for('products'))
        else:
            flash('Допустимы только изображения (png, jpg, jpeg)')

    return render_template('add_product.html')


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}


@app.route('/delete_product/<int:product_id>')
def delete_product(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if not user.is_admin:
        flash('Только администраторы могут удалять товары')
        return redirect(url_for('products'))

    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Товар успешно удален!')
    return redirect(url_for('products'))


@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    quantity = int(request.args.get('quantity', 1))
    product = Product.query.get_or_404(product_id)

    if 'cart' not in session:
        session['cart'] = []

    cart = session['cart']

    for item in cart:
        if item['id'] == product.id:
            item['quantity'] += quantity
            session.modified = True
            flash(f'Количество товара "{product.name}" увеличено до {item["quantity"]}.')
            return redirect(url_for('view_cart'))

    cart.append({
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'quantity': quantity
    })
    session.modified = True
    flash(f'Товар "{product.name}" добавлен в корзину в количестве {quantity}.')
    return redirect(url_for('view_cart'))


@app.route('/cart')
def view_cart():
    cart = session.get('cart', [])
    total_amount = sum(item['price'] * item['quantity'] for item in cart)
    return render_template('cart.html', cart=cart, total_amount=total_amount)


@app.route('/clear_cart')
def clear_cart():
    session.pop('cart', None)
    flash('Корзина успешно очищена.')
    return redirect(url_for('view_cart'))


@app.route('/checkout')
def checkout():
    cart = session.get('cart', [])
    if not cart:
        flash('Ваша корзина пуста!')
        return redirect(url_for('products'))
    return render_template('checkout.html', cart=cart)


@app.route('/confirm_purchase')
def confirm_purchase():
    if 'cart' not in session or not session['cart']:
        flash('Ваша корзина пуста!')
        return redirect(url_for('products'))

    session.pop('cart', None)
    flash('Покупка успешно оформлена! Спасибо за заказ!')
    return redirect(url_for('products'))


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        if 'avatar' in request.files:
            avatar = request.files['avatar']
            if avatar.filename != '':
                avatar_name = secure_filename(avatar.filename)
                avatar.save(os.path.join(app.config['UPLOAD_FOLDER'], avatar_name))
                user.profile_picture = avatar_name

        user.first_name = request.form['first_name']
        user.last_name = request.form['last_name']
        user.patronymic = request.form['patronymic']
        user.address = request.form['address']
        user.phone_number = request.form['phone_number']
        user.about_me = request.form['about_me']

        secret_key = request.form.get('secret_key')
        if secret_key == 'QWE123' and not user.is_admin:
            user.is_admin = True
            flash('Вы получили права администратора!')

        db.session.commit()
        flash('Профиль успешно обновлен!')
        return redirect(url_for('profile'))

    return render_template('profile.html', user=user)


@app.route('/reviews', methods=['GET', 'POST'])
def reviews():
    if request.method == 'POST':
        username = request.form.get('username', 'Аноним')
        rating = int(request.form['rating'])
        description = request.form['description']
        image = request.files.get('image')

        if not description:
            flash('Введите текст отзыва!')
            return redirect(url_for('reviews'))

        if image and image.filename != '':
            image_name = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_name))
            new_review = Review(
                username=username,
                rating=rating,
                description=description,
                image=image_name
            )
        else:
            new_review = Review(
                username=username,
                rating=rating,
                description=description
            )

        db.session.add(new_review)
        db.session.commit()
        flash('Ваш отзыв успешно добавлен!')

    reviews_list = Review.query.order_by(Review.id.desc()).all()
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    return render_template('reviews.html', reviews=reviews_list, user=user)


@app.route('/delete_review/<int:review_id>')
def delete_review(review_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if not user.is_admin:
        flash('Только администраторы могут удалять отзывы!')
        return redirect(url_for('reviews'))

    review = Review.query.get_or_404(review_id)
    db.session.delete(review)
    db.session.commit()
    flash('Отзыв успешно удален!')
    return redirect(url_for('reviews'))


@app.route('/add_favorite/<int:product_id>')
def add_favorite(product_id):
    if 'user_id' not in session:
        flash('Войдите, чтобы добавлять товары в избранное!')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    product = Product.query.get(product_id)

    if not product:
        flash('Товар не найден!')
        return redirect(url_for('products'))

    existing = Favorite.query.filter_by(
        user_id=user.id,
        product_id=product.id
    ).first()

    if existing:
        flash('Товар уже в избранном!')
    else:
        new_fav = Favorite(user_id=user.id, product_id=product.id)
        db.session.add(new_fav)
        db.session.commit()
        flash('Товар добавлен в избранное!')

    return redirect(url_for('product_detail', product_id=product_id))


@app.route('/remove_favorite/<int:product_id>')
def remove_favorite(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    fav = Favorite.query.filter_by(
        user_id=session['user_id'],
        product_id=product_id
    ).first()

    if fav:
        db.session.delete(fav)
        db.session.commit()
        flash('Товар был удален из избранного!')

    return redirect(request.referrer or url_for('favorites'))

@app.route('/favorites')
def favorites():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    favs = Favorite.query.filter_by(user_id=user.id).all()
    products = [fav.product for fav in favs]

    return render_template('favorites.html', favorites=products)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        if not name or not message:
            flash('Заполните обязательные поля!')
            return redirect(url_for('contact'))

        new_msg = ContactMessage(
            name=name,
            email=email,
            message=message
        )
        db.session.add(new_msg)
        db.session.commit()

        flash('Ваше сообщение было успешно отправлено!')
        return redirect(url_for('contact'))

    return render_template('contact.html')


@app.route('/order', methods=['GET', 'POST'])
def order():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')

        if not all([full_name, email, phone, message]):
            flash('Пожалуйста, заполните все обязательные поля', 'error')
            return redirect(url_for('order'))

        new_order = Order(
            full_name=full_name,
            email=email,
            phone=phone,
            message=message,
            user_id=session.get('user_id')
        )

        try:
            db.session.add(new_order)
            db.session.commit()
            return redirect(url_for('order', success=True))
        except Exception as e:
            db.session.rollback()
            flash('Произошла ошибка при сохранении заказа', 'error')
            return redirect(url_for('order'))

    success = request.args.get('success')
    if success:
        flash('Ваш заказ успешно отправлен!', 'success')
    return render_template('order.html')


if __name__ == '__main__':
    app.run(debug=True)