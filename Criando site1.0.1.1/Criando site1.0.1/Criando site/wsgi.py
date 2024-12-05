import os

# Configurar variáveis de ambiente
os.environ['PRODUCTION'] = 'True'
os.environ['SECRET_KEY'] = 'sua-chave-secreta-muito-segura'

from app import app as application

if __name__ == '__main__':
    application.run()
