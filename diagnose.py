#!/usr/bin/env python3
"""
Script di diagnostica migliorato per l'app di gestione offerte su Synology NAS.
Questo script verifica le configurazioni, i permessi, le dipendenze e l'integrità dei dati.
"""

import os
import sys
import importlib
import platform
import subprocess
import logging
import json
from pathlib import Path
from datetime import datetime

# Configurazione del logging
log_file = f"diagnose_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file)
    ]
)

def print_section(title):
    """Stampa un'intestazione di sezione con formattazione"""
    logging.info("\n" + "=" * 60)
    logging.info(f" {title} ".center(60, "="))
    logging.info("=" * 60)

def check_python_version():
    """Verifica la versione di Python"""
    print_section("VERIFICA VERSIONE PYTHON")
    version = platform.python_version()
    logging.info(f"Versione Python: {version}")
    if version < "3.6":
        logging.error("⚠️ Versione Python troppo vecchia. Richiesta 3.6 o superiore.")
        return False
    logging.info("✅ Versione Python OK")
    return True

def fix_common_problems():
    """Tenta di correggere problemi comuni"""
    print_section("TENTATIVI DI CORREZIONE")
    
    # Correggi i permessi
    current_dir = Path(__file__).parent.absolute()
    data_dir = current_dir / "data"
    uploads_dir = current_dir / "static" / "uploads"
    logs_dir = current_dir / "logs"
    
    # Crea le directory mancanti
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(uploads_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)
    
    logging.info("Tentativo di correzione dei permessi...")
    try:
        # Cambia i permessi in modo ricorsivo
        for path in [data_dir, uploads_dir, logs_dir]:
            for root, dirs, files in os.walk(path):
                for d in dirs:
                    dir_path = os.path.join(root, d)
                    os.chmod(dir_path, 0o755)
                for f in files:
                    file_path = os.path.join(root, f)
                    os.chmod(file_path, 0o644)
        
        # Rendi eseguibili gli script
        script_files = [
            current_dir / "start.sh",
            current_dir / "install_synology.sh"
        ]
        
        for script in script_files:
            if script.exists():
                os.chmod(script, 0o755)
                logging.info(f"✅ Reso eseguibile: {script}")
        
        logging.info("✅ Permessi corretti")
    except Exception as e:
        logging.error(f"⚠️ Errore nella correzione dei permessi: {e}")
    
    # Controlla se siamo su Synology e tenta di cambiare proprietario
    if os.path.exists('/etc/synology-release'):
        try:
            logging.info("Tentativo di cambio proprietario (richiede privilegi di root)...")
            subprocess.run(['chown', '-R', 'http:http', str(current_dir)], check=True)
            logging.info("✅ Proprietario cambiato a http:http")
        except Exception as e:
            logging.error(f"⚠️ Errore nel cambio proprietario: {e}")
    
    # Verifica se il servizio è configurato e attivo
    if os.path.exists('/bin/systemctl') and os.path.exists('/etc/systemd/system/app-offerte.service'):
        try:
            logging.info("Tentativo di riavvio del servizio app-offerte...")
            subprocess.run(['systemctl', 'restart', 'app-offerte'], check=True)
            logging.info("✅ Servizio riavviato")
        except Exception as e:
            logging.error(f"⚠️ Errore nel riavvio del servizio: {e}")
    
    # Crea un file di indice se mancante
    index_file = data_dir / "offerte_index.json"
    if not index_file.exists():
        try:
            logging.info("Creazione file indice mancante...")
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
            logging.info("✅ File indice creato")
        except Exception as e:
            logging.error(f"⚠️ Errore nella creazione del file indice: {e}")
    
    # Crea un file contatore se mancante
    counter_file = data_dir / "counter.json"
    if not counter_file.exists():
        try:
            logging.info("Creazione file contatore mancante...")
            current_year = str(datetime.now().year)
            with open(counter_file, 'w', encoding='utf-8') as f:
                json.dump({current_year: 0}, f)
            logging.info("✅ File contatore creato")
        except Exception as e:
            logging.error(f"⚠️ Errore nella creazione del file contatore: {e}")
    
    return True

