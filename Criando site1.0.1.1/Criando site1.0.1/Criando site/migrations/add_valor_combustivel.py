from app import app, db
from flask_migrate import Migrate
from sqlalchemy import Column, Float

migrate = Migrate(app, db)

def upgrade():
    with app.app_context():
        # Add the new column
        db.engine.execute('ALTER TABLE nota ADD COLUMN valor_combustivel FLOAT DEFAULT 0')

def downgrade():
    with app.app_context():
        # Remove the column
        db.engine.execute('ALTER TABLE nota DROP COLUMN valor_combustivel')

if __name__ == '__main__':
    upgrade()
