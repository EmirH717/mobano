import json
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId

# -------------------------------------------------------
# CONFIGURACIÓN DE MONGO
# -------------------------------------------------------
MONGO_URI = "mongodb+srv://nathaniel_db_user:kdgwWVa2u9vwjMCP@mobano.7xleahm.mongodb.net/mobano_db?retryWrites=true&w=majority&appName=mobano"
DB_NAME = "mobano_db"

# -------------------------------------------------------
# INICIALIZACIÓN DE FLASK
# -------------------------------------------------------
app = Flask(__name__)

# Variables globales para Mongo
client = None
db = None
productos_collection = None
cotizaciones_collection = None
tipos_producto_collection = None
db_connected = False


# -------------------------------------------------------
# CONEXIÓN A MONGO
# -------------------------------------------------------
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")  # Confirmar conexión

    db = client[DB_NAME]

    productos_collection = db["productos"]
    cotizaciones_collection = db["cotizaciones"]
    tipos_producto_collection = db["tipos_producto"]

    db_connected = True
    print("✅ Conexión a MongoDB Atlas exitosa.")

except Exception as e:
    db_connected = False
    print("❌ ERROR: No se pudo conectar a MongoDB.")
    print(f"Detalle: {e}")


# -------------------------------------------------------
# FUNCIÓN: OBTENER PRODUCTOS AGRUPADOS POR TIPO
# -------------------------------------------------------
def obtener_productos_agrupados():
    if not db_connected:
        print("⚠ No hay conexión a MongoDB.")
        return {}

    try:
        tipos = list(tipos_producto_collection.find({}))
        productos = list(productos_collection.find({}))

        resultado = {}

        for t in tipos:
            nombre_tipo = t.get("nombre")
            if not nombre_tipo:
                continue

            productos_relacionados = [
                {
                    **p,
                    "_id": str(p["_id"])
                }
                for p in productos
                if p.get("tipo", "").strip().lower() == nombre_tipo.strip().lower()
            ]

            if productos_relacionados:
                resultado[nombre_tipo] = productos_relacionados

        return resultado

    except Exception as e:
        print(f"❌ Error al agrupar productos: {e}")
        return {}


# -------------------------------------------------------
# RUTAS
# -------------------------------------------------------

@app.route("/")
def index():
    if not db_connected:
        return render_template("index.html", productos_por_tipo={})

    productos = obtener_productos_agrupados()
    return render_template("index.html", productos_por_tipo=productos)


@app.route("/cotizacion")
def cotizacion_form():
    return render_template("cotizacion.html")


@app.route("/submit_quotation", methods=["POST"])
def submit_quotation():
    if not db_connected:
        return jsonify({
            "success": False,
            "message": "❌ No hay conexión a la base de datos."
        }), 500

    try:
        data = {
            "client_name": request.form.get("client_name"),
            "client_last_name": request.form.get("client_last_name"),
            "client_email": request.form.get("client_email"),
            "client_phone": request.form.get("client_phone"),
            "required_date": request.form.get("required_date"),
            "required_time": request.form.get("required_time"),
            "quotation_details": request.form.get("quotation_details"),
            "submission_timestamp": datetime.now().isoformat(),
            "status": "pendiente"
        }

        # Validación de campos
        if not data["client_name"] or not data["client_email"] or not data["quotation_details"]:
            return jsonify({
                "success": False,
                "message": "⚠ Faltan campos obligatorios."
            }), 400

        cotizaciones_collection.insert_one(data)

        return jsonify({
            "success": True,
            "message": "🎉 ¡Solicitud enviada con éxito!"
        }), 200

    except Exception as e:
        print(f"❌ Error al guardar cotización: {e}")
        return jsonify({
            "success": False,
            "message": "❌ Error interno del servidor."
        }), 500


# -------------------------------------------------------
# EJECUCIÓN
# -------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