def main():
    """Funzione principale"""
    print_section("DIAGNOSI APP OFFERTE VALTSERVICE")
    logging.info(f"Data e ora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info(f"Percorso script: {os.path.abspath(__file__)}")
    
    # Esegui tutti i controlli
    python_ok = check_python_version()
    venv_ok = check_venv()
    deps_ok = check_dependencies()
    perms_ok = check_file_permissions()
    network_ok = check_network()
    synology_ok = check_synology_environment()
    db_ok = check_database_integrity()
    logs_ok = check_logs()
    
    # Sintesi dei risultati
    print_section("RISULTATI")
    results = [
        ("Versione Python", python_ok),
        ("Ambiente virtuale", venv_ok),
        ("Dipendenze", deps_ok),
        ("Permessi file", perms_ok),
        ("Rete", network_ok),
        ("Ambiente Synology", synology_ok),
        ("Database", db_ok),
        ("Analisi log", logs_ok)
    ]
    
    all_ok = True
    for check_name, status in results:
        icon = "✅" if status else "⚠️"
        logging.info(f"{icon} {check_name}")
        if not status:
            all_ok = False
    
    if not all_ok:
        logging.info("\nTrovati problemi. Tentativo di correzione automatica...")
        fix_common_problems()
    
    # Risultato finale
    print_section("CONCLUSIONE")
    if all_ok:
        logging.info("✅ Tutti i controlli sono passati. L'app dovrebbe funzionare correttamente.")
    else:
        logging.info("⚠️ Ci sono problemi che potrebbero impedire il corretto funzionamento dell'app.")
        logging.info(f"   Si consiglia di verificare il log ({log_file}) per i dettagli.")
    
    logging.info("\nConsigli per la risoluzione dei problemi:")
    logging.info("1. Riavviare l'applicazione: systemctl restart app-offerte")
    logging.info("2. Controllare i log: tail -f logs/app.log")
    logging.info("3. Verificare i permessi: chown -R http:http /volume1/web/app_offerte")
    logging.info("4. Reinstallare le dipendenze: source venv/bin/activate && pip install -r requirements-synology.txt")
    logging.info("5. URL dell'applicazione: http://[ip-nas]:5002")
    
    logging.info(f"\nLog diagnosi salvato in: {log_file}")

if __name__ == "__main__":
    main()

def check_venv():
    """Verifica se l'ambiente virtuale è attivo e configurato correttamente"""
    print_section("VERIFICA AMBIENTE VIRTUALE")
    
    is_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if is_venv:
        logging.info(f"✅ Ambiente virtuale attivo: {sys.prefix}")
    else:
        logging.warning("⚠️ Ambiente virtuale non attivo - le dipendenze potrebbero essere in conflitto")
        
        # Controlla se l'ambiente virtuale esiste
        app_dir = Path(__file__).parent.absolute()
        venv_path = app_dir / "venv"
        
        if venv_path.exists():
            logging.info(f"✅ Directory ambiente virtuale trovata: {venv_path}")
            logging.info("ℹ️ Attiva l'ambiente virtuale con: source venv/bin/activate")
        else:
            logging.warning(f"⚠️ Directory ambiente virtuale non trovata in: {venv_path}")
            logging.info("ℹ️ Crea un ambiente virtuale con: python3 -m venv venv")
    
    return is_venv

def check_dependencies():
    """Verifica le dipendenze Python"""
    print_section("VERIFICA DIPENDENZE")
    required_modules = [
        ("flask", "Flask"),
        ("werkzeug", "Werkzeug"),
        ("jinja2", "Jinja2"),
        ("reportlab", "ReportLab"),
        ("PIL", "Pillow"),
        ("dateutil", "python-dateutil"),
        ("waitress", "Waitress"),
        ("dotenv", "python-dotenv")
    ]
    
    all_ok = True
    
    # Verifica le dipendenze nel venv attivo
    for module_name, package_name in required_modules:
        try:
            if module_name == "PIL":
                module = importlib.import_module("PIL")
            else:
                module = importlib.import_module(module_name)
            
            version = getattr(module, "__version__", "Sconosciuta")
            logging.info(f"✅ {module_name}: Versione {version}")
        except ImportError:
            logging.error(f"⚠️ {module_name}: NON INSTALLATO")
            logging.info(f"  Prova a installarlo con: pip install {package_name}")
            all_ok = False
    
    # Verifica se il venv è attivo ma le dipendenze mancano
    if not all_ok and hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        logging.warning("ℹ️ Sei in un ambiente virtuale ma mancano alcune dipendenze")
        logging.info("  Prova a installare tutte le dipendenze con: pip install -r requirements-synology.txt")
    
    return all_ok

def check_file_permissions():
    """Verifica i permessi dei file e delle directory"""
    print_section("VERIFICA PERMESSI")
    
    # Determina percorsi importanti
    current_dir = Path(__file__).parent.absolute()
    data_dir = current_dir / "data"
    uploads_dir = current_dir / "static" / "uploads"
    logs_dir = current_dir / "logs"
    
    # Crea le directory se non esistono
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(uploads_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)
    
    # Controlla i permessi
    paths_to_check = [
        current_dir,
        data_dir,
        uploads_dir,
        logs_dir,
        current_dir / "app.py",
        current_dir / "wsgi.py",
        current_dir / "start.sh"
    ]
    
    all_ok = True
    for path in paths_to_check:
        if path.exists():
            # Verifica permessi
            mode = path.stat().st_mode
            readable = os.access(path, os.R_OK)
            writable = os.access(path, os.W_OK)
            executable = os.access(path, os.X_OK) if path.is_dir() or path.name.endswith('.sh') else True
            
            status = "✅" if (readable and writable and executable) else "⚠️"
            perms = f"r{'w' if writable else '-'}{'x' if executable else '-'}"
            logging.info(f"{status} {path}: {perms}")
            
            if not (readable and writable and (executable if path.is_dir() or path.name.endswith('.sh') else True)):
                all_ok = False
                
                # Verifica l'utente proprietario
                try:
                    import pwd
                    uid = path.stat().st_uid
                    user = pwd.getpwuid(uid).pw_name
                    logging.info(f"  Proprietario: {user} (UID: {uid})")
                except:
                    logging.info(f"  Impossibile determinare il proprietario")
        else:
            logging.error(f"⚠️ {path}: NON ESISTE")
            all_ok = False
    
    return all_ok

def check_network():
    """Verifica la configurazione di rete"""
    print_section("VERIFICA RETE")
    
    # Controlla se il server è in ascolto sulla porta 5002
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = s.connect_ex(('127.0.0.1', 5002))
        if result == 0:
            logging.info("✅ La porta 5002 è in uso. L'app sembra essere in esecuzione.")
            
            # Prova a fare una richiesta HTTP di base
            try:
                import urllib.request
                response = urllib.request.urlopen('http://127.0.0.1:5002/')
                status = response.getcode()
                logging.info(f"✅ L'app risponde con codice stato HTTP: {status}")
            except Exception as e:
                logging.warning(f"⚠️ Non è stato possibile connettersi all'app via HTTP: {e}")
        else:
            logging.warning("⚠️ La porta 5002 NON è in uso. L'app potrebbe non essere in esecuzione.")
            
            # Controlla se altre porte sono in uso (5000, 8000)
            alternate_ports = [5000, 8000]
            for port in alternate_ports:
                result = s.connect_ex(('127.0.0.1', port))
                if result == 0:
                    logging.info(f"ℹ️ Trovato server in ascolto sulla porta alternativa {port}")
        s.close()
    except Exception as e:
        logging.error(f"⚠️ Errore nel controllo della porta: {e}")
    
    # Controlla gli indirizzi IP disponibili
    try:
        hostname = socket.gethostname()
        
        # IP locale
        local_ip = socket.gethostbyname(hostname)
        logging.info(f"IP locale: {local_ip}")
        
        # Cerca di ottenere altri IP dalla rete
        all_ips = socket.getaddrinfo(hostname, None)
        network_ips = set()
        
        for ip_info in all_ips:
            addr = ip_info[4][0]
            if addr != '127.0.0.1' and addr != local_ip and not addr.startswith('::') and not addr.startswith('fe80'):
                network_ips.add(addr)
        
        if network_ips:
            logging.info(f"Altri IP disponibili: {', '.join(network_ips)}")
            for ip in network_ips:
                logging.info(f"URL dell'app: http://{ip}:5002")
    except Exception as e:
        logging.error(f"⚠️ Errore nel recupero degli IP: {e}")
    
    return True

def check_synology_environment():
    """Verifica se l'ambiente è Synology"""
    print_section("VERIFICA AMBIENTE SYNOLOGY")
    
    # Controlla se siamo su Synology
    is_synology = (
        os.path.exists('/etc/synology-release') or 
        os.path.exists('/usr/syno/synoman/webman')
    )
    
    if is_synology:
        logging.info("✅ Ambiente Synology rilevato")
        
        # Controlla il percorso /volume1/web
        web_path = Path("/volume1/web")
        if web_path.exists() and web_path.is_dir():
            logging.info("✅ Percorso /volume1/web esiste")
        else:
            logging.error("⚠️ Percorso /volume1/web non trovato")
        
        # Controlla l'utente http
        try:
            import pwd
            pwd.getpwnam('http')
            logging.info("✅ Utente 'http' esiste")
        except KeyError:
            logging.error("⚠️ Utente 'http' non trovato")
        
        # Controlla lo stato del servizio systemd (se disponibile)
        if os.path.exists('/bin/systemctl'):
            try:
                result = subprocess.run(['systemctl', 'status', 'app-offerte.service'], 
                                       capture_output=True, text=True)
                if 'Active: active (running)' in result.stdout:
                    logging.info("✅ Servizio app-offerte.service è attivo e in esecuzione")
                elif 'Active:' in result.stdout:
                    status_line = [line for line in result.stdout.split('\n') if 'Active:' in line][0]
                    logging.warning(f"⚠️ Servizio app-offerte.service stato: {status_line.strip()}")
                else:
                    logging.warning("⚠️ Impossibile determinare lo stato del servizio app-offerte.service")
            except Exception as e:
                logging.error(f"⚠️ Errore nel controllo del servizio systemd: {e}")
    else:
        logging.info("ℹ️ Non siamo su un NAS Synology")
    
    return is_synology

def check_database_integrity():
    """Verifica l'integrità del database"""
    print_section("VERIFICA DATABASE")
    
    data_dir = Path(__file__).parent.absolute() / "data"
    index_file = data_dir / "offerte_index.json"
    counter_file = data_dir / "counter.json"
    
    # Verifica che i file di base esistano
    files_ok = True
    for file_path in [index_file, counter_file]:
        if file_path.exists():
            logging.info(f"✅ {file_path.name} esiste")
            
            # Verifica che il file sia un JSON valido
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    json.load(f)
                logging.info(f"✅ {file_path.name} è un JSON valido")
            except json.JSONDecodeError:
                logging.error(f"⚠️ {file_path.name} non è un JSON valido")
                files_ok = False
            except Exception as e:
                logging.error(f"⚠️ Errore nella lettura di {file_path.name}: {e}")
                files_ok = False
        else:
            logging.info(f"💡 {file_path.name} non esiste (sarà creato all'avvio)")
    
    # Controlla le offerte esistenti
    offer_count = 0
    problems_found = 0
    customer_dirs = [d for d in data_dir.iterdir() if d.is_dir() and d.name not in ["__pycache__"]]
    
    for customer_dir in customer_dirs:
        offer_dirs = [d for d in customer_dir.iterdir() if d.is_dir()]
        for offer_dir in offer_dirs:
            json_file = offer_dir / "dati_offerta.json"
            if json_file.exists():
                offer_count += 1
                
                # Verifica che il file sia un JSON valido
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if "tabs" not in data:
                            logging.warning(f"⚠️ Offerta {offer_dir.name} non ha il campo 'tabs'")
                            problems_found += 1
                        elif not isinstance(data["tabs"], list):
                            logging.warning(f"⚠️ Offerta {offer_dir.name} ha 'tabs' non valido (non è una lista)")
                            problems_found += 1
                        
                        # Verifica ID
                        if "id" not in data:
                            logging.warning(f"⚠️ Offerta {offer_dir.name} non ha il campo 'id'")
                            problems_found += 1
                        
                        # Verifica congruenza offer_number / cartella
                        if "offer_number" in data and data["offer_number"] != offer_dir.name:
                            logging.warning(f"⚠️ Offerta {offer_dir.name}: il numero offerta nei dati ({data['offer_number']}) non corrisponde al nome della cartella")
                            problems_found += 1
                except Exception as e:
                    logging.error(f"⚠️ Errore nella lettura di {json_file}: {e}")
                    problems_found += 1
                    files_ok = False
    
    logging.info(f"Trovate {offer_count} offerte")
    if problems_found > 0:
        logging.warning(f"⚠️ Trovati {problems_found} problemi con i file delle offerte")
    else:
        logging.info("✅ Nessun problema trovato nei file delle offerte")
    
    return files_ok

def check_logs():
    """Analizza i log per errori noti"""
    print_section("ANALISI LOG")
    
    log_file = Path(__file__).parent.absolute() / "app.log"
    if not log_file.exists():
        log_dir = Path(__file__).parent.absolute() / "logs"
        logs = list(log_dir.glob("*.log"))
        
        if logs:
            log_file = max(logs, key=os.path.getmtime)  # Prendi il log più recente
            logging.info(f"File di log principale non trovato, analizzo {log_file.name}")
        else:
            logging.info("Nessun file di log trovato.")
            return True
    
    # Errori da cercare
    error_patterns = [
        ("invalid literal for int", "Errore nel parsing degli indici tab"),
        ("Permission denied", "Problema con i permessi dei file"),
        ("No such file or directory", "File o cartella mancante"),
        ("Internal Server Error", "Errore interno del server"),
        ("KeyError", "Chiave mancante in un dizionario"),
        ("IndexError", "Indice fuori dai limiti"),
        ("TypeError", "Errore di tipo"),
        ("ValueError", "Valore non valido"),
        ("Input/output error", "Errore di input/output (I/O)"),
        ("TemplateNotFound", "Template non trovato"),
        ("ImportError", "Errore di importazione"),
        ("ModuleNotFoundError", "Modulo non trovato"),
        ("RuntimeError", "Errore di runtime"),
        ("AttributeError", "Attributo non trovato"),
        ("'Flask' object has no attribute", "Problema di configurazione Flask")
    ]
    
    errors_found = {}
    line_count = 0
    recent_errors = 0  # Conta gli errori nelle ultime 100 righe
    
    # Leggi il file di log e cerca gli errori
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            line_count = len(lines)
            
            # Analizza le ultime 100 righe per errori recenti
            for line in lines[-100:]:
                if "[ERROR]" in line or "Error:" in line or "Exception" in line:
                    recent_errors += 1
            
            for line in lines:
                if "[ERROR]" in line or "Error:" in line or "Exception" in line:
                    for pattern, description in error_patterns:
                        if pattern in line:
                            if pattern not in errors_found:
                                errors_found[pattern] = {"count": 0, "description": description, "examples": []}
                            
                            errors_found[pattern]["count"] += 1
                            if len(errors_found[pattern]["examples"]) < 3:  # Limita a 3 esempi
                                errors_found[pattern]["examples"].append(line.strip())
    except Exception as e:
        logging.error(f"Errore nell'analisi del log: {e}")
        return False
    
    # Mostra risultati
    if errors_found:
        logging.info(f"File di log analizzato ({line_count} linee). Trovati errori:")
        for pattern, data in errors_found.items():
            logging.info(f"\n⚠️ {data['description']} ({data['count']} occorrenze):")
            for example in data['examples']:
                logging.info(f"  → {example}")
                
        if recent_errors > 0:
            logging.warning(f"⚠️ {recent_errors} errori trovati nelle ultime 100 righe del log (potrebbero essere recenti)")
        else:
            logging.info("✅ Nessun errore recente nelle ultime 100 righe del log")
    else:
        logging.info(f"File di log analizzato ({line_count} linee). Nessun errore noto trovato.")
    
    return True