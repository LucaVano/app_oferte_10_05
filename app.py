from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
import os
import json
import uuid
import shutil
import re
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
from utils.pdf_generator import generate_pdf
from utils.pdf_preview import generate_pdf_preview
from auth import init_auth, login_required
from utils.format_utils import format_price

app = Flask(__name__)
app.secret_key = 'valtservice_secret_key'  # Assicurati sia una stringa sicura in produzione
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
app.config['DATA_FOLDER'] = os.path.join(app.root_path, 'data')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

# Inizializza l'autenticazione
app = init_auth(app)

# Inizializzazione delle cartelle necessarie
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['DATA_FOLDER'], exist_ok=True)

def allowed_file(filename):
    """Controlla se l'estensione del file è consentita"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.context_processor
def inject_now():
    """Inietta la data attuale nei template"""
    return {'now': datetime.now()}

@app.context_processor
def utility_processor():
    return dict(format_price=format_price)

def get_next_offer_number():
    """Genera il prossimo numero di offerta nel formato YYYY-XXXX"""
    counter_file = os.path.join(app.config['DATA_FOLDER'], "counter.json")
    
    # Inizializza il contatore se non esiste
    if not os.path.exists(counter_file):
        current_year = str(datetime.now().year)
        counter = {current_year: 0}
        with open(counter_file, 'w') as f:
            json.dump(counter, f)
    
    # Carica il contatore
    with open(counter_file, 'r') as f:
        counter = json.load(f)
    
    current_year = str(datetime.now().year)
    if current_year not in counter:
        counter[current_year] = 0
    
    counter[current_year] += 1
    
    # Salva il contatore aggiornato
    with open(counter_file, 'w') as f:
        json.dump(counter, f)
    
    return f"{current_year}-{counter[current_year]:04d}"

def update_offerte_index(data, data_folder):
    """Aggiorna il file di indice delle offerte"""
    try:
        index_file = os.path.join(data_folder, "offerte_index.json")
        
        # Carica l'indice esistente
        if os.path.exists(index_file):
            with open(index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
        else:
            index = []
        
        # Verifica se l'offerta è già presente nell'indice
        for i, entry in enumerate(index):
            if entry.get('id') == data['id']:
                # Aggiorna la voce esistente
                index[i] = {
                    'id': data['id'],
                    'offer_number': data['offer_number'],
                    'date': data['date'],
                    'customer': data['customer'],
                    'customer_email': data['customer_email'],
                    'description': data['offer_description'][:100] + '...' if len(data['offer_description']) > 100 else data['offer_description']
                }
                break
        else:
            # Aggiungi una nuova voce
            index.append({
                'id': data['id'],
                'offer_number': data['offer_number'],
                'date': data['date'],
                'customer': data['customer'],
                'customer_email': data['customer_email'],
                'description': data['offer_description'][:100] + '...' if len(data['offer_description']) > 100 else data['offer_description']
            })
        
        # Salva l'indice aggiornato
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=4, ensure_ascii=False)
        
    except Exception as e:
        logging.info(f"ERRORE nell'aggiornamento dell'indice: {e}")

def get_offerta_direct(offerta_id, data_folder):
    """Ottiene direttamente un'offerta dal file JSON usando l'ID"""
    try:
        # Carica l'indice
        index_file = os.path.join(data_folder, "offerte_index.json")
        if not os.path.exists(index_file):
            logging.info(f"ERRORE: File indice non trovato: {index_file}")
            return None
            
        with open(index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)
            
        # Trova l'offerta nell'indice
        for entry in index:
            if entry.get('id') == offerta_id:
                # Costruisci il percorso del file JSON
                customer_folder = os.path.join(data_folder, entry['customer'].upper())
                offer_folder = os.path.join(customer_folder, entry['offer_number'])
                json_path = os.path.join(offer_folder, "dati_offerta.json")
                
                if not os.path.exists(json_path):
                    logging.info(f"ERRORE: File JSON non trovato: {json_path}")
                    return None
                    
                # Carica i dati completi
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Assicurati che tabs esista
                if 'tabs' not in data or not isinstance(data['tabs'], list):
                    data['tabs'] = []
                    
                return data
                
        logging.info(f"ERRORE: Offerta con ID {offerta_id} non trovata nell'indice")
        return None
        
    except Exception as e:
        logging.info(f"ERRORE in get_offerta_direct: {e}")
        return None

def get_all_offerte():
    """Restituisce tutte le offerte dalla repository data"""
    offers = []  # Inizializza offers come lista vuota
    data_folder = app.config['DATA_FOLDER']
    
    try:
        # Scansiona tutte le cartelle dei clienti
        for customer_folder in os.listdir(data_folder):
            # Salta i file e considera solo le directory
            customer_path = os.path.join(data_folder, customer_folder)
            if not os.path.isdir(customer_path) or customer_folder in ["__pycache__"]:
                continue
                
            # Scansiona tutte le cartelle delle offerte
            for offer_folder in os.listdir(customer_path):
                offer_path = os.path.join(customer_path, offer_folder)
                if os.path.isdir(offer_path):
                    json_path = os.path.join(offer_path, "dati_offerta.json")
                    if os.path.exists(json_path):
                        try:
                            with open(json_path, 'r', encoding='utf-8') as f:
                                offer_data = json.load(f)
                                # Migra gli stati vecchi al nuovo formato
                                if 'status' not in offer_data:
                                    offer_data['status'] = 'in_attesa'
                                elif offer_data['status'] == 'pending':
                                    offer_data['status'] = 'in_attesa'
                                elif offer_data['status'] == 'accepted':
                                    offer_data['status'] = 'accettata'
                                offers.append(offer_data)
                        except Exception as e:
                            logging.info(f"Errore nel caricamento dell'offerta {offer_folder}: {str(e)}")
                            continue
        
        # Ordina le offerte per numero d'offerta (più recenti prima)
        # Solo se la lista non è vuota
        if offers:
            def sort_key(offer):
                offer_number = offer.get('offer_number', '')
                try:
                    if '-' in offer_number:
                        year, number = offer_number.split('-')
                        return (year, int(number))
                    return offer_number
                except:
                    return offer_number

            offers.sort(key=sort_key, reverse=True)
        
        return offers
    except Exception as e:
        logging.info(f"Errore nel caricamento delle offerte: {str(e)}")
        return []  # Restituisci una lista vuota invece di None

def process_form_final(form, files):
    """
    Versione semplificata e robusta della funzione di processo dei form
    """
    import logging
    import re
    
    logging.info("Elaborazione form ricevuto")
    
    tabs = []
    
    # Utilizza un pattern regex per trovare gli indici nelle chiavi
    tab_indices = set()
    product_indices = dict()  # Memorizza gli indici dei prodotti per ogni tab
    
    # Cerca gli indici numerici nei nomi dei campi
    for key in form:
        # Cerca pattern come tab_0type_
        match = re.search(r'tab_(\d+)type_', key)
        if match:
            try:
                idx = int(match.group(1))
                tab_indices.add(idx)
                logging.info(f"Trovato tab_{idx}type_ : {form[key]}")
            except ValueError:
                logging.warning(f"Indice non valido in {key}: {match.group(1)}")
            continue
            
        # Cerca pattern come tab_type_0
        match = re.search(r'tab_type_(\d+)', key)
        if match:
            try:
                idx = int(match.group(1))
                tab_indices.add(idx)
                logging.info(f"Trovato tab_type_{idx} : {form[key]}")
            except ValueError:
                logging.warning(f"Indice non valido in {key}: {match.group(1)}")
            continue
        
        # Cerca pattern per gli indici dei prodotti nelle schede multiprodotto
        match = re.search(r'product_(\d+)(name|model|price|quantity|description)__(\d+)', key)
        if match:
            try:
                tab_idx = int(match.group(1))
                prod_idx = int(match.group(3))
                
                if tab_idx not in product_indices:
                    product_indices[tab_idx] = set()
                
                product_indices[tab_idx].add(prod_idx)
            except ValueError:
                logging.warning(f"Indice non valido in {key}")
    
    # Se non abbiamo trovato indici di tab validi ma abbiamo un tab_type_ senza indice,
    # aggiungiamo un indice predefinito 0
    if not tab_indices and 'tab_type_' in form:
        tab_indices.add(0)
        logging.info("Nessun indice valido trovato, ma rilevato tab_type_. Aggiunto indice predefinito 0.")
    
    # Debug degli indici trovati
    logging.info(f"Indici tab trovati: {sorted(tab_indices)}")
    logging.info(f"Indici prodotti trovati: {product_indices}")

    # Crea le schede
    for idx in sorted(tab_indices):
        logging.info(f"Elaborazione tab {idx}")
        
        # Determina il tipo di scheda
        tab_type = None
        if f'tab_{idx}type_' in form:
            tab_type = form[f'tab_{idx}type_']
        elif f'tab_type_{idx}' in form:
            tab_type = form[f'tab_type_{idx}']
        elif 'tab_type_' in form and idx == 0:  # Caso speciale per tab_type_ senza indice
            tab_type = form['tab_type_']
        
        logging.info(f"Tipo tab {idx}: {tab_type}")
        
        if not tab_type:
            logging.info(f"Tipo non trovato per tab {idx}, salto...")
            continue
        
        # Elabora in base al tipo
        if tab_type == 'single_product':
            # GESTIONE PRODOTTO SINGOLO
            
            # Cerca i campi con entrambi i formati possibili
            product_name = get_form_value(form, [f'product_{idx}name_', f'product_name_{idx}', 'product_name_'])
            product_code = get_form_value(form, [f'product_{idx}code_', f'product_code_{idx}', 'product_code_'])
            unit_price = get_form_value(form, [f'unit_{idx}price_', f'unit_price_{idx}', 'unit_price_'], '0')
            quantity = get_form_value(form, [f'quantity_{idx}', 'quantity_'], '1')
            description = get_form_value(form, [f'description_{idx}', 'description_'])
            discount = get_form_value(form, [f'discount_{idx}', 'discount_'], '0')
            power_w = get_form_value(form, [f'power_{idx}w_', f'power_w_{idx}', 'power_w_'])
            volts = get_form_value(form, [f'volts_{idx}', 'volts_'])
            size = get_form_value(form, [f'size_{idx}', 'size_'])
            posizione = get_form_value(form, [f'posizione_{idx}', 'posizione_'])
            
            # Checkbox dello sconto - necessita di un trattamento speciale
            discount_flag_keys = [f'discount_{idx}flag_', f'discount_flag_{idx}', 'discount_flag_']
            discount_flag = any(key in form and form[key] == 'on' for key in discount_flag_keys)
            
            # Gestione caricamento immagine
            image_path = ''
            # Cerca il campo existing_image con pattern specifico per questo tab
            existing_image_keys = [f'existing_image_{idx}', 'existing_image_']
            for key in existing_image_keys:
                if key in form:
                    image_path = form[key]
                    logging.info(f"Trovato campo {key} = {image_path}")
                    break

            # Cerca il campo product_image con pattern specifico per questo tab nei files
            product_image_key = None
            product_image_keys = [f'product_{idx}image_', f'product_image_{idx}', 'product_image_']
            for key in product_image_keys:
                if key in files and files[key] and files[key].filename:
                    product_image_key = key
                    logging.info(f"Trovato campo immagine {key} per tab {idx}")
                    break

            if product_image_key and files[product_image_key] and files[product_image_key].filename and allowed_file(files[product_image_key].filename):
                product_image = files[product_image_key]
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{product_image.filename}")
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                product_image.save(file_path)
                image_path = '/static/uploads/' + filename
                logging.info(f"Salvata nuova immagine in {image_path} per tab {idx}")

            logging.info(f"Valore finale di image_path per tab {idx}: {image_path}")
            
            # Crea la scheda prodotto singolo
            if product_name:  # Rimuovi il controllo su product_code per permettere l'inserimento senza modello
                single_product_tab = {
                    'type': 'single_product',
                    'product_code': product_code, # Può essere vuoto
                    'product_name': product_name,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'description': description,
                    'discount': discount,
                    'discount_flag': discount_flag,
                    'power_w': power_w,
                    'volts': volts,
                    'size': size,
                    'posizione': posizione,
                    'product_image_path': image_path
                }
                
                logging.info(f"Aggiunto prodotto singolo: {product_name}")
                tabs.append(single_product_tab)
            else:
                logging.warning(f"Saltato prodotto singolo per tab {idx} - nome prodotto mancante")
        
        elif tab_type == 'multi_product':
            products = []
            # Cerca tutti i prodotti per questa scheda
            max_rows = 3  # Default è 3 righe
            
            # Cerca possibili indici di prodotti per questa scheda
            prod_indices = set(range(max_rows))  # Default: 0, 1, 2
            if idx in product_indices:
                prod_indices.update(product_indices[idx])
                
            for i in sorted(prod_indices):
                name = get_form_value(form, [f'product_{idx}name__{i}', f'product_name__{i}'])
                if name and name.strip():  # Solo se il nome è compilato
                    model = get_form_value(form, [f'product_{idx}model__{i}', f'product_model__{i}'])
                    price = get_form_value(form, [f'product_{idx}price__{i}', f'product_price__{i}'], '0')
                    quantity = get_form_value(form, [f'product_{idx}quantity__{i}', f'product_quantity__{i}'], '1')
                    description = get_form_value(form, [
                        f'product_{idx}description__{i}', 
                        f'product_description__{i}',
                        f'description_{idx}_{i}'
                    ], '')  # Add more possible key patterns
                    
                    # Ensure description is included in the product data
                    products.append([
                        name.strip(),
                        model.strip(),
                        price,
                        quantity,
                        description.strip()
                    ])
            
            multi_product_tab = {
                'type': 'multi_product',
                'products': products,
                'max_items_per_page': 3
            }
            
            logging.info(f"Aggiunta scheda multiprodotto con {len(products)} prodotti")
            tabs.append(multi_product_tab)
    
    # Se non abbiamo trovato nessuna scheda, proviamo un approccio diverso
    if not tabs:
        logging.warning("Nessuna scheda trovata con i metodi standard, tentativo di recupero diretto")
        
        # Cerca tutti i possibili campi prodotto nel form
        product_fields = {}
        
        for key in form:
            # Crea un dizionario di tutti i campi che sembrano essere prodotti
            if key.startswith('product_') and '_name_' in key:
                idx = key.split('_name_')[1]
                if idx not in product_fields:
                    product_fields[idx] = {'type': 'single_product'}
                product_fields[idx]['product_name'] = form[key]
            
            elif key.startswith('product_') and 'name_' in key:
                parts = key.split('name_')
                if len(parts) == 2:
                    idx = parts[0].replace('product_', '')
                    if idx not in product_fields:
                        product_fields[idx] = {'type': 'single_product'}
                    product_fields[idx]['product_name'] = form[key]
        
        # Crea schede per ogni prodotto trovato
        for idx, fields in product_fields.items():
            if 'product_name' in fields and fields['product_name'].strip():
                # Questo è un prodotto singolo valido, trova gli altri campi
                prefix = f'product_{idx}'
                
                # Cerca gli altri campi di questo prodotto
                for key in form:
                    if key.startswith(prefix):
                        field_name = key.replace(prefix, '')
                        if field_name.startswith('_code_'):
                            fields['product_code'] = form[key]
                        elif field_name.startswith('_price_'):
                            fields['unit_price'] = form[key]
                        # Aggiungi altri campi...
                
                # Se abbiamo i campi essenziali, crea la scheda
                if 'product_code' in fields:
                    single_product_tab = {
                        'type': 'single_product',
                        'product_code': fields.get('product_code', ''),
                        'product_name': fields.get('product_name', ''),
                        'quantity': fields.get('quantity', '1'),
                        'unit_price': fields.get('unit_price', '0'),
                        'description': fields.get('description', ''),
                        'discount': '0',
                        'discount_flag': False,
                        'power_w': '',
                        'volts': '',
                        'size': '',
                        'posizione': '',
                        'product_image_path': ''
                    }
                    
                    logging.info(f"Aggiunto prodotto singolo con recupero diretto: {fields.get('product_name')}")
                    tabs.append(single_product_tab)
    
    logging.info(f"Processo completato. Totale schede elaborate: {len(tabs)}")
    return tabs

def get_form_value(form, possible_keys, default=''):
    """
    Cerca un valore nel form provando diverse possibili chiavi
    
    Args:
        form: Il form da cui ottenere i valori
        possible_keys: Lista di possibili chiavi da provare
        default: Valore predefinito se nessuna chiave viene trovata
        
    Returns:
        Il valore trovato o il default
    """
    for key in possible_keys:
        if key in form:
            return form[key]
    return default

@app.route('/')
@login_required
def index():
    try:
        # Carica tutte le offerte dalla repository
        offers = get_all_offerte()
        
        # Assicurati che offers non sia None
        if offers is None:
            offers = []
        
        # Dividi le offerte per stato
        pending_offers = [offer for offer in offers if offer.get('status', 'in_attesa') == 'in_attesa']
        accepted_offers = [offer for offer in offers if offer.get('status', 'in_attesa') == 'accettata']
        
        return render_template('index.html', 
                            all_offers=offers,
                            pending_offers=pending_offers,
                            accepted_offers=accepted_offers)
    except Exception as e:
        flash(f'Errore durante il caricamento delle offerte: {str(e)}', 'error')
        return render_template('index.html', 
                            all_offers=[],
                            pending_offers=[],
                            accepted_offers=[])

@app.route('/nuova-offerta', methods=['GET', 'POST'])
@login_required
def nuova_offerta():
    try:
        if request.method == 'GET':
            # Genera un nuovo numero di offerta per il form
            next_number = get_next_offer_number()
            today_date = datetime.now().strftime('%Y-%m-%d')
            return render_template('nuova_offerta.html', next_number=next_number, today_date=today_date)
        
        elif request.method == 'POST':
            logging.info("DEBUG - Ricevuto POST per nuova offerta")
            
            # Crea un dizionario per la nuova offerta
            data = {
                'date': request.form.get('date'),
                'customer': request.form.get('customer'),
                'customer_email': request.form.get('customer_email'),
                'address': request.form.get('address'),
                'offer_description': request.form.get('offer_description'),
                'offer_number': request.form.get('offer_number'),
                'id': str(uuid.uuid4()),
                'tabs': process_form_final(request.form, request.files),
                'status': 'in_attesa'  # Impostiamo lo stato iniziale come 'in_attesa'
            }
            
            logging.info(f"DEBUG - Dati offerta preparati - {len(data['tabs'])} tabs")
            
            # Salva direttamente i dati in un file JSON
            customer_folder = os.path.join(app.config['DATA_FOLDER'], data['customer'].upper())
            offer_folder = os.path.join(customer_folder, data['offer_number'])
            os.makedirs(offer_folder, exist_ok=True)
            
            json_path = os.path.join(offer_folder, "dati_offerta.json")
            
            logging.info(f"DEBUG - Salvataggio JSON in: {json_path}")
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            logging.info(f"DEBUG - JSON salvato con successo")
            
            # Aggiorna indice offerte
            update_offerte_index(data, app.config['DATA_FOLDER'])
            
            # Genera il PDF
            pdf_path = generate_pdf(data, app.root_path)
            
            # Aggiorna il percorso del PDF
            data['pdf_path'] = os.path.basename(pdf_path)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            flash('Offerta creata con successo!', 'success alert-permanent')
            return redirect(url_for('view_offerta', offerta_id=data['id']))
        
        return redirect(url_for('index'))
    
    except Exception as e:
        import traceback
        logging.info(f"ERRORE in nuova_offerta: {e}")
        logging.info(traceback.format_exc())
        flash(f'Si è verificato un errore: {str(e)}', 'danger alert-permanent')
        return redirect(url_for('index'))

@app.route('/offerta/<offerta_id>/json')
@login_required
def debug_offerta_json(offerta_id):
    """Endpoint di debug che mostra il JSON dell'offerta"""
    try:
        offerta = get_offerta_direct(offerta_id, app.config['DATA_FOLDER'])
        if not offerta:
            return jsonify({"error": "Offerta non trovata"}), 404
        return jsonify(offerta)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/offerta/<offerta_id>')
