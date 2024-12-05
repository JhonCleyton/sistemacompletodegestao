import sqlite3
import os

def add_usuario_id_column():
    db_path = 'instance/aves.db'
    
    # Verifica se o banco de dados existe
    if not os.path.exists(db_path):
        print("Banco de dados não encontrado!")
        return
    
    # Conecta ao banco de dados
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Verifica se a coluna já existe
        cursor.execute('''
            SELECT count(*) FROM pragma_table_info('nota') WHERE name='usuario_id'
        ''')
        
        if cursor.fetchone()[0] == 0:
            # Adiciona a nova coluna usuario_id
            cursor.execute('''
                ALTER TABLE nota ADD COLUMN usuario_id INTEGER
            ''')
            print("Coluna usuario_id adicionada com sucesso!")
            
            # Define um valor padrão para notas existentes (opcional)
            cursor.execute('''
                UPDATE nota SET usuario_id = 1 WHERE usuario_id IS NULL
            ''')
            print("Valores padrão definidos para notas existentes")
        else:
            print("Coluna usuario_id já existe!")
            
        conn.commit()
        print("Migração concluída com sucesso!")
        
    except Exception as e:
        print(f"Erro durante a migração: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    add_usuario_id_column()
