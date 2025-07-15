#!/usr/bin/env python3
"""
Test script to debug email sending functionality
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email_config import EMAIL_CONFIG



test_email_connection():
    """Test the email connection and sending"""
    print("🔍 Testing Email Configuration...")
    print(f"Server: {EMAIL_CONFIG['MAIL_SERVER']}")
    print(f"Port: {EMAIL_CONFIG['MAIL_PORT']}")
    print(f"Username: {EMAIL_CONFIG['MAIL_USERNAME']}")
    print(f"Password: {'*' * len(EMAIL_CONFIG['MAIL_PASSWORD'])} (hidden)")
    print("-" * 50)

    try:
        # Test 1: Create SMTP connection
        print("📡 Testing SMTP connection...")
        server = smtplib.SMTP(EMAIL_CONFIG['MAIL_SERVER'], EMAIL_CONFIG['MAIL_PORT'])
        print("✅ SMTP connection created successfully")

        # Test 2: Start TLS
        print("🔒 Starting TLS...")
        server.starttls()
        print("✅ TLS started successfully")

        # Test 3: Login
        print("🔑 Attempting login...")
        server.login(EMAIL_CONFIG['MAIL_USERNAME'], EMAIL_CONFIG['MAIL_PASSWORD'])
        print("✅ Login successful!")

        # Test 4: Send test email
        print("📧 Sending test email...")
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['MAIL_USERNAME']
        msg['To'] = EMAIL_CONFIG['MAIL_USERNAME']  # Send to yourself
        msg['Subject'] = "Test Email - Canteen Billing System"

        body = """
        <html>
        <body>
            <h2>Test Email</h2>
            <p>This is a test email from your Canteen Billing System.</p>
            <p>If you receive this, your email configuration is working correctly!</p>
            <br>
            <p>Test OTP: <strong>123456</strong></p>
        </body>
        </html>
        """

        msg.attach(MIMEText(body, 'html'))
        text = msg.as_string()

        server.sendmail(EMAIL_CONFIG['MAIL_USERNAME'], EMAIL_CONFIG['MAIL_USERNAME'], text)
        print("✅ Test email sent successfully!")
        print("📬 Check your email inbox for the test message")

        # Close connection
        server.quit()
        print("✅ SMTP connection closed")

        return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("💡 Check your app password - it should be 16 characters without spaces")
        return False

    except smtplib.SMTPConnectError as e:
        print(f"❌ Connection failed: {e}")
        print("💡 Check your internet connection and firewall settings")
        return False

    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Check your email configuration")
        return False



test_app_password_format():
    """Test if app password format is correct"""
    password = EMAIL_CONFIG['MAIL_PASSWORD']
    print(f"🔍 Checking app password format...")
    print(f"Password length: {len(password)} characters")
    print(f"Password contains spaces: {'Yes' if ' ' in password else 'No'}")

    # Remove spaces for checking
    clean_password = password.replace(' ', '')
    print(f"Password without spaces: {len(clean_password)} characters")

    if len(clean_password) == 16:
        print("✅ App password format looks correct")
        return True
    else:
        print("❌ App password should be exactly 16 characters (excluding spaces)")
        return False

if __name__ == '__main__':
    print("🚀 Email Configuration Test")
    print("=" * 50)

    # Test app password format
    if test_app_password_format():
        # Test email connection
        if test_email_connection():
            print("\n🎉 All tests passed! Your email configuration is working.")
            print("You can now use the password reset functionality.")
        else:
            print("\n❌ Email test failed. Please check the error messages above.")
    else:
        print("\n❌ App password format is incorrect. Please fix it first.")

    print("\n" + "=" * 50)