@login_required
def view_offerta(offerta_id):
    try:
        # Ottieni l'offerta direttamente dal file JSON
        offerta_data = get_offerta_direct(offerta_id, app.config['DATA_FOLDER'])
        
        if not offerta_data:
            flash('Offerta non trovata', 'danger')
            return redirect(url_for('index'))
        
        logging.info(f"DEBUG view_offerta: ID={offerta_id}, tabs={len(offerta_data.get('tabs', []))}")
        
        return render_template('vista_offerta.html', offerta=offerta_data)
    except Exception as e:
        import traceback
        logging.info(f"Errore in view_offerta: {e}")
        logging.info(traceback.format_exc())
        flash(f'Errore nel caricamento dell\'offerta: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/offerta/<offerta_id>/modifica', methods=['GET', 'POST'])
@login_required
def edit_offerta(offerta_id):
    try:
        if request.method == 'GET':
            # Ottieni l'offerta direttamente dal file JSON
            offerta = get_offerta_direct(offerta_id, app.config['DATA_FOLDER'])
            if not offerta:
                flash('Offerta non trovata', 'danger')
                return redirect(url_for('index'))
                
            return render_template('nuova_offerta.html', offerta=offerta, is_edit=True, today_date=datetime.now().strftime('%Y-%m-%d'))
            
        elif request.method == 'POST':
            logging.info(f"DEBUG - Ricevuto POST per modifica offerta {offerta_id}")
            
            # Stesso approccio di nuova_offerta, ma manteniamo l'ID originale
            # Ottieni prima i dati dell'offerta esistente
            original_offerta = get_offerta_direct(offerta_id, app.config['DATA_FOLDER'])
            if not original_offerta:
                flash('Offerta non trovata', 'danger')
                return redirect(url_for('index'))
            
            # Aggiorna i dati dell'offerta
            data = {
                'date': request.form.get('date'),
                'customer': request.form.get('customer'),
                'customer_email': request.form.get('customer_email'),
                'address': request.form.get('address'),
                'offer_description': request.form.get('offer_description'),
                'offer_number': request.form.get('offer_number'),
                'id': offerta_id,  # Mantieni l'ID originale
                'tabs': process_form_final(request.form, request.files)
            }
            
            logging.info(f"DEBUG - Dati offerta preparati per modifica - {len(data['tabs'])} tabs")
            
            # Mantieni il percorso PDF esistente
            if original_offerta and 'pdf_path' in original_offerta:
                data['pdf_path'] = original_offerta['pdf_path']
            
            # Gestisci il caso in cui il cliente o il numero offerta sono cambiati
            old_customer = original_offerta.get('customer', '').upper()
            old_offer_number = original_offerta.get('offer_number', '')
            
            new_customer = data['customer'].upper()
            new_offer_number = data['offer_number']
            
            old_folder = os.path.join(app.config['DATA_FOLDER'], old_customer, old_offer_number)
            new_folder = os.path.join(app.config['DATA_FOLDER'], new_customer, new_offer_number)
            
            # Crea nuova cartella se necessario
            os.makedirs(os.path.dirname(new_folder), exist_ok=True)
            os.makedirs(new_folder, exist_ok=True)
            
            # Salva i dati aggiornati
            json_path = os.path.join(new_folder, "dati_offerta.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            # Se la posizione è cambiata, copia i file necessari
            if old_folder != new_folder and os.path.exists(old_folder):
                for filename in os.listdir(old_folder):
                    if filename != "dati_offerta.json":  # File JSON già riscritto
                        src_path = os.path.join(old_folder, filename)
                        dst_path = os.path.join(new_folder, filename)
                        shutil.copy2(src_path, dst_path)
                
                # Prova a rimuovere le vecchie cartelle
                try:
                    shutil.rmtree(old_folder)
                    # Se la cartella cliente è vuota, rimuovi anche quella
                    old_customer_folder = os.path.join(app.config['DATA_FOLDER'], old_customer)
                    if os.path.exists(old_customer_folder) and not os.listdir(old_customer_folder):
                        shutil.rmtree(old_customer_folder)
                except:
                    pass  # Ignora errori nella pulizia
            
            # Aggiorna l'indice
            update_offerte_index(data, app.config['DATA_FOLDER'])
            
            # Rigenera il PDF
            pdf_path = generate_pdf(data, app.root_path)
            data['pdf_path'] = os.path.basename(pdf_path)
            
            # Salva di nuovo con il percorso PDF aggiornato
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            flash('Offerta aggiornata con successo!', 'success')
            return redirect(url_for('view_offerta', offerta_id=offerta_id))
            
    except Exception as e:
        import traceback
        logging.info(f"ERRORE in edit_offerta: {e}")
        logging.info(traceback.format_exc())
        flash(f'Si è verificato un errore: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/offerta/<offerta_id>/pdf')
@login_required
def download_pdf(offerta_id):
    try:
        offerta = get_offerta_direct(offerta_id, app.config['DATA_FOLDER'])
        if not offerta or not offerta.get('pdf_path'):
            flash('PDF non trovato', 'danger')
            return redirect(url_for('view_offerta', offerta_id=offerta_id))
        
        pdf_path = os.path.join(app.config['DATA_FOLDER'], offerta['customer'].upper(), 
                               offerta['offer_number'], offerta['pdf_path'])
        
        return send_file(pdf_path, as_attachment=True)
    except Exception as e:
        flash(f'Errore nel download del PDF: {str(e)}', 'danger')
        return redirect(url_for('view_offerta', offerta_id=offerta_id))

@app.route('/offerta/<offerta_id>/elimina', methods=['POST'])
@login_required
def delete_offerta(offerta_id):
    try:
        logging.info(f"Ricevuta richiesta di eliminazione per offerta {offerta_id}")
        offerta = get_offerta_direct(offerta_id, app.config['DATA_FOLDER'])
        if not offerta:
            logging.info(f"Offerta non trovata: {offerta_id}")
            flash('Offerta non trovata', 'danger')
            return redirect(url_for('index'))
        
        # Rimuovi dall'indice
        index_file = os.path.join(app.config['DATA_FOLDER'], "offerte_index.json")
        if os.path.exists(index_file):
            with open(index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
            
            index = [entry for entry in index if entry.get('id') != offerta_id]
            
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index, f, indent=4, ensure_ascii=False)
        
        # Rimuovi i file
        customer_folder = os.path.join(app.config['DATA_FOLDER'], offerta['customer'].upper())
        offer_folder = os.path.join(customer_folder, offerta['offer_number'])
        
        if os.path.exists(offer_folder):
            shutil.rmtree(offer_folder)
            logging.info(f"Cartella offerta eliminata: {offer_folder}")
        
        # Se la cartella cliente è vuota, rimuovi anche quella
        if os.path.exists(customer_folder) and not os.listdir(customer_folder):
            shutil.rmtree(customer_folder)
            logging.info(f"Cartella cliente eliminata: {customer_folder}")
        
        logging.info(f"Offerta eliminata con successo: {offerta_id}")
        flash('Offerta eliminata con successo', 'success')
        return jsonify({'success': True})
    except Exception as e:
        logging.info(f"ERRORE nell'eliminazione dell'offerta: {e}")
        flash(f'Errore durante l\'eliminazione dell\'offerta: {str(e)}', 'danger')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/next-offer-number', methods=['GET'])
@login_required
def api_next_offer_number():
    next_number = get_next_offer_number()
    return jsonify({'next_number': next_number})

@app.route('/update_offer_status/<offer_id>', methods=['POST'])
@login_required
def update_offer_status(offer_id):
    try:
        logging.info(f"Ricevuta richiesta di aggiornamento stato per offerta {offer_id}")
        new_status = request.form.get('status')
        logging.info(f"Nuovo stato richiesto: {new_status}")
        
        if new_status not in ['in_attesa', 'accettata']:
            logging.info(f"Stato non valido: {new_status}")
            return jsonify({'success': False, 'error': 'Stato non valido'}), 400
            
        # Ottieni l'offerta direttamente dal file JSON
        offerta_data = get_offerta_direct(offer_id, app.config['DATA_FOLDER'])
        
        if not offerta_data:
            logging.info(f"Offerta non trovata: {offer_id}")
            return jsonify({'success': False, 'error': 'Offerta non trovata'}), 404
        
        logging.info(f"Stato attuale: {offerta_data.get('status')}, Nuovo stato: {new_status}")
        
        # Aggiorna lo stato
        offerta_data['status'] = new_status
        
        # Salva i dati aggiornati
        customer_folder = os.path.join(app.config['DATA_FOLDER'], offerta_data['customer'].upper())
        offer_folder = os.path.join(customer_folder, offerta_data['offer_number'])
        os.makedirs(offer_folder, exist_ok=True)
        
        json_path = os.path.join(offer_folder, "dati_offerta.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(offerta_data, f, indent=4, ensure_ascii=False)
        
        # Aggiorna l'indice
        update_offerte_index(offerta_data, app.config['DATA_FOLDER'])
        
        logging.info(f"Stato aggiornato con successo per offerta {offer_id}")
        return jsonify({'success': True})
    except Exception as e:
        logging.info(f"Errore durante l'aggiornamento dello stato: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/offerta/<offerta_id>/salva', methods=['POST'])
@login_required
def save_offerta(offerta_id):
    try:
        # Ottieni l'offerta direttamente dal file JSON
        offerta_data = get_offerta_direct(offerta_id, app.config['DATA_FOLDER'])
        
        if not offerta_data:
            return jsonify({'success': False, 'error': 'Offerta non trovata'}), 404
        
        # Assicurati che l'offerta abbia uno stato
        if 'status' not in offerta_data:
            offerta_data['status'] = 'pending'
        
        # Aggiorna l'indice delle offerte
        update_offerte_index(offerta_data, app.config['DATA_FOLDER'])
        
        # Salva i dati aggiornati
        customer_folder = os.path.join(app.config['DATA_FOLDER'], offerta_data['customer'].upper())
        offer_folder = os.path.join(customer_folder, offerta_data['offer_number'])
        os.makedirs(offer_folder, exist_ok=True)
        
        json_path = os.path.join(offer_folder, "dati_offerta.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(offerta_data, f, indent=4, ensure_ascii=False)
        
        return jsonify({'success': True})
    except Exception as e:
        logging.info(f"Errore durante il salvataggio dell'offerta: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/offerte-in-attesa')
@login_required
def offerte_in_attesa():
    offers = get_all_offerte()
    pending_offers = [offer for offer in offers if offer.get('status') == 'in_attesa']
    return render_template('filtered_offers.html', 
                         title='Offerte in Attesa',
                         icon='fa-clock',
                         offers=pending_offers)

@app.route('/offerte-accettate')
@login_required
def offerte_accettate():
    offers = get_all_offerte()
    accepted_offers = [offer for offer in offers if offer.get('status') == 'accettata']
    return render_template('filtered_offers.html',
                         title='Offerte Accettate',
                         icon='fa-check-circle',
                         offers=accepted_offers)

@app.route('/preview_pdf', methods=['POST'])
@login_required
def preview_pdf():
    """Generates a temporary PDF preview based on current form data"""
    try:
        # Create a temporary folder for previews if it doesn't exist
        preview_folder = os.path.join(app.config['DATA_FOLDER'], '_previews')
        os.makedirs(preview_folder, exist_ok=True)
        
        # Clean up old preview files (older than 1 hour)
        current_time = datetime.now().timestamp()
        for filename in os.listdir(preview_folder):
            file_path = os.path.join(preview_folder, filename)
            if os.path.isfile(file_path) and (current_time - os.path.getmtime(file_path)) > 3600:
                os.remove(file_path)
        
        # Process form data like in the regular form submission
        form_data = request.form.to_dict()
        files_data = request.files.to_dict()
        
        # Create temporary data for PDF generation
        temp_data = {
            'date': form_data.get('date', datetime.now().strftime('%Y-%m-%d')),
            'customer': form_data.get('customer', 'Cliente Temporaneo'),
            'customer_email': form_data.get('customer_email', 'email@esempio.com'),
            'address': form_data.get('address', 'Indirizzo Temporaneo'),
            'offer_description': form_data.get('offer_description', 'Descrizione Temporanea'),
            'offer_number': form_data.get('offer_number', 'TEMP-0001'),
            'id': 'preview-' + str(uuid.uuid4()),
            'tabs': process_form_final(form_data, files_data),
            'status': 'pending'
        }
        
        # Generate a unique filename for this preview
        preview_filename = f"preview_{uuid.uuid4()}.pdf"
        preview_path = os.path.join(preview_folder, preview_filename)
        
        # Generate the PDF directly to the preview location
        from utils.pdf_generator import generate_pdf_preview
        generate_pdf_preview(temp_data, app.root_path, preview_path)
        
        # Return the URL to the preview PDF
        return jsonify({
            'success': True,
            'preview_url': url_for('serve_preview', filename=preview_filename)
        })
        
    except Exception as e:
        import traceback
        logging.info(f"Error generating PDF preview: {e}")
        logging.info(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/preview/<filename>')
@login_required
def serve_preview(filename):
    """Serves a preview PDF file"""
    preview_folder = os.path.join(app.config['DATA_FOLDER'], '_previews')
    return send_file(os.path.join(preview_folder, filename))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)