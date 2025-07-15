#!/usr/bin/env python3
"""
Setup script for Canteen Billing System with Authentication
This script initializes the database and creates an admin user.
"""

from canteen_app import app, db, User, Customer, PasswordReset
from werkzeug.security import generate_password_hash



setup_database():
    """Initialize the database and create tables"""
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database tables created successfully!")



create_admin_user():
    """Create an admin user if it doesn't exist"""
    with app.app_context():
        # Check if admin user already exists
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            print("✅ Admin user already exists!")
            return

        # Create admin user
        admin_user = User(
            username='admin',
            email='admin@canteen.com',
            role='admin'
        )
        admin_user.set_password('admin123')

        db.session.add(admin_user)
        db.session.commit()
        print("✅ Admin user created successfully!")
        print("   Username: admin")
        print("   Password: admin123")
        print("   Please change the password after first login!")



create_sample_customer():
    """Create a sample customer for testing"""
    with app.app_context():
        # Check if sample customer already exists
        sample_customer = Customer.query.filter_by(phone='9876543210').first()
        if sample_customer:
            print("✅ Sample customer already exists!")
            return

        # Create sample customer
        sample_customer = Customer(
            name='John Doe',
            phone='9876543210',
            email='john.doe@example.com',
            address='Sample Address'
        )

        db.session.add(sample_customer)
        db.session.commit()
        print("✅ Sample customer created successfully!")



create_sample_user():
    """Create a sample regular user"""
    with app.app_context():
        # Check if sample user already exists
        sample_user = User.query.filter_by(username='user1').first()
        if sample_user:
            print("✅ Sample user already exists!")
            return

        # Get the sample customer
        sample_customer = Customer.query.filter_by(phone='9876543210').first()
        if not sample_customer:
            print("❌ Sample customer not found. Please run create_sample_customer() first.")
            return

        # Create sample user
        sample_user = User(
            username='user1',
            email='user1@example.com',
            role='user',
            customer_id=sample_customer.id
        )
        sample_user.set_password('user123')

        db.session.add(sample_user)
        db.session.commit()
        print("✅ Sample user created successfully!")
        print("   Username: user1")
        print("   Password: user123")
        print("   This user is linked to the sample customer.")

if __name__ == '__main__':
    print("🚀 Setting up Canteen Billing System with Authentication...")
    print("=" * 60)

    try:
        setup_database()
        create_admin_user()
        create_sample_customer()
        create_sample_user()

        print("=" * 60)
        print("🎉 Setup completed successfully!")
        print("\n📋 Login Credentials:")
        print("   Admin User:")
        print("     Username: admin")
        print("     Password: admin123")
        print("     Role: Admin (can access everything)")
        print("\n   Regular User:")
        print("     Username: user1")
        print("     Password: user123")
        print("     Role: User (can only see own data)")
        print("\n⚠️  IMPORTANT: Change these passwords after first login!")
        print("\n🚀 You can now run the application with: python canteen_app.py")

    except Exception as e:
        print(f"❌ Error during setup: {e}")
        print("Please make sure all dependencies are installed.")
