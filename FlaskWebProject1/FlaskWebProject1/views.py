"""
Routes and views for the flask application.
"""

from datetime import datetime
from flask import render_template, request, Response, jsonify
from FlaskWebProject1 import app
from json import dumps
import asyncio
import websockets
import os
import json

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle


##Variables Globales
uri = "ws://localhost:5555"
headers = {'Access-Control-Allow-Origin': '*'}
files_dir = "AppsDist_Cliente"

def obtenerURLDescargas():
     # Obtén la ruta completa del directorio "Descargas"
    descargas_path = os.path.join(os.path.expanduser('~'), 'Downloads')
    # Verifica si existe el directorio "Descargas", lo crea
    if not os.path.exists(descargas_path):
        descargas_path = os.path.join(os.path.expanduser('~'), 'Descargas')
        if not os.path.exists(descargas_path):
            os.makedirs(descargas_path)

    # Carpeta para guardar
    dir_path = os.path.join(descargas_path, files_dir)
    # Si la carpeta no existe, créala
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"Se ha creado la carpeta de descargas en: {dir_path}")
    else:
        print(f"Se ha almacena en descargas en: {dir_path}")

    #Devuelve ruta
    return dir_path

def generar_reporte_pago(nombre, suscripcion,cantidad, tiempo):
    # Crear un objeto PDF
    dir_path = obtenerURLDescargas()
    # Ruta completa del archivo
    pdf_file = os.path.join(dir_path, "reporte_pago.pdf")
    pdf = SimpleDocTemplate(pdf_file, pagesize=letter)

    # Configuración del texto con diferentes tipos de letra
    styles = getSampleStyleSheet()
    estilo_titulo = styles["Heading1"]
    estilo_normal = styles["BodyText"]

    # Contenido del informe
    contenido = []

    # Título
    titulo = "Reporte de Pago"
    contenido.append(Paragraph(titulo, estilo_titulo))
    contenido.append(Paragraph("\n", estilo_normal))

    # Información de pago
    texto = f"Se realizo un pago de la suscripcion {suscripcion} en {tiempo} a nombre de {nombre}."
    contenido.append(Paragraph(texto, estilo_normal))
    contenido.append(Paragraph("\n", estilo_normal))

    # Tabla con información adicional
    datos_tabla = [['Descripcion', 'Cantidad', 'Fecha'],
                   [f'Renta de servicio de Streaming:{suscripcion}', f"${cantidad}", tiempo]]
    
    tabla = Table(datos_tabla, colWidths=[7 * 30, 3 * 30, 4 * 30])
    tabla.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                               ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                               ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                               ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                               ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                               ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                               ('GRID', (0, 0), (-1, -1), 1, colors.black)]))

    contenido.append(tabla)

    # Agregar la fecha actual al PDF
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    contenido.append(Paragraph(f"\nFecha del reporte: {fecha_actual}", estilo_normal))

    # Construir el PDF
    pdf.build(contenido)

    print(f"El reporte de pago con tabla ha sido generado en: {pdf_file}")
    return "OK"



@app.route('/')
@app.route('/home')
def home():
    """Renders the home page."""
    return render_template(
        'index.html',
        title='Home Page',
        year=datetime.now().year,
    )

@app.route('/contact')
def contact():
    """Renders the contact page."""
    return render_template(
        'contact.html',
        title='Contactos',
        year=datetime.now().year,
        message='Aqui podras encontrar los datos de contacto de los creadores.'
    )

@app.route('/about')
def about():
    """Renders the about page."""
    return render_template(
        'about.html',
        title='About',
        year=datetime.now().year,
        message='Your application description page.'
    )

