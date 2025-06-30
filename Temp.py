import pyodbc

# Konfigurasi koneksi
server = 'localhost'            # atau IP/hostname SQL Server kamu
database = 'ChatApp'      # ganti dengan nama database kamu
username = 'user1'              # username SQL Server
password = 'password'           # password SQL Server

# String koneksi
conn_str = (
    f'DRIVER={{ODBC Driver 17 for SQL Server}};'
    f'SERVER={server};'
    f'DATABASE={database};'
    f'UID={username};'
    f'PWD={password}'
)

# Membuat koneksi
conn = pyodbc.connect(conn_str)

# Membuat cursor dan eksekusi query
cursor = conn.cursor()
cursor.execute("SELECT TOP 5 * FROM Users")  # ganti dengan nama tabel kamu

# Tampilkan hasil
for row in cursor.fetchall():
    print(row[1], row[2])

# Tutup koneksi
cursor.close()
conn.close()
