# 🔐 Password Reset Functionality

This document explains how to set up and use the password reset functionality in your Canteen Billing System.

## ✨ Features

- **Email-based OTP**: Users receive a 6-digit OTP via email
- **Secure Reset**: OTP expires after 10 minutes
- **User-friendly Interface**: Clean, modern UI for password reset
- **Multiple Email Providers**: Support for Gmail, Outlook, Yahoo, etc.

## 🚀 How It Works

1. **User clicks "Forgot Password"** on the login page
2. **User enters their email address**
3. **System generates a 6-digit OTP** and sends it via email
4. **User enters the OTP** and sets a new password
5. **Password is updated** and user can log in

## 📧 Email Setup Instructions

### For Gmail (Recommended)

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate an App Password**:
   - Go to [Google Account Settings](https://myaccount.google.com/)
   - Security → 2-Step Verification → App passwords
   - Select "Mail" and generate a new password
   - Copy the 16-character password

3. **Update Email Configuration**:
   - Open `email_config.py`
   - Replace `your-email@gmail.com` with your Gmail address
   - Replace `your-app-password` with the 16-character app password

### For Outlook/Hotmail

1. **Enable 2-Factor Authentication** on your Microsoft account
2. **Generate an App Password**:
   - Go to [Microsoft Account Security](https://account.microsoft.com/security)
   - Advanced security options → App passwords
   - Generate a new app password

3. **Update Email Configuration**:
   - Open `email_config.py`
   - Uncomment the Outlook section
   - Update with your email and app password

### For Yahoo

1. **Enable 2-Factor Authentication** on your Yahoo account
2. **Generate an App Password**:
   - Go to Yahoo Account Security
   - Generate app-specific password

3. **Update Email Configuration**:
   - Open `email_config.py`
   - Uncomment the Yahoo section
   - Update with your email and app password

## 🔧 Configuration Files

### `email_config.py`
```python
EMAIL_CONFIG = {
    'MAIL_SERVER': 'smtp.gmail.com',
    'MAIL_PORT': 587,
    'MAIL_USE_TLS': True,
    'MAIL_USERNAME': 'your-email@gmail.com',
    'MAIL_PASSWORD': 'your-app-password'
}
```

### Environment Variables (Production)
For production, use environment variables:
```python
import os
EMAIL_CONFIG = {
    'MAIL_SERVER': 'smtp.gmail.com',
    'MAIL_PORT': 587,
    'MAIL_USE_TLS': True,
    'MAIL_USERNAME': os.environ.get('EMAIL_USERNAME'),
    'MAIL_PASSWORD': os.environ.get('EMAIL_PASSWORD')
}
```

## 🧪 Testing the Functionality

1. **Start the application**:
   ```bash
   python canteen_app.py
   ```

2. **Go to login page** and click "Forgot Password"

3. **Enter a registered email** (e.g., `user1@example.com`)

4. **Check your email** for the OTP

5. **Enter the OTP** and set a new password

## 📱 User Interface

### Forgot Password Page
- Clean, modern design
- Email input field
- Instructions for users
- Link back to login

### Reset Password Page
- OTP input with validation
- New password fields
- Password confirmation
- Show/hide password toggles
- Auto-focus on OTP field

## 🔒 Security Features

- **OTP Expiration**: 10-minute timeout
- **One-time Use**: OTP can only be used once
- **Email Verification**: Only registered emails can request reset
- **Password Validation**: Minimum 6 characters required
- **Secure Storage**: Passwords are hashed using Werkzeug

## 🛠️ Troubleshooting

### Email Not Sending
1. **Check email configuration** in `email_config.py`
2. **Verify app password** is correct
3. **Check firewall/antivirus** settings
4. **Test with different email provider**

### OTP Not Working
1. **Check email spam folder**
2. **Verify OTP hasn't expired** (10 minutes)
3. **Ensure OTP is entered correctly**
4. **Check database connection**

### Common Error Messages
- `"No user found with this email address"` → Email not registered
- `"Invalid or expired OTP"` → OTP expired or incorrect
- `"Failed to send email"` → Email configuration issue

## 📋 Database Schema

### PasswordReset Table
```sql
CREATE TABLE password_reset (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    otp VARCHAR(6) NOT NULL,
    expires_at DATETIME NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user (id)
);
```

## 🔄 Maintenance

### Cleanup Expired OTPs
You can add a scheduled task to clean up expired OTPs:
```python
# Clean up expired OTPs older than 1 hour
expired_otps = PasswordReset.query.filter(
    PasswordReset.expires_at < datetime.utcnow() - timedelta(hours=1)
).all()
for otp in expired_otps:
    db.session.delete(otp)
db.session.commit()
```

## 📞 Support

If you encounter issues:
1. Check the email configuration
2. Verify your email provider settings
3. Test with a different email address
4. Check the application logs for errors

---

**Note**: Always use app passwords instead of your main email password for security! 