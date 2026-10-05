import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import app, db

# Use /tmp for SQLite on Vercel (ephemeral)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/budsbeez.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

with app.app_context():
    db.create_all()

application = app
