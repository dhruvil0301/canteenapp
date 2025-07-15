# Canteen Billing System

A comprehensive Flask-based canteen billing and management system with role-based access control, animated UI, and advanced reporting features.

## Features

### 🔐 Authentication & Security
- **Role-based Access Control**: Admin and User roles with different permissions
- **Secure Login**: Email/username login with password hashing
- **Password Reset**: Email-based OTP system for forgotten passwords
- **Admin Password Reset**: Direct password reset functionality for administrators

### 🎨 User Interface
- **Animated Login/Registration**: Beautiful gradient animations and interactive elements
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Modern UI**: Bootstrap 5 with custom CSS animations
- **Password Strength Meter**: Real-time password validation and strength indicators

### 📊 Billing & Management
- **Customer Management**: Add, edit, and manage customer information
- **Menu Management**: Create and manage menu items with categories
- **Order Processing**: Create, edit, and track orders
- **Payment Tracking**: Multiple payment methods and status tracking

### 📈 Reporting & Analytics
- **Customizable Reports**: Daily, weekly, monthly, and yearly reports
- **Dynamic Charts**: Interactive charts with configurable colors and types
- **Customer Bills**: Generate and download PDF bills
- **Sales Analytics**: Revenue tracking and order statistics

### 📧 Communication
- **Email Integration**: Send bills and notifications via email
- **WhatsApp Integration**: Send bills via WhatsApp (if configured)
- **PDF Generation**: Automatic bill generation in PDF format

## Installation

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd flask_project
   ```

2. **Create virtual environment**
   ```bash
   python -m venv env
   ```

3. **Activate virtual environment**
   - Windows:
     ```bash
     env\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source env/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure email settings** (optional)
   Create `email_config.py` file:
   ```python
   EMAIL_CONFIG = {
       'MAIL_SERVER': 'smtp.gmail.com',
       'MAIL_PORT': 587,
       'MAIL_USE_TLS': True,
       'MAIL_USERNAME': 'your-email@gmail.com',
       'MAIL_PASSWORD': 'your-app-password'
   }
   ```

6. **Run the application**
   ```bash
   python canteen_app.py
   ```

7. **Access the application**
   Open your browser and go to `http://localhost:5000`

## Default Users

The system comes with default admin credentials:
- **Username**: admin
- **Password**: admin123

**⚠️ Important**: Change these credentials after first login for security.

## Usage

### Admin Features
- **Dashboard**: Overview of total customers, orders, and revenue
- **Customer Management**: Add, edit, and manage customer profiles
- **Menu Management**: Create and manage menu items
- **Order Management**: Process and track all orders
- **User Management**: Create and manage user accounts
- **Reports**: Generate detailed sales and analytics reports
- **Admin Panel**: Manage users and customer-user linkages

### User Features
- **Personal Dashboard**: View own orders and spending
- **Order History**: Track personal order history
- **Profile Management**: Update personal information

## File Structure

```
flask_project/
├── canteen_app.py          # Main Flask application
├── requirements.txt        # Python dependencies
├── .gitignore             # Git ignore rules
├── README.md              # Project documentation
├── templates/             # HTML templates
│   ├── login_animated.html
│   ├── register_animated.html
│   ├── index.html
│   └── ... (other templates)
├── static/                # Static files (CSS, JS, images)
└── env/                   # Virtual environment (not in repo)
```

## Configuration

### Database
- Uses SQLite by default
- Database file: `canteen.db` (created automatically)

### Email Configuration
- Supports Gmail SMTP
- Requires app password for Gmail
- Configure in `email_config.py`

### Security
- Flask-Login for session management
- Werkzeug password hashing
- Role-based access control

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions:
- Create an issue in the repository
- Contact the development team

## Changelog

### Version 1.0.0
- Initial release
- Basic billing functionality
- User authentication
- Role-based access control
- Animated UI
- Reporting system
- Email integration 