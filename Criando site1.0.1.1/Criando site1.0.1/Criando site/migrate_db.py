import sqlite3
import os

def migrate_database():
    db_path = 'instance/aves.db'
    
    # Verifica se o banco de dados existe
    if not os.path.exists(db_path):
        print("Banco de dados não encontrado!")
        return
    
    # Conecta ao banco de dados
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Adiciona a nova coluna em_edicao se ela não existir
        cursor.execute('''
            SELECT count(*) FROM pragma_table_info('nota') WHERE name='em_edicao'
        ''')
        
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                ALTER TABLE nota ADD COLUMN em_edicao BOOLEAN DEFAULT FALSE
            ''')
            print("Coluna em_edicao adicionada com sucesso!")
        else:
            print("Coluna em_edicao já existe!")
            
        conn.commit()
        print("Migração concluída com sucesso!")
        
    except Exception as e:
        print(f"Erro durante a migração: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()
