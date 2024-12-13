import socket
import threading
import tkinter as tk
import sys
import time
import sqlite3
import random

HOST = '127.0.0.1'
# PORT = 65432 # Removed, ports will be passed as argument
client_name = sys.argv[1] if len(sys.argv) > 1 else "Cliente Desconocido"
group_name = sys.argv[2] if len(sys.argv) > 2 else "Grupo Desconocido"
server_ports = sys.argv[3].split(',') if len(sys.argv) > 3 else ["65432"] # Get ports from argument

# Simple encryption (for demonstration purposes only - NOT SECURE for real-world use)
def encrypt(message):
    encrypted = ""
    for char in message:
        encrypted += chr(ord(char) + 1)
    return encrypted

def decrypt(message):
    decrypted = ""
    for char in message:
        decrypted += chr(ord(char) - 1)
    return decrypted

def receive_messages():
    while True:
        try:
            data = client_socket.recv(1024).decode()
            if not data:
                break
            display_message(decrypt(data))
        except Exception as e:
            print(f"Error receiving message: {e}")
            break

def display_message(message, sender=False):
    if isinstance(message, tuple):
        sender_name, actual_message, timestamp = message
        formatted_message = f"{sender_name}: {actual_message} {timestamp}"
    else:
        message_text, timestamp = message.rsplit(' ', 1)  # Separa el mensaje del timestamp
        message_parts = message_text.split(':', 1)  # Separar nombre del mensaje
        sender_name = message_parts[0]
        actual_message = message_parts[1].strip()
        formatted_message = f"{sender_name}: {actual_message} {timestamp}"

    # Cuadro para el mensaje
    message_frame = tk.Frame(messages_frame, bg="#333333")
    message_frame.pack(fill='x', pady=5)

    # Mostrar nombre alineado a la izquierda (o "Yo" si es el mensaje del propio cliente)
    name_label = tk.Label(message_frame, text=sender_name if not sender else "Yo", bg="#333333", fg="#4caf50", font=("Helvetica", 10, "bold"), anchor="w")
    name_label.pack(fill="x", side="top", padx=5)

    # Mostrar mensaje alineado a la izquierda
    message_label = tk.Label(message_frame, text=actual_message, wraplength=300, bg="#333333", fg="white", font=entry_font, justify="left", anchor="w")
    message_label.pack(fill="x", side="top", padx=5)

    # Mostrar la hora siempre alineada a la derecha
    time_label = tk.Label(message_frame, text=timestamp, bg="#333333", fg="white", font=("Helvetica", 10))
    time_label.pack(side='right', padx=5)

    # Actualizar la barra de desplazamiento
    messages_canvas.yview_moveto(1)

def send_message():
    message = entry.get()
    if message:
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        formatted_message_for_self = f"{client_name}: {message} {timestamp}"  # Formato para el propio cliente
        encrypted_message_for_server = encrypt(f"{client_name}: {message}")  # Solo envía el mensaje
        client_socket.send(encrypted_message_for_server.encode())
        display_message(formatted_message_for_self, sender=True)  # Marca que es el mensaje del propio cliente
        entry.delete(0, tk.END)

# Client setup
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Try to connect to any of the available servers
for port in server_ports:
    try:
        client_socket.connect((HOST, int(port)))
        print(f"Connected to server on port {port}")
        break
    except:
        print(f"Could not connect to server on port {port}")
        continue
else:
    print("Could not connect to any server")
    sys.exit()

client_socket.send(client_name.encode())  # Send the client name to the server

# Database setup
conn = sqlite3.connect('chat_history.db', check_same_thread=False)
cursor = conn.cursor()

# GUI setup
root = tk.Tk()
root.title(f"Chat - {client_name} en {group_name}")
root.geometry("400x500")
root.configure(bg="#1e1e1e")

# Estilos
label_font = ("Helvetica", 12, "bold")
entry_font = ("Helvetica", 12)
button_font = ("Helvetica", 12, "bold")

# Frame principal
main_frame = tk.Frame(root)
main_frame.pack(fill='both', expand=True)

# Canvas para la barra de desplazamiento
messages_canvas = tk.Canvas(main_frame, bg="#1e1e1e")
scrollbar = tk.Scrollbar(main_frame, command=messages_canvas.yview)
scrollbar.pack(side="right", fill="y")

messages_frame = tk.Frame(messages_canvas, bg="#1e1e1e")

# Función para actualizar el scroll
def on_configure(event):
    messages_canvas.configure(scrollregion=messages_canvas.bbox("all"))

messages_frame.bind("<Configure>", on_configure)
messages_canvas.create_window((0, 0), window=messages_frame, anchor="nw")
messages_canvas.pack(side="left", fill="both", expand=True)
messages_canvas.configure(yscrollcommand=scrollbar.set)

# Campo de entrada para mensajes
entry = tk.Entry(root, font=entry_font, width=30, bg="#2e2e2e", fg="white")
entry.pack(pady=10)

# Botón de enviar
send_button = tk.Button(root, text="Enviar", font=button_font, bg="#4caf50", fg="white", activebackground="#45a049", width=15, command=send_message)
send_button.pack(pady=10)

# Load chat history
cursor.execute("SELECT sender, message, timestamp FROM messages")
chat_history = cursor.fetchall()
for message in chat_history:
    display_message(message)

# Hilo para recibir mensajes
receive_thread = threading.Thread(target=receive_messages)
receive_thread.start()

root.mainloop()
