from __future__ import print_function
import httplib2
import os, io

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from apiclient.http import MediaFileUpload
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None
import auth

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/drive-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Drive API Python Quickstart'
authinst = auth.auth(SCOPES, CLIENT_SECRET_FILE, APPLICATION_NAME)
credentials = authinst.getCredentials()

http = credentials.authorize(httplib2.Http())
drive_service = discovery.build('drive', 'v3', http=http)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "./Archivos"

def listaArchivos(size):
    results = drive_service.files().list(
        pageSize=size,fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])
    if not items:
        print('No files found.')
    else:
        print('Files:')
        for item in items:
            print('{0} ({1})'.format(item['name'], item['id']))

def buscarArchivo(size,query):
    results = drive_service.files().list(
        pageSize=size,fields="nextPageToken, files(id, name)", q=query).execute()
    items = results.get('files', [])
    if not items:
        print('No files found.')
    else:
        print('Files:')
        for item in items:
            print('{0} ({1})'.format(item['name'], item['id']))
            return item['id']

def moveraCarpeta(file_id):
    folder_id = buscarArchivo(1000,"name contains 'Reto'")
    # Retrieve the existing parents to remove
    file = drive_service.files().get(fileId=file_id,fields='parents').execute()
    previous_parents = ",".join(file.get('parents'))
    # Move the file to the new folder
    file = drive_service.files().update(fileId=file_id,addParents=folder_id,removeParents=previous_parents,fields='id, parents').execute()


def subir(filename,filepath,mimetype):
    file_metadata = {'name': filename}
    media = MediaFileUpload('Archivos/' + filepath, mimetype=mimetype)
    file = drive_service.files().create(body=file_metadata,media_body=media,fields='id').execute()
    print('File ID: %s' % file.get('id'))
    moveraCarpeta(file.get('id'))

def descargarArchivo(file_id, filepath):
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print ("Download %d%%." % int(status.progress() * 100))
    with io.open(filepath,"wb") as f:
        fh.seek(0)
        f.write(fh.read())
#downloadFile('id de archivo','nombrearchivoendrive.algo')

def crearCarpeta(name):
    file_metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    file = drive_service.files().create(body=file_metadata,fields='id').execute()
    print ('Folder ID: %s' % file.get('id'))
    moveraCarpeta(file.get('id'))


@app.route("/CrearCarpeta", methods = ['POST'])
def creadorCarpeta():
    if request.method == "POST":
        f = request.form["CrearCarpeta"]  
        crearCarpeta(f)
        return "Carpeta Creada"

@app.route("/")
def subirArchivo():
    return render_template('formulario.html')

@app.route("/uploader", methods = ['POST'])
def uploader():
    if request.method == "POST":
        f = request.files['archivo']
        mimetype = f.content_type 
        filename = secure_filename(f.filename)
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        subir(filename, filename, mimetype)
        return "Archivo subido"


if __name__ == '__main__':
    app.run(debug=False)



    