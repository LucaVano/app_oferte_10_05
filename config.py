import os

class Config:
    """Configurazione base dell'applicazione Flask"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'valtservice_secret_key_default'
    
    # Directory di base per i file dell'applicazione
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # Directory per i file di dati
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    
    # Directory per i file caricati
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    
    # Estensioni di file permesse
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
    
    # Dimensione massima dei file caricati (10 MB)
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    
    # Template predefiniti per le intestazioni/piè di pagina PDF
    PDF_HEADER_TEMPLATE = os.path.join(BASE_DIR, 'templates', 'pdf', 'header.html')
    PDF_FOOTER_TEMPLATE = os.path.join(BASE_DIR, 'templates', 'pdf', 'footer.html')
    
    # Numero massimo di offerte nella cronologia (0 = illimitato)
    MAX_HISTORY_ITEMS = 0
    
    @staticmethod
    def init_app(app):
        """Inizializza l'applicazione con la configurazione corrente"""
        # Crea le directory necessarie
        os.makedirs(Config.DATA_DIR, exist_ok=True)
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        
        # Imposta le configurazioni nell'oggetto app
        app.config['SECRET_KEY'] = Config.SECRET_KEY
        app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
        app.config['DATA_DIR'] = Config.DATA_DIR
        app.config['ALLOWED_EXTENSIONS'] = Config.ALLOWED_EXTENSIONS
        app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH

class DevelopmentConfig(Config):
    """Configurazione per l'ambiente di sviluppo"""
    DEBUG = True

class ProductionConfig(Config):
    """Configurazione per l'ambiente di produzione"""
    DEBUG = False
    
    # In produzione, usa un secret key più sicuro
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'difficile_da_indovinare_secret_key'
    
    # Opzioni di sicurezza aggiuntive per l'ambiente di produzione
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        # Aggiungi configurazioni di sicurezza specifiche per l'ambiente di produzione
        pass

class SynologyConfig(ProductionConfig):
    """Configurazione specifica per il deployment su NAS Synology"""
    
    # Percorsi specifici per Synology
    SYNOLOGY_WEB_FOLDER = '/volume1/web'
    SYNOLOGY_APP_NAME = 'app_offerte'
    
    @staticmethod
    def is_synology():
        """Verifica se l'applicazione è in esecuzione su un NAS Synology"""
        import os
        # Metodi più affidabili per verificare se siamo su Synology
        return (os.path.exists('/etc/synology-release') or 
                os.path.exists('/usr/syno/synoman/webman') or
                os.environ.get('SYNOLOGY_DSM_VERSION') is not None)
    
    @staticmethod
    def init_app(app):
        """Inizializza l'applicazione con configurazioni specifiche per Synology"""
        ProductionConfig.init_app(app)
        
        import os
        import logging
        
        # Inizializza il logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('app.log')
            ]
        )
        
        # Se siamo su Synology, usa percorsi specifici
        if SynologyConfig.is_synology():
            logging.info("Rilevato ambiente Synology: configurazione percorsi specifici")
            
            # Determina percorso base dell'app
            base_folder = os.path.join(SynologyConfig.SYNOLOGY_WEB_FOLDER, SynologyConfig.SYNOLOGY_APP_NAME)
            
            # Configura percorsi specifici
            app.config['DATA_DIR'] = os.path.join(base_folder, 'data')
            app.config['UPLOAD_FOLDER'] = os.path.join(base_folder, 'static', 'uploads')
            
            logging.info(f"Percorso dati: {app.config['DATA_DIR']}")
            logging.info(f"Percorso upload: {app.config['UPLOAD_FOLDER']}")
            
            # Assicurati che le directory esistano con permessi corretti
            try:
                os.makedirs(app.config['DATA_DIR'], exist_ok=True, mode=0o755)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True, mode=0o755)
                
                # Correggi i permessi se necessario
                os.chmod(app.config['DATA_DIR'], 0o755)
                os.chmod(app.config['UPLOAD_FOLDER'], 0o755)
                logging.info("Directory create/aggiornate correttamente")
            except Exception as e:
                logging.error(f"Errore nella creazione delle directory: {e}")
                
            # Imposta altri parametri specifici per l'ambiente di produzione
            app.config['DEBUG'] = False
            app.config['TESTING'] = False
            app.config['PREFERRED_URL_SCHEME'] = 'https'

# Dizionario di configurazione per permettere la selezione da variabile d'ambiente
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'synology': SynologyConfig,
    'default': SynologyConfig
}