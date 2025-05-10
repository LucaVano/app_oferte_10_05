#!/bin/bash
# Script di installazione migliorato per l'app di gestione offerte su Synology NAS

echo "=== Installazione app offerte su Synology NAS ==="
echo "Questo script installerà l'app e configurerà le dipendenze"

# Verifica se siamo su Synology
if [ ! -f "/etc/synology-release" ] && [ ! -d "/usr/syno/synoman/webman" ]; then
    echo "ERRORE: Questo script deve essere eseguito su un NAS Synology"
    exit 1
fi

# Verifica se Python è installato
if ! command -v python3 &> /dev/null; then
    echo "ERRORE: Python 3 non trovato. Installalo dal Package Center di Synology"
    exit 1
fi

# Percorso base dell'app
APP_NAME="app_offerte"
WEB_FOLDER="/volume1/web"
APP_FOLDER="$WEB_FOLDER/$APP_NAME"

# Crea i percorsi necessari
echo "Creazione cartelle..."
mkdir -p "$APP_FOLDER/data"
mkdir -p "$APP_FOLDER/static/uploads"
mkdir -p "$APP_FOLDER/logs"

# Crea un ambiente virtuale Python
echo "Creazione ambiente virtuale Python..."
python3 -m venv "$APP_FOLDER/venv"
source "$APP_FOLDER/venv/bin/activate"

# Installa le dipendenze Python con output dettagliato
echo "Installazione dipendenze Python..."
python3 -m pip install --upgrade pip
echo "Installazione dipendenze da requirements-synology.txt..."
python3 -m pip install -r "$APP_FOLDER/requirements-synology.txt" | tee "$APP_FOLDER/logs/pip_install.log"

# Verifica l'installazione delle dipendenze
echo "Verifica installazione dipendenze..."
{
    echo "Flask: $(python3 -c 'import flask; print(flask.__version__)' 2>&1)"
    echo "Werkzeug: $(python3 -c 'import werkzeug; print(werkzeug.__version__)' 2>&1)"
    echo "Jinja2: $(python3 -c 'import jinja2; print(jinja2.__version__)' 2>&1)"
    echo "Reportlab: $(python3 -c 'import reportlab; print(reportlab.Version)' 2>&1)"
    echo "PIL: $(python3 -c 'import PIL; print(PIL.__version__)' 2>&1)"
    echo "Dateutil: $(python3 -c 'import dateutil; print(dateutil.__version__)' 2>&1)"
    echo "Waitress: $(python3 -c 'import waitress; print(waitress.__version__)' 2>&1)"
    echo "python-dotenv: $(python3 -c 'import dotenv; print(dotenv.__version__)' 2>&1)"
} | tee "$APP_FOLDER/logs/dependencies.log"

# Esci dall'ambiente virtuale
deactivate

# Setta variabili d'ambiente
echo "Configurazione variabili d'ambiente..."
cat > "$APP_FOLDER/.env" << EOF
FLASK_ENV=production
FLASK_CONFIG=synology
PORT=5002
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(16))")
EOF

# Crea lo script di avvio
echo "Creazione script di avvio..."
cat > "$APP_FOLDER/start.sh" << EOF
#!/bin/bash
cd "$APP_FOLDER"
source venv/bin/activate
export FLASK_ENV=production
export FLASK_CONFIG=synology
export PORT=5002
python3 wsgi.py >> logs/app.log 2>&1
EOF

chmod +x "$APP_FOLDER/start.sh"

# Imposta i permessi corretti
echo "Impostazione permessi..."
chmod -R 755 "$APP_FOLDER"
chown -R http:http "$APP_FOLDER"

# Crea un servizio SystemD (se disponibile)
if command -v systemctl &> /dev/null; then
    echo "Configurazione servizio systemd..."
    cat > /etc/systemd/system/app-offerte.service << EOF
[Unit]
Description=App Offerte Valtservice
After=network.target

[Service]
User=http
Group=http
WorkingDirectory=$APP_FOLDER
ExecStart=/bin/bash $APP_FOLDER/start.sh
Restart=always
Environment="PATH=$APP_FOLDER/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=$APP_FOLDER"

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable app-offerte.service
    systemctl start app-offerte.service
    
    echo "Servizio systemd configurato e avviato"
    echo "Verifica stato del servizio:"
    systemctl status app-offerte.service
else
    echo "systemd non disponibile, script di avvio manuale è in $APP_FOLDER/start.sh"
    echo "Puoi avviare l'app con: cd $APP_FOLDER && ./start.sh"
fi

echo ""
echo "=== Installazione completata ==="
echo "L'app dovrebbe essere disponibile all'indirizzo: http://[ip-nas]:5002"
echo "Log di installazione salvati in $APP_FOLDER/logs/"
echo "Se l'app non è accessibile, controlla i log in $APP_FOLDER/logs/app.log"
echo ""