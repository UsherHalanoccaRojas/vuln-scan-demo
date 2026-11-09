from flask import Flask, request
import sqlite3

app = Flask(__name__)

def db():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE users (id INTEGER, name TEXT)")
    conn.execute("INSERT INTO users VALUES (1, 'admin'), (2, 'maria')")
    return conn

@app.route("/")
def home():
    return "<h1>Demo App</h1><a href='/search?q=maria'>Buscar</a> | <a href='/user?id=1'>Usuario</a>"

# Vulnerable a XSS reflejado
@app.route("/search")
def search():
    q = request.args.get("q", "")
    return f"<p>Resultados para: {q}</p>"

# Vulnerable a SQL Injection
@app.route("/user")
def user():
    uid = request.args.get("id", "1")
    rows = db().execute(f"SELECT * FROM users WHERE id = {uid}").fetchall()
    return str(rows)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
