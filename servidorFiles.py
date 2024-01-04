import asyncio
import websockets
import os
import json,datetime
from websockets.exceptions import ConnectionClosedOK
import math
FRAGMENT_SIZE = 524288#262144

async def handle_client(websocket, path, files_dir):
    try:
        options = await websocket.recv()

        if options == "get_file_list":
            # Obtén la lista de archivos en el directorio
            archivos = []
            id = 0
            # Itera sobre los archivos en el directorio y lee su contenido con codificación 'utf-8'
            for archivo_nombre in os.listdir(files_dir):
                archivo_path = os.path.join(files_dir, archivo_nombre)
                try:
                    tamano = os.path.getsize(archivo_path)
                    #fecha_modificacion = datetime.fromtimestamp(os.path.getmtime(archivo_path))
                    id+=1
                    archivos.append({
                        'nombre': archivo_nombre,
                        'tamano': tamano,
                        'id': id,
                        #'fecha_modificacion': fecha_modificacion
                    })

                except Exception as e:
                    # Maneja cualquier excepción durante la lectura del archivo
                    print(f"Error al leer el archivo {archivo_path}: {str(e)}")

            # Envía la lista de archivos al servidor
            await websocket.send(json.dumps(archivos))

            print("End: get_file_list")
            # Imprime la lista de archivos en el cliente
            #print("Archivos disponibles:")
            #for i, file in enumerate(files, start=1):
            #    print(f"{i}. {file}")
        elif options == "get_file_download":
            print("Start: get_file_download")
            # Obtén la lista de archivos en el directorio
            files = [f for f in os.listdir(files_dir) if os.path.isfile(os.path.join(files_dir, f))]
            
            # Lee el archivo seleccionado y envíalo al servidor
            choice = int(await websocket.recv())
            selected_file = files[choice - 1]
            #Envia el nombre del archivo
            await websocket.send(selected_file)

            print(f"Archivo: {choice}-{selected_file}")
            file_path = os.path.join(files_dir, selected_file)
            with open(file_path, 'rb') as file:
                data = file.read()
                #await websocket.send(data)

            division = len(data)/FRAGMENT_SIZE 
            #print("Se mandaran"+division+" paquetes")
            if division > 1:
                await websocket.send(str(math.ceil(division)))
                for i in range(0, len(data), FRAGMENT_SIZE):
                    fragment = data[i:i + FRAGMENT_SIZE]
                    await websocket.send(fragment)
            else:
                await websocket.send("1")
                await websocket.send(data)

            # Envía un fragmento vacío para indicar el final
            await websocket.send("")

            print("End: get_file_download")
        else:
            # Envía error
            await websocket.send(json.dumps("Error: Funcion no encontrada"))
            
    except ConnectionClosedOK:
        pass  # La conexión se cerró de manera ordenada

    print("Conexión cerrada. Servidor esperando conexiones...")

async def server(websocket, path):
    print(f"Conexión establecida desde: {websocket.remote_address}")

    await handle_client(websocket, path, 'archivos_servidor')

if __name__ == "__main__":
    start_server = websockets.serve(server, "localhost", 5555, max_size=None)

    print("Servidor esperando conexiones...")

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