#Nos muestra los archivos descargados
@app.route('/downloads')
def downloads():
    """Renders the about page."""
    # Obtén la lista de archivos en el directorio
    archivos = []
    dir_path = obtenerURLDescargas()
    # Itera sobre los archivos en el directorio y lee su contenido con codificación 'utf-8'
    for archivo_nombre in os.listdir(dir_path):
        archivo_path = os.path.join(dir_path, archivo_nombre)
        try:
            tamano = os.path.getsize(archivo_path)
            #fecha_modificacion = datetime.fromtimestamp(os.path.getmtime(archivo_path))
            archivos.append({
                'nombre': archivo_nombre,
                'tamano': tamano,
                #'fecha_modificacion': fecha_modificacion
            })

        except Exception as e:
            # Maneja cualquier excepción durante la lectura del archivo
            print(f"Error al leer el archivo {archivo_path}: {str(e)}")
    print(archivos)
    return render_template(
        'lista_archivos.html',
        title='Descargas',
        year=datetime.now().year,
        message='Aqui podras encontrar los archivos que has descargado',
        archivos= archivos
    )

# Solicita la lista de documentos disponibles por el Servidor
@app.route('/server/documentos', methods=['POST'])
async def serverDocs():
    if request.method == 'POST':
        async with websockets.connect(uri) as websocket:
            # Solicitar la lista de archivos
            await websocket.send("get_file_list")

            # Recibe la lista de archivos disponibles
            files = await websocket.recv()
            files = eval(files)  # Convierte la cadena JSON a lista de Python

        # Renderiza la plantilla HTML con la lista de archivos
        if files:
            return Response(response=dumps({'archivos': files}), headers=headers, status=200)
        else:
            # No se encontro el contenido solicitado
            return Response(response=dumps({'message': 'No hay archivos disponibles'}), headers=headers, status=404)
    else:
        # Peticion Incorrecta
        return Response(response=dumps({'message': 'Petiicion Incorrecta'}), headers=headers, status=400)

#Descarga archivo por su id
@app.route('/server/descarga/<number>', methods=['GET'])
async def descargar_archivo(number):
    if request.method == 'GET':
        if number:
            try:
                async with websockets.connect(uri) as websocket:
                    # Solicitar descarga de archivo
                    await websocket.send("get_file_download")
            
                    # Se envia el id del archivo seleccionado
                    choice = int(number);
                    print(f"choice:{choice}")
                    await websocket.send(str(choice))
                    #Recibe nombre del archivo
                    file_name= await websocket.recv()
                    
                    dir_path = obtenerURLDescargas()

                    # Ruta completa del archivo
                    ruta_archivo = os.path.join(dir_path, file_name)
                    i=1
                    num_frames= await websocket.recv()
                    print(f"Se dividira en {num_frames} frames")
                    # Recibe el archivo del servidor
                    with open( ruta_archivo, 'wb') as file:
                        while True:
                            data = await websocket.recv()
                            if data:
                                file.write(data)
                                print(f"F[{i}]/{num_frames}")
                                i += 1
                            else:
                                break
                    return Response(response=dumps({'message': 'Se creo normalmente','url': ruta_archivo}), headers=headers, status=200)

            except websockets.exceptions.ConnectionClosedOK:
                # Esta excepción se levanta cuando la conexión se cierra con status code 1000 (OK)
                print("La conexion WebSocket se cerro normalmente.")
                return Response(response=dumps({'message': 'Se cerro normalmente','url': ruta_archivo}), headers=headers, status=200)

            except Exception as e:
                # Otras excepciones no manejadas específicamente
                print(f"Ocurrio una excepcion: {e}")
                return Response(response=dumps({'message': f'Ocurrio una excepcion{e}'}), headers=headers, status=406)
        else:
            # Datos Incompletos
            return Response(response=dumps({'message': 'No se recibio un id'}), headers=headers, status=406)
    else:
        # Peticion Incorrecta
        return Response(response=dumps({'message': 'Peticion Incorrecta'}), headers=headers, status=400)


#Genera PDF de comprobante de pago
@app.route('/pagos/comprobante',methods=['POST'])
def descargaComprobantePago():
    nombre = "Juan Perez"
    tipo_suscripcion = "Basico"
    costo_suscripcion = 100.0
    fecha_pago = "01/01/2023 15:30"
    mensaje= generar_reporte_pago(nombre,tipo_suscripcion, costo_suscripcion,fecha_pago )
    if mensaje == "OK":
        return Response(response=dumps({'message': 'Se creo correctamente'}), headers=headers, status=200)
    else:
        return Response(response=dumps({'message': 'Ocurrio un problema, vuelva a intentar'}), headers=headers, status=400)
    
