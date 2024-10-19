import subprocess
import os
import zipfile
import threading

from PyQt6.QtWidgets import QApplication, QVBoxLayout, QProgressBar, QWidget, QLabel
from PyQt6.QtCore import pyqtSignal
import psutil

IS_DEV = False

ZIP_DIRECTORY = '' if IS_DEV else 'tempupdate'
CLIENT_DIRECTORY = 'client_folder' if IS_DEV else ''

def kill_client_process():
    PROCESS_NAME = 'electron.exe' if IS_DEV else 'WaddleForeverClient.exe'
    for process in psutil.process_iter(['pid', 'name']):
        try:
            if process.info['name'] == PROCESS_NAME:
                process.terminate()
                if IS_DEV:
                    print(f"Terminated process {process.info['name']} (PID: {process.info['pid']})")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

class UpdaterApp(QApplication):
    def __init__(self):
        super().__init__([])
        self.window = Updater()
        self.window.finished.connect(self.close_app)
        self.window.show()

    def close_app(self):
        QApplication.quit()

class Updater(QWidget):
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Waddle Forever Updater")
        self.setGeometry(300, 300, 300, 150)
        
        self.layout = QVBoxLayout()
        
        self.message = QLabel(self)
        self.layout.addWidget(self.message)

        self.progress_bar = QProgressBar(self)
        self.layout.addWidget(self.progress_bar)
        
        self.setLayout(self.layout)

        self.unzip_folders()

    def unzip_folders(self):
        dirs = os.listdir(os.path.join(os.getcwd(), ZIP_DIRECTORY))
        media_zips = ['static', 'special', 'clothing']
        self.existing_medias = []
        for zip in media_zips:
            if zip + '.zip' in dirs:
                self.existing_medias.append(zip)
        
        self.total_zips = len(self.existing_medias) + 1
        self.unzip_client()

    
    def unzip_client(self):
        self.start_unzip('client.zip', CLIENT_DIRECTORY, f'Extracting folders: client.zip (1/{self.total_zips})', self.unzip_medias)

    def next_media(self):
        self.current_media += 1

    def unzip_media(self):
        self.next_media()
        if (self.current_media >= len(self.existing_medias)):
            self.migrate_database()
        else:
            zip = self.existing_medias[self.current_media]
            zip_name = zip + '.zip'
            self.start_unzip(zip_name, 'media/' + zip, f'Extracting folders: {zip_name} ({self.current_media + 2}/{self.total_zips})', self.unzip_media)

    def unzip_medias(self):
        self.current_media = -1
        os.makedirs('media', exist_ok=True)
        self.unzip_media()
        
    def start_unzip(self, zip_dir, output_folder, message, finish_callback):
        output_dir = os.path.join(os.getcwd(), output_folder)
        zip_dir = os.path.join(os.getcwd(), ZIP_DIRECTORY, zip_dir)
        self.message.setText(message)
        self.zip_thread = threading.Thread(target=self.unzip_with_progress, args=(zip_dir, output_dir, finish_callback))
        self.zip_thread.start()
        
    def unzip_with_progress(self, zip_path, extract_to, finish_callback):
        os.makedirs(extract_to, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            total_files = len(zip_ref.infolist())
            for i, file in enumerate(zip_ref.infolist()):
                zip_ref.extract(file, extract_to)
                self.update_progress(i + 1, total_files)

        finish_callback()

    def update_progress(self, current, total):
        percentage = int((current / total) * 100)
        self.progress_bar.setValue(percentage)
    
    def migrate_database(self):
        # current no logic
        self.end_update()
    
    def end_update(self):
        subprocess.Popen(os.path.join(os.getcwd(), 'WaddleForeverClient.exe'))
        self.finished.emit()

kill_client_process()
app = UpdaterApp()
app.exec()
