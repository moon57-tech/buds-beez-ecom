from server import app, db
from models import User, Category, Product
from werkzeug.security import generate_password_hash


def init_db():
    with app.app_context():
        db.create_all()

        # Create admin user
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@budsbeez.co.za',
                full_name='Admin User',
                phone='0000000000',
                password_hash=generate_password_hash('admin123'),
                is_admin=True,
                is_active=True
            )
            db.session.add(admin)

        # Create categories
        if not Category.query.first():
            flowers = Category(name='Flowers', description='Fresh cut flowers for all occasions')
            honey = Category(name='Honey', description='Pure, natural honey')
            produce = Category(name='Fresh Produce', description='Fresh fruits and vegetables')
            db.session.add_all([flowers, honey, produce])
            db.session.commit()

            # Create sample products
            products = [
                Product(name='Rose Bouquet', description='Beautiful mixed rose bouquet', price=250.00,
                        stock_quantity=50, category_id=flowers.id, is_active=True,
                        image_url='/static/img/rose-bouquet.jpg'),
                Product(name='Wildflower Arrangement', description='Fresh seasonal wildflowers', price=180.00,
                        stock_quantity=40, category_id=flowers.id, is_active=True),
                Product(name='Pure Raw Honey (500g)', description='Unfiltered, pure raw honey', price=120.00,
                        stock_quantity=100, category_id=honey.id, is_active=True),
                Product(name='Pure Raw Honey (1kg)', description='Unfiltered, pure raw honey', price=200.00,
                        stock_quantity=80, category_id=honey.id, is_active=True),
                Product(name='Fresh Strawberries (500g)', description='Sweet, ripe strawberries', price=65.00,
                        stock_quantity=150, category_id=produce.id, is_active=True),
                Product(name='Mixed Greens', description='Fresh organic mixed greens', price=45.00,
                        stock_quantity=200, category_id=produce.id, is_active=True),
            ]
            db.session.add_all(products)

        db.session.commit()
        print('Database initialized successfully!')


if __name__ == '__main__':
    init_db()
