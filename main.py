from flask import Flask, request, session, redirect
import sqlite3
import os
from functools import wraps
from urllib.parse import quote

app = Flask(__name__)
app.secret_key = "repuestos_rd_seguro"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "repuestos.db")


# =========================
# CONEXIÓN SEGURA
# =========================
def conectar():
    try:
        return sqlite3.connect(DB_PATH)
    except Exception as e:
        print("Error BD:", e)
        return None


# =========================
# LOGIN REQUIRED
# =========================
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return wrapper


# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario")
        password = request.form.get("password")

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT usuario FROM usuarios WHERE usuario=? AND password=?",
            (usuario, password)
        )

        user = cursor.fetchone()
        conn.close()

        if user:
            session["user"] = user[0]
            return redirect("/")
        else:
            return "<h2>❌ Login incorrecto</h2><a href='/login'>Volver</a>"

    return """
    <h2>🔐 Login Repuestos RD</h2>
    <form method="post">
        <input name="usuario" placeholder="Usuario" required><br><br>
        <input name="password" type="password" placeholder="Contraseña" required><br><br>
        <button type="submit">Entrar</button>
    </form>
    """


# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# =========================
# HOME
# =========================
@app.route("/")
@login_required
def inicio():
    return f"""
    <h1>🔧 Repuestos RD</h1>
    <p>Bienvenido: {session['user']}</p>

    <a href="/logout">Cerrar sesión</a><br><br>

    <form action="/guardar" method="post">
        <input name="nombre" placeholder="Nombre pieza" required><br>
        <input name="marca" placeholder="Marca" required><br>
        <input name="modelo" placeholder="Modelo"><br>
        <input name="ano" placeholder="Año"><br>
        <input name="precio" placeholder="Precio"><br>
        <input name="telefono" placeholder="WhatsApp (8091234567)" required><br>
        <input name="provincia" placeholder="Provincia"><br>
        <input name="imagen" placeholder="URL imagen (https://...)" required><br>

        <button type="submit">Guardar repuesto</button>
    </form>

    <br>

    <form action="/buscar">
        <input name="q" placeholder="Buscar repuesto" required>
        <button type="submit">Buscar</button>
    </form>

    <a href="/repuestos">📦 Ver catálogo</a>
    """


# =========================
# GUARDAR
# =========================
@app.route("/guardar", methods=["POST"])
@login_required
def guardar():
    try:
        datos = request.form

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO piezas (nombre, marca, modelo, ano, precio, telefono, provincia, imagen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datos.get("nombre", ""),
            datos.get("marca", ""),
            datos.get("modelo", ""),
            datos.get("ano", ""),
            datos.get("precio", ""),
            datos.get("telefono", ""),
            datos.get("provincia", ""),
            datos.get("imagen", "")
        ))

        conn.commit()
        conn.close()

        return "<h2>✅ Guardado correctamente</h2><a href='/'>Volver</a>"

    except Exception as e:
        return f"<h2>❌ Error</h2><p>{e}</p><a href='/'>Volver</a>"


# =========================
# CATÁLOGO
# =========================
@app.route("/repuestos")
@login_required
def ver_repuestos():

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM piezas")
    datos = cursor.fetchall()
    conn.close()

    html = "<h1>📦 Catálogo de Repuestos</h1>"

    for fila in datos:

        nombre = fila[1]
        marca = fila[2]
        modelo = fila[3]
        precio = fila[5]
        telefono = fila[6]
        imagen = fila[8] if len(fila) > 8 else ""

        mensaje = quote(f"Hola, estoy interesado en: {nombre} {marca} {modelo}")
        whatsapp_link = f"https://wa.me/{telefono}?text={mensaje}"

        html += f"""
        <div style="
            border:1px solid #ccc;
            padding:10px;
            margin:10px;
            border-radius:10px;
            display:inline-block;
            width:260px;
            background:white;
        ">

            <img src="{imagen}" style="width:100%; height:150px; object-fit:cover; border-radius:8px;">

            <h3>🔧 {nombre}</h3>
            <p><b>Marca:</b> {marca}</p>
            <p><b>Modelo:</b> {modelo}</p>
            <p><b>Precio:</b> RD${precio}</p>

            <a href="{whatsapp_link}" target="_blank"
               style="
                   display:block;
                   background:green;
                   color:white;
                   padding:8px;
                   text-align:center;
                   border-radius:5px;
                   text-decoration:none;
                   margin-top:10px;
               ">
               📲 WhatsApp
            </a>
        </div>
        """

    html += "<br><br><a href='/'>Volver</a>"
    return html


# =========================
# BUSCAR
# =========================
@app.route("/buscar")
@login_required
def buscar():

    q = request.args.get("q", "")

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM piezas
        WHERE nombre LIKE ? OR marca LIKE ? OR modelo LIKE ?
    """, (f"%{q}%", f"%{q}%", f"%{q}%"))

    datos = cursor.fetchall()
    conn.close()

    html = "<h1>🔍 Resultados</h1>"

    for fila in datos:
        html += f"<p>🔧 {fila[1]} - {fila[2]} - {fila[3]} - RD${fila[5]}</p>"

    html += "<br><a href='/'>Volver</a>"
    return html


# =========================
# RUN (RENDER READY)
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)