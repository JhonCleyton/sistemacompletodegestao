from app import app, db, User

with app.app_context():
    users = User.query.all()
    print("\nUsuários cadastrados:")
    print("-" * 50)
    for user in users:
        print(f"Username: {user.username}")
        print(f"Role: {user.role}")
        print(f"Nome: {user.nome_completo}")
        print(f"Ativo: {user.ativo}")
        print("-" * 50)
