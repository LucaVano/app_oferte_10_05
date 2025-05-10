import os
import logging
import logging.config
from app import app as application
from waitress import serve

# Definisci una funzione per configurare il logging
def setup_logging():
    """Configura il logging usando un file di configurazione se disponibile"""
    config_path = os.path.join(os.path.dirname(__file__), 'logging.conf')
    
    if os.path.exists(config_path):
        # Usa il file di configurazione
        logging.config.fileConfig(config_path, disable_existing_loggers=False)
        logging.info(f"Configurazione logging caricata da {config_path}")
    else:
        # Configurazione di base
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('app.log')
            ]
        )
        logging.info("Configurazione logging di base inizializzata")

# Funzione per determinare se siamo su Synology
def is_synology():
    """Verifica se l'applicazione è in esecuzione su un NAS Synology"""
    return (os.path.exists('/etc/synology-release') or 
            os.path.exists('/usr/syno/synoman/webman') or
            os.environ.get('SYNOLOGY_DSM_VERSION') is not None)

if __name__ == '__main__':
    # Configura il logging
    setup_logging()
    
    # Ottieni la porta dall'ambiente o usa il default 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Determina l'ambiente (produzione/sviluppo)
    env = os.environ.get('FLASK_ENV', 'development')
    
    # Aggiorna l'ambiente se necessario
    if is_synology() and env != 'production':
        env = 'production'
        os.environ['FLASK_ENV'] = 'production'
        os.environ['FLASK_CONFIG'] = 'synology'
        logging.info("Rilevato ambiente Synology, forzata configurazione di produzione")
    
    if env == 'production' or is_synology():
        # Usa Waitress in produzione
        logging.info(f"Avvio server in modalità produzione sulla porta {port}")
        threads = 4  # Limitato per NAS con risorse limitate
        logging.info(f"Server configurato con {threads} threads")
        serve(application, host='0.0.0.0', port=port, threads=threads)
    else:
        # Usa il server di sviluppo Flask
        logging.info(f"Avvio server in modalità sviluppo sulla porta {port}")
        application.run(host='0.0.0.0', port=port, debug=True)