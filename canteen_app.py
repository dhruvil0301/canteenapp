from flask import Flask, render_template, request, redirect, url_for, flash, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import pytz
# from weasyprint import HTML  # No longer needed
import io
from xhtml2pdf import pisa
from collections import defaultdict
from functools import wraps
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string

INDIA_TZ = pytz.timezone('Asia/Kolkata')


def localize_datetime(dt):
    if dt is None:
        return ''
    # If dt is naive (no timezone), treat as UTC
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    return dt.astimezone(INDIA_TZ)


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///canteen.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email configuration for password reset
try:
    from email_config import EMAIL_CONFIG
    app.config.update(EMAIL_CONFIG)
except ImportError:
    # Default fallback configuration
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'your-email@gmail.com'  # Change this to your email
    app.config['MAIL_PASSWORD'] = 'your-app-password'     # Change this to your app password

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'


# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'admin' or 'user'
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    customer = db.relationship('Customer', backref='user', uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class PasswordReset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    otp = db.Column(db.String(6), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='password_resets')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if current_user.role != 'admin':
            flash('Admin access required!', 'error')
            return redirect(url_for('user_dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))


def send_email(to_email, subject, body):
    """Send email using SMTP"""
    try:
        msg = MIMEMultipart()
        msg['From'] = app.config['MAIL_USERNAME']
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT'])
        server.starttls()
        server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        text = msg.as_string()
        server.sendmail(app.config['MAIL_USERNAME'], to_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False


def send_password_reset_email(user, otp):
    """Send password reset email with OTP"""
    subject = "Password Reset - Canteen Billing System"
    body = f"""
    <html>
    <body>
        <h2>Password Reset Request</h2>
        <p>Hello {user.username},</p>
        <p>You have requested to reset your password for the Canteen Billing System.</p>
        <p>Your OTP (One-Time Password) is: <strong style="font-size: 24px; color: #007bff;">{otp}</strong></p>
        <p>This OTP will expire in 10 minutes.</p>
        <p>If you didn't request this password reset, please ignore this email.</p>
        <br>
        <p>Best regards,<br>Canteen Billing System Team</p>
    </body>
    </html>
    """
    return send_email(user.email, subject, body)


class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    orders = db.relationship('Order', backref='customer', lazy=True)


class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    category = db.Column(db.String(50))
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Numeric(10, 2), default=0)
    status = db.Column(db.String(20), default='pending')  # pending, completed, cancelled
    payment_method = db.Column(db.String(20), default='cash')
    order_items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    menu_item = db.relationship('MenuItem')


# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # Redirect based on user role
        if current_user.role == 'admin':
            return redirect(url_for('index'))
        else:
            return redirect(url_for('user_dashboard'))

    if request.method == 'POST':
        login_field = request.form['login_field']
        password = request.form['password']

        # Check if login_field is email or username
        if '@' in login_field:
            user = User.query.filter_by(email=login_field).first()
        else:
            user = User.query.filter_by(username=login_field).first()

        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                # Redirect based on user role
                if user.role == 'admin':
                    next_page = url_for('index')
                else:
                    next_page = url_for('user_dashboard')
            return redirect(next_page)
        else:
            flash('Invalid username/email or password', 'error')

    return render_template('login_animated.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Validation
        if not username or not email or not password:
            flash('All fields are required!', 'error')
            return render_template('register_animated.html')

        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('register_animated.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long!', 'error')
            return render_template('register_animated.html')

        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
            return render_template('register_animated.html')

        if User.query.filter_by(email=email).first():
            flash('Email already exists!', 'error')
            return render_template('register_animated.html')

        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register_animated.html')


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()

        if user:
            # Generate OTP
            otp = generate_otp()
            expires_at = datetime.utcnow() + timedelta(minutes=10)

            # Save OTP to database
            password_reset = PasswordReset(
                user_id=user.id,
                otp=otp,
                expires_at=expires_at
            )
            db.session.add(password_reset)
            db.session.commit()

            # Send email
            if send_password_reset_email(user, otp):
                flash('Password reset OTP has been sent to your email!', 'success')
            else:
                flash('Failed to send email. Please try again.', 'error')
        else:
            flash('Email not found!', 'error')

    return render_template('forgot_password.html')


@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form['email']
        otp = request.form['otp']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        # Validation
        if new_password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('reset_password.html')

        if len(new_password) < 6:
            flash('Password must be at least 6 characters long!', 'error')
            return render_template('reset_password.html')

        # Verify OTP
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('Email not found!', 'error')
            return render_template('reset_password.html')

        password_reset = PasswordReset.query.filter_by(
            user_id=user.id,
            otp=otp,
            used=False
        ).filter(PasswordReset.expires_at > datetime.utcnow()).first()

        if not password_reset:
            flash('Invalid or expired OTP!', 'error')
            return render_template('reset_password.html')

        # Update password
        user.set_password(new_password)
        password_reset.used = True
        db.session.commit()

        flash('Password has been reset successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html')


@app.route('/')
@login_required
@admin_required
def index():
    # Get summary statistics
    total_customers = Customer.query.count()
    total_orders = Order.query.count()
    total_revenue = db.session.query(db.func.sum(Order.total_amount)).scalar() or 0
    recent_orders = Order.query.order_by(Order.order_date.desc()).limit(5).all()

    return render_template('index.html',
                         total_customers=total_customers,
                         total_orders=total_orders,
                         total_revenue=total_revenue,
                         recent_orders=recent_orders)


@app.route('/customers')
@login_required
@admin_required
def customers():
    customers_list = Customer.query.all()
    return render_template('customers.html', customers=customers_list)


@app.route('/customers/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_customer():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        address = request.form['address']

        # Check if phone already exists
        if Customer.query.filter_by(phone=phone).first():
            flash('Phone number already exists!', 'error')
            return render_template('add_customer.html')

        customer = Customer(name=name, phone=phone, email=email, address=address)
        db.session.add(customer)
        db.session.commit()

        flash('Customer added successfully!', 'success')
        return redirect(url_for('customers'))

    return render_template('add_customer.html')


@app.route('/customers/<int:customer_id>')
@login_required
def customer_detail(customer_id):
    # Regular users can only see their own customer details
    if current_user.role != 'admin' and current_user.customer_id != customer_id:
        flash('Access denied!', 'error')
        return redirect(url_for('user_dashboard'))

    customer = Customer.query.get_or_404(customer_id)
    orders = Order.query.filter_by(customer_id=customer_id).order_by(Order.order_date.desc()).all()
    return render_template('customer_detail.html', customer=customer, orders=orders)


@app.route('/faculty/<int:faculty_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_faculty(faculty_id):
    # Regular users can only edit their own details
    if current_user.role != 'admin' and current_user.customer_id != faculty_id:
        flash('Access denied!', 'error')
        return redirect(url_for('user_dashboard'))

    customer = Customer.query.get_or_404(faculty_id)
    if request.method == 'POST':
        customer.name = request.form['name']
        customer.phone = request.form['phone']
        customer.email = request.form['email']
        customer.address = request.form['address']
        db.session.commit()
        flash('Faculty details updated successfully!', 'success')
        return redirect(url_for('customer_detail', customer_id=customer.id))

    return render_template('edit_faculty.html', customer=customer)


@app.route('/faculty/<int:faculty_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_faculty(faculty_id):
    customer = Customer.query.get_or_404(faculty_id)
    db.session.delete(customer)
    db.session.commit()
    flash('Faculty deleted successfully!', 'success')
    return redirect(url_for('customers'))


@app.route('/menu')
@login_required
def menu():
    menu_items = MenuItem.query.filter_by(is_available=True).all()
    return render_template('menu.html', menu_items=menu_items)


@app.route('/menu/add', methods=['GET', 'POST'])
def add_menu_item():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        category = request.form['category']

        menu_item = MenuItem(name=name, description=description, price=price, category=category)
        db.session.add(menu_item)
        db.session.commit()

        flash('Menu item added successfully!', 'success')
        return redirect(url_for('menu'))

    return render_template('add_menu_item.html')


@app.route('/menu/<int:item_id>/edit', methods=['GET', 'POST'])
def edit_menu_item(item_id):
    menu_item = MenuItem.query.get_or_404(item_id)
    if request.method == 'POST':
        menu_item.name = request.form['name']
        menu_item.description = request.form['description']
        menu_item.price = request.form['price']
        menu_item.category = request.form['category']
        db.session.commit()
        flash('Menu item updated successfully!', 'success')
        return redirect(url_for('menu'))

    return render_template('edit_menu_item.html', menu_item=menu_item)


@app.route('/orders')
@login_required
def orders():
    # Regular users can only see their own orders
    if current_user.role == 'admin':
        orders_list = Order.query.order_by(Order.order_date.desc()).all()
    else:
        if not current_user.customer_id:
            orders_list = []
        else:
            orders_list = Order.query.filter_by(
                customer_id=current_user.customer_id
            ).order_by(Order.order_date.desc()).all()

    return render_template('orders.html', orders=orders_list)


@app.route('/orders/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_order():
    if request.method == 'POST':
        customer_id = request.form['customer_id']
        menu_items = request.form.getlist('menu_item_id')
        quantities = request.form.getlist('quantity')

        if not customer_id or not menu_items:
            flash('Please select customer and menu items!', 'error')
            return redirect(url_for('new_order'))

        # Create order
        order = Order(customer_id=customer_id)
        db.session.add(order)
        db.session.flush()  # Get the order ID

        total_amount = 0
        for menu_item_id, quantity in zip(menu_items, quantities):
            if quantity and int(quantity) > 0:
                menu_item = MenuItem.query.get(menu_item_id)
                if menu_item:
                    unit_price = float(menu_item.price)
                    total_price = unit_price * int(quantity)
                    total_amount += total_price

                    order_item = OrderItem(
                        order_id=order.id,
                        menu_item_id=menu_item_id,
                        quantity=int(quantity),
                        unit_price=unit_price,
                        total_price=total_price
                    )
                    db.session.add(order_item)

        order.total_amount = total_amount
        db.session.commit()

        flash('Order created successfully!', 'success')
        return redirect(url_for('orders'))

    customers_list = Customer.query.all()
    menu_items = MenuItem.query.filter_by(is_available=True).all()
    return render_template('new_order.html', customers=customers_list, menu_items=menu_items)


@app.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    # Regular users can only see their own orders
    if current_user.role != 'admin' and current_user.customer_id != order.customer_id:
        flash('Access denied!', 'error')
        return redirect(url_for('user_dashboard'))

    return render_template('order_detail.html', order=order)


@app.route('/orders/<int:order_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_order(order_id):
    order = Order.query.get_or_404(order_id)
    if request.method == 'POST':
        # Update order status
        order.status = request.form['status']
        order.payment_method = request.form['payment_method']

        # Update order items
        menu_items = request.form.getlist('menu_item_id')
        quantities = request.form.getlist('quantity')

        # Remove existing order items
        OrderItem.query.filter_by(order_id=order.id).delete()

        total_amount = 0
        for menu_item_id, quantity in zip(menu_items, quantities):
            if quantity and int(quantity) > 0:
                menu_item = MenuItem.query.get(menu_item_id)
                if menu_item:
                    unit_price = float(menu_item.price)
                    total_price = unit_price * int(quantity)
                    total_amount += total_price

                    order_item = OrderItem(
                        order_id=order.id,
                        menu_item_id=menu_item_id,
                        quantity=int(quantity),
                        unit_price=unit_price,
                        total_price=total_price
                    )
                    db.session.add(order_item)

        order.total_amount = total_amount
        db.session.commit()

        flash('Order updated successfully!', 'success')
        return redirect(url_for('orders'))

    customers_list = Customer.query.all()
    menu_items = MenuItem.query.filter_by(is_available=True).all()
    return render_template('edit_order.html', order=order, customers=customers_list, menu_items=menu_items)


@app.route('/orders/<int:order_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    flash('Order deleted successfully!', 'success')
    return redirect(url_for('orders'))


@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    users = User.query.all()
    customers = Customer.query.all()
    return render_template('admin_panel.html', users=users, customers=customers)


@app.route('/admin/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        customer_id = request.form.get('customer_id') or None

        # Validation
        if not username or not email or not password:
            flash('All fields are required!', 'error')
            return render_template('add_user.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long!', 'error')
            return render_template('add_user.html')

        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
            return render_template('add_user.html')

        if User.query.filter_by(email=email).first():
            flash('Email already exists!', 'error')
            return render_template('add_user.html')

        # Create new user
        user = User(username=username, email=email, role=role, customer_id=customer_id)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('User added successfully!', 'success')
        return redirect(url_for('admin_panel'))

    customers_list = Customer.query.all()
    return render_template('add_user.html', customers=customers_list)


@app.route('/admin/users/<int:user_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    username = request.form['username']
    email = request.form['email']
    role = request.form['role']
    customer_id = request.form.get('customer_id') or None

    # Check if username or email already exists (excluding current user)
    existing_user = User.query.filter_by(username=username).first()
    if existing_user and existing_user.id != user.id:
        flash('Username already exists!', 'error')
        return redirect(url_for('admin_panel'))

    existing_user = User.query.filter_by(email=email).first()
    if existing_user and existing_user.id != user.id:
        flash('Email already exists!', 'error')
        return redirect(url_for('admin_panel'))

    user.username = username
    user.email = email
    user.role = role
    user.customer_id = customer_id
    db.session.commit()

    flash('User updated successfully!', 'success')
    return redirect(url_for('admin_panel'))


@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete your own account!', 'error')
        return redirect(url_for('admin_panel'))

    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin_panel'))


@app.route('/admin/customers/<int:customer_id>/link', methods=['POST'])
@login_required
@admin_required
def link_customer_to_user(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    user_id = request.form.get('user_id')

    if user_id:
        user = User.query.get(user_id)
        if user:
            user.customer_id = customer_id
            db.session.commit()
            flash(f'Customer {customer.name} linked to user {user.username}!', 'success')
        else:
            flash('User not found!', 'error')
    else:
        flash('Please select a user!', 'error')

    return redirect(url_for('admin_panel'))


@app.route('/admin/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def admin_reset_password(user_id):
    user = User.query.get_or_404(user_id)
    new_password = request.form.get('new_password')

    if not new_password:
        flash('New password is required!', 'error')
        return redirect(url_for('admin_panel'))

    if len(new_password) < 6:
        flash('Password must be at least 6 characters long!', 'error')
        return redirect(url_for('admin_panel'))

    user.set_password(new_password)
    db.session.commit()

    flash(f'Password for {user.username} has been reset successfully!', 'success')
    return redirect(url_for('admin_panel'))


@app.route('/reports')
@login_required
@admin_required
def reports():
    return render_template('reports.html')


@app.route('/user-dashboard')
@login_required
def user_dashboard():
    # Regular users see their own data only
    if not current_user.customer_id:
        flash('No customer account linked to your user account!', 'error')
        return redirect(url_for('logout'))

    customer = Customer.query.get(current_user.customer_id)
    if not customer:
        flash('Customer account not found!', 'error')
        return redirect(url_for('logout'))

    # Get user's orders
    orders = Order.query.filter_by(
        customer_id=current_user.customer_id
    ).order_by(Order.order_date.desc()).all()

    # Calculate total spent
    total_spent = sum(float(order.total_amount) for order in orders)

    return render_template('user_dashboard.html',
                         customer=customer,
                         orders=orders,
                         total_spent=total_spent)


@app.route('/reports/weekly')
@login_required
def weekly_report():
    # Get date range for current week
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    # Get orders for the week
    orders = Order.query.filter(
        Order.order_date >= start_of_week,
        Order.order_date <= end_of_week
    ).all()

    # Calculate statistics
    total_orders = len(orders)
    total_revenue = sum(float(order.total_amount) for order in orders)
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

    # Group by day
    daily_stats = defaultdict(lambda: {'orders': 0, 'revenue': 0})
    for order in orders:
        day = order.order_date.strftime('%A')
        daily_stats[day]['orders'] += 1
        daily_stats[day]['revenue'] += float(order.total_amount)

    return render_template('weekly_report.html',
                         orders=orders,
                         total_orders=total_orders,
                         total_revenue=total_revenue,
                         avg_order_value=avg_order_value,
                         daily_stats=daily_stats,
                         start_date=start_of_week,
                         end_date=end_of_week)


@app.route('/reports/monthly')
@login_required
@admin_required
def monthly_report():
    # Get current month
    today = datetime.now()
    start_of_month = today.replace(day=1)
    if today.month == 12:
        end_of_month = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        end_of_month = today.replace(month=today.month + 1, day=1) - timedelta(days=1)

    # Get orders for the month
    orders = Order.query.filter(
        Order.order_date >= start_of_month,
        Order.order_date <= end_of_month
    ).all()

    # Calculate statistics
    total_orders = len(orders)
    total_revenue = sum(float(order.total_amount) for order in orders)
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

    # Group by day
    daily_stats = defaultdict(lambda: {'orders': 0, 'revenue': 0})
    for order in orders:
        day = order.order_date.day
        daily_stats[day]['orders'] += 1
        daily_stats[day]['revenue'] += float(order.total_amount)

    return render_template('monthly_report.html',
                         orders=orders,
                         total_orders=total_orders,
                         total_revenue=total_revenue,
                         avg_order_value=avg_order_value,
                         daily_stats=daily_stats,
                         start_date=start_of_month,
                         end_date=end_of_month)


@app.route('/reports/yearly')
@login_required
@admin_required
def yearly_report():
    # Get current year
    today = datetime.now()
    start_of_year = today.replace(month=1, day=1)
    end_of_year = today.replace(month=12, day=31)

    # Get orders for the year
    orders = Order.query.filter(
        Order.order_date >= start_of_year,
        Order.order_date <= end_of_year
    ).all()

    # Calculate statistics
    total_orders = len(orders)
    total_revenue = sum(float(order.total_amount) for order in orders)
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

    # Group by month
    monthly_stats = defaultdict(lambda: {'orders': 0, 'revenue': 0})
    for order in orders:
        month = order.order_date.month
        monthly_stats[month]['orders'] += 1
        monthly_stats[month]['revenue'] += float(order.total_amount)

    return render_template('yearly_report.html',
                         orders=orders,
                         total_orders=total_orders,
                         total_revenue=total_revenue,
                         avg_order_value=avg_order_value,
                         monthly_stats=monthly_stats,
                         start_date=start_of_year,
                         end_date=end_of_year)


@app.route('/reports/custom', methods=['GET'])
@login_required
@admin_required
def custom_report():
    # Get date range from query parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
        except ValueError:
            flash('Invalid date format!', 'error')
            return render_template('custom_report.html')

        # Get orders for the date range
        orders = Order.query.filter(
            Order.order_date >= start_date,
            Order.order_date <= end_date
        ).all()

        # Calculate statistics
        total_orders = len(orders)
        total_revenue = sum(float(order.total_amount) for order in orders)
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

        # Group by customer
        customer_stats = defaultdict(lambda: {'orders': 0, 'revenue': 0})
        for order in orders:
            customer_name = order.customer.name
            customer_stats[customer_name]['orders'] += 1
            customer_stats[customer_name]['revenue'] += float(order.total_amount)

        return render_template('custom_report.html',
                             orders=orders,
                             total_orders=total_orders,
                             total_revenue=total_revenue,
                             avg_order_value=avg_order_value,
                             customer_stats=customer_stats,
                             start_date=start_date,
                             end_date=end_date)

    return render_template('custom_report.html')


@app.route('/reports/daily', methods=['GET'])
def daily_report():
    # Get today's date
    today = datetime.now().date()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = datetime.combine(today, datetime.max.time())

    # Get orders for today
    orders = Order.query.filter(
        Order.order_date >= start_of_day,
        Order.order_date <= end_of_day
    ).all()

    # Calculate statistics
    total_orders = len(orders)
    total_revenue = sum(float(order.total_amount) for order in orders)
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

    # Group by hour
    hourly_stats = defaultdict(lambda: {'orders': 0, 'revenue': 0})
    for order in orders:
        hour = order.order_date.hour
        hourly_stats[hour]['orders'] += 1
        hourly_stats[hour]['revenue'] += float(order.total_amount)

    return render_template('daily_report.html',
                         orders=orders,
                         total_orders=total_orders,
                         total_revenue=total_revenue,
                         avg_order_value=avg_order_value,
                         hourly_stats=hourly_stats,
                         date=today)


@app.route('/reports/customer/<int:customer_id>')
def customer_bill(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    orders = Order.query.filter_by(customer_id=customer_id).order_by(Order.order_date.desc()).all()

    # Calculate total amount
    total_amount = sum(float(order.total_amount) for order in orders)

    # Group orders by date
    orders_by_date = defaultdict(list)
    for order in orders:
        date_key = order.order_date.strftime('%Y-%m-%d')
        orders_by_date[date_key].append(order)

    return render_template('customer_bill.html',
                         customer=customer,
                         orders=orders,
                         orders_by_date=orders_by_date,
                         total_amount=total_amount)


@app.route('/download_bill_pdf/<int:customer_id>')
def download_bill_pdf(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    orders = Order.query.filter_by(customer_id=customer_id).order_by(Order.order_date.desc()).all()

    # Calculate total amount
    total_amount = sum(float(order.total_amount) for order in orders)

    # Group orders by date
    orders_by_date = defaultdict(list)
    for order in orders:
        date_key = order.order_date.strftime('%Y-%m-%d')
        orders_by_date[date_key].append(order)

    # Generate HTML content
    html_content = render_template('customer_bill_pdf.html',
                                 customer=customer,
                                 orders=orders,
                                 orders_by_date=orders_by_date,
                                 total_amount=total_amount)

    # Create PDF
    result = io.BytesIO()
    pdf = pisa.CreatePDF(io.StringIO(html_content), result)

    if not pdf.err:
        response = make_response(result.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=bill_{customer.name}.pdf'
        return response

    return "Error generating PDF", 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
