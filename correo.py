import os
import smtplib
import speech_recognition as sr
import threading
import tkinter as tk
import mysql.connector
import requests
from dotenv import load_dotenv
from email.message import EmailMessage
from PIL import Image, ImageTk
import webbrowser
from flask import Flask, request, jsonify

# Cargar variables de entorno
load_dotenv("correo.env")
EMAIL = os.getenv("EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# Conexión a MySQL
conexion = mysql.connector.connect(
    host="localhost",
    user="root",
    password="gus3112++",
    database="gestion_educativa"
)
cursor = conexion.cursor()

# Flask API
app = Flask(__name__)

@app.route("/mensaje", methods=["POST"])
def mejorar_mensaje():
    data = request.get_json()
    texto = data.get("texto", "")

    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "llama3:8b",
                "messages": [
                    {"role": "system", "content": "Corrige este texto y mejora su redacción en español"},
                    {"role": "user", "content": texto}
                ],
                "stream": False
            }
        )
        response.raise_for_status()
        mensaje_corregido = response.json()["message"]["content"]
        return jsonify({"mejorado": mensaje_corregido})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/destinatario", methods=["POST"])
def obtener_destinatario():
    data = request.get_json()
    nombre = data.get("nombre", "")
    cursor.execute(
        "SELECT correo, nombre FROM profesor WHERE nombre = %s UNION SELECT correo, nombre FROM alumno WHERE nombre = %s",
        (nombre, nombre)
    )
    resultado = cursor.fetchone()
    if resultado:
        return jsonify({"correo": resultado[0], "nombre": resultado[1]})
    else:
        return jsonify({"error": "Destinatario no encontrado"}), 404

@app.route("/adjunto", methods=["POST"])
def buscar_archivo():
    data = request.get_json()
    nombre_archivo = data.get("archivo", "").lower()

    directorios = [os.path.expanduser("~/Desktop"), os.path.expanduser("~/Downloads"), os.path.expanduser("~/Documents")]
    for directorio in directorios:
        for raiz, _, archivos in os.walk(directorio):
            for archivo in archivos:
                if nombre_archivo in archivo.lower():
                    ruta = os.path.join(raiz, archivo)
                    return jsonify({"ruta": ruta, "nombre": archivo})
    return jsonify({"error": "Archivo no encontrado"}), 404

@app.route("/enviar", methods=["POST"])
def enviar_correo():
    data = request.get_json()
    destinatario = data.get("destinatario")
    nombre_destinatario = data.get("nombre")
    asunto = data.get("asunto")
    cuerpo = data.get("mensaje")
    archivo = data.get("archivo")

    msg = EmailMessage()
    msg['Subject'] = asunto
    msg['From'] = EMAIL
    msg['To'] = destinatario
    msg.set_content(f"Estimado {nombre_destinatario},\n\n{cuerpo}")

    if archivo and os.path.exists(archivo):
        try:
            with open(archivo, 'rb') as f:
                msg.add_attachment(f.read(), maintype='application', subtype='octet-stream', filename=os.path.basename(archivo))
        except Exception as e:
            return jsonify({"error": f"No se pudo adjuntar el archivo: {str(e)}"}), 500

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return jsonify({"mensaje": "Correo enviado correctamente."})
    except Exception as e:
        return jsonify({"error": f"No se pudo enviar el correo: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)

