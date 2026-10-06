import os
from server import app, db


def _ensure_db():
    with app.app_context():
        db.create_all()
        try:
            from models import User, Category, Product
            from werkzeug.security import generate_password_hash
            if not User.query.filter_by(username='admin').first():
                db.session.add(User(
                    username='admin',
                    email='admin@budsbeez.co.za',
                    full_name='Admin User',
                    phone='0000000000',
                    password_hash=generate_password_hash('admin123'),
                    is_admin=True,
                    is_active=True,
                ))
            if not Category.query.first():
                flowers = Category(name='Flowers', description='Fresh cut flowers for all occasions')
                honey = Category(name='Honey', description='Pure, natural honey')
                produce = Category(name='Fresh Produce', description='Fresh fruits and vegetables')
                db.session.add_all([flowers, honey, produce])
                db.session.commit()
                db.session.add_all([
                    Product(name='Rose Bouquet', description='Beautiful mixed rose bouquet', price=250.00,
                            stock_quantity=50, category_id=flowers.id, is_active=True),
                    Product(name='Wildflower Arrangement', description='Fresh seasonal wildflowers', price=180.00,
                            stock_quantity=40, category_id=flowers.id, is_active=True),
                    Product(name='Pure Raw Honey (500g)', description='Unfiltered, pure raw honey', price=120.00,
                            stock_quantity=100, category_id=honey.id, is_active=True),
                    Product(name='Pure Raw Honey (1kg)', description='Unfiltered, pure raw honey', price=200.00,
                            stock_quantity=80, category_id=honey.id, is_active=True),
                    Product(name='Fresh Strawberries (500g)', description='Sweet, ripe strawberries', price=65.00,
                            stock_quantity=150, category_id=produce.id, is_active=True),
                    Product(name='Mixed Greens', description='Organic mixed greens', price=45.00,
                            stock_quantity=200, category_id=produce.id, is_active=True),
                ])
            db.session.commit()
        except Exception:
            db.session.rollback()


_ensure_db()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))