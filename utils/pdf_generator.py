import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
import datetime
from utils.format_utils import format_price

def generate_pdf(offerta, app_root):
    """Genera il PDF con i dati delle schede."""
    # Assicuriamoci che tabs esista
    if 'tabs' not in offerta or not isinstance(offerta['tabs'], list):
        offerta['tabs'] = []
    
    # Inizializza il prezzo totale dell'offerta
    total_offer_price = 0
    
    # Percorsi delle risorse
    static_folder = os.path.join(app_root, 'static')
    data_folder = os.path.join(app_root, 'data')
    
    # Crea le cartelle necessarie
    customer_folder = os.path.join(data_folder, offerta['customer'].upper())
    offer_folder = os.path.join(customer_folder, offerta['offer_number'])
    os.makedirs(offer_folder, exist_ok=True)
    
    # Percorso del file PDF da generare
    output_path = os.path.join(offer_folder, f"offerta_{offerta['offer_number']}.pdf")
    
    # Inizializza il canvas PDF
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    
    # Stile personalizzato per i paragrafi
    custom_style = ParagraphStyle(
        name="CustomStyle",
        fontSize=12,
        leading=20,
        spaceAfter=10,
        fontName="Times-Roman",
    )
    
    # Carica e posiziona i logo
    logo_valtservice_path = os.path.join(static_folder, 'img', 'logo_valtservice.png')
    logo_zanussi_path = os.path.join(static_folder, 'img', 'logo_zanussi.png')
    
    try:
        img = ImageReader(logo_valtservice_path)
        img_width, img_height = img.getSize()
        aspect_ratio = img_width / img_height
        max_width, max_height = 200, 100
        if img_width > max_width or img_height > max_height:
            if img_width > img_height:
                new_width = max_width
                new_height = new_width / aspect_ratio
            else:
                new_height = max_height
                new_width = new_height * aspect_ratio
        else:
            new_width, new_height = img_width, img_height
        c.drawImage(img, 50, height - new_height - 20, width=new_width, height=new_height)
    except Exception as e:
        print("Logo non caricato:", e)
    
    try:
        img = ImageReader(logo_zanussi_path)
        img_width, img_height = img.getSize()
        aspect_ratio = img_width / img_height
        max_width, max_height = 80, 50
        if img_width > max_width or img_height > max_height:
            if img_width > img_height:
                new_width2 = max_width
                new_height2 = new_width2 / aspect_ratio
            else:
                new_height2 = max_height
                new_width2 = new_height2 * aspect_ratio
        else:
            new_width2, new_height2 = img_width, img_height
        c.drawImage(img, 460, height - new_height2 - 20, width=new_width2, height=new_height2)
    except Exception as e:
        print("Logo Zanussi non caricato:", e)
    
    # Linea separatrice dopo i loghi
    c.line(50, height - 105, width - 50, height - 105)
    
    # Informazioni di base dell'offerta
    c.setFont("Times-Roman", 12)
    c.drawString(50, height - 140, f"Offerta N: {offerta['offer_number']} - Data: {offerta['date']}")
    
    # Informazioni cliente
    text_width = c.stringWidth("Spett.le", "Times-Roman", 14)
    c.drawString(((width - text_width) / 2), height - 200, "Spett.le")
    c.setFont("Times-Bold", 14)
    text = offerta['customer']
    text_width = c.stringWidth(text, "Times-Bold", 14)
    c.drawString(((width - text_width) / 2), height - 220, text)
    
    c.setFont("Times-Roman", 14)
    text = offerta['customer_email']
    email_width = c.stringWidth(text, "Times-Roman", 14)
    c.drawString(((width - email_width) / 2), height - 260, text)
    
    c.setFont("Times-Roman", 14)
    text = offerta['address']
    text_width = c.stringWidth(text, "Times-Roman", 14)
    c.drawString(((width - text_width) / 2), height - 240, text)
    
    # Linea tratteggiata
    c.setDash(3, 2)
    c.line(50, height - 320, width - 50, height - 320)
    c.line(50, height - 325, width - 50, height - 325)
    c.setDash()
    
    # Oggetto dell'offerta
    c.setFont("Times-Bold", 14)
    c.drawString(50, height - 360, "Oggetto offerta:")
    text_width = c.stringWidth("Oggetto offerta:", "Times-Bold", 16)
    c.setFont("Times-Roman", 14)
    c.drawString(text_width + 50, height - 360, "Abbiamo il piacere di presentare la ns. Offerta per la fornitura ")
    c.drawString(text_width + 50, height - 375, "di attrezzature per cucina.")
    
    # Descrizione offerta
    c.setFont("Times-Bold", 14)
    offer_description_text = f"<b>Descrizione offerta:</b> {offerta['offer_description']}"
    para = Paragraph(offer_description_text, ParagraphStyle(name="CustomStyle", fontSize=14, leading=20))
    available_width = width - 100
    available_height = height - 400
    _, para_height = para.wrap(available_width, available_height)
    para.drawOn(c, 50, height - 400 - para_height)
    
    # Testo finale
    c.setFont("Times-Roman", 12)
    c.drawString(50, height - 620, "Per ulteriori dettagli e specifiche consultare l'interno dell'offerta.")
    c.drawString(50, height - 640, "Augurando buon lavoro, porgiamo cordiali saluti.")
    
    # Linea tratteggiata finale
    c.setDash(3, 2)
    c.line(50, height - 655, width - 50, height - 655)
    c.line(50, height - 660, width - 50, height - 660)
    c.setDash()
    
    # Footer
    c.setFont("Times-Roman", 9)
    diff = 740
    c.drawString(50, height - diff, "Valtservice")
    c.drawString(50, height - diff - 20, "Part. Iva:.00872020144")
    c.drawString(50, height - diff - 30, "Iscrizione R.E.A.SO - 65776")
    c.drawString(450, height - diff, "Filiale di Sondrio:")
    c.drawString(450, height - diff - 10, "Via  Valeriana, 103/A")
    c.drawString(450, height - diff - 20, "23019 TRAONA (SO)")
    c.drawString(450, height - diff - 30, "Tel. (+39) 0342590138")
    c.drawString(450, height - diff - 40, "info@valtservice.com")
    c.setFont("Times-Roman", 7)
    c.drawString(50, height - diff - 60, "I modelli e le specifiche tecniche dei prodotti indicati possono subire variazioni senza preavviso.")
    
    # Processa i tab
    for tab in offerta.get('tabs', []):
        if tab["type"] == "multi_product":
            products = tab.get('products', [])
            max_items_per_page = tab.get('max_items_per_page', 3)
            tab_total_price = 0

            for i in range(0, len(products), max_items_per_page):
                c.showPage()

                # Intestazione nuova pagina
                try:
                    img = ImageReader(logo_valtservice_path)
                    img_width, img_height = img.getSize()
                    aspect_ratio = img_width / img_height
                    max_width, max_height = 200, 100
                    if img_width > max_width or img_height > max_height:
                        if img_width > img_height:
                            new_width = max_width
                            new_height = new_width / aspect_ratio
                        else:
                            new_height = max_height
                            new_width = new_height * aspect_ratio
                    else:
                        new_width, new_height = img_width, img_height
                    c.drawImage(img, 50, height - new_height - 20, width=new_width, height=new_height)
                except Exception as e:
                    print("Errore caricamento logo_valtservice:", e)

                try:
                    img = ImageReader(logo_zanussi_path)
                    img_width, img_height = img.getSize()
                    aspect_ratio = img_width / img_height
                    max_width, max_height = 80, 50
                    if img_width > max_width or img_height > max_height:
                        if img_width > img_height:
                            new_width2 = max_width
                            new_height2 = new_width2 / aspect_ratio
                        else:
                            new_height2 = max_height
                            new_width2 = new_height2 * aspect_ratio
                    else:
                        new_width2, new_height2 = img_width, img_height
                    c.drawImage(img, 460, height - new_height2 - 20, width=new_width2, height=new_height2)
                except Exception as e:
                    print("Errore caricamento logo_zanussi:", e)

                c.setLineWidth(1)
                c.setStrokeColorRGB(0, 0, 0, alpha=1)
                c.line(50, height - 105, width - 50, height - 105)

                page_products = products[i:i + max_items_per_page]
                y_position = height - 150
                for product in page_products:
                    nome, _, prezzo_unitario, quantita, descrizione = product

                    try:
                        prezzo_unitario = float(prezzo_unitario)
                        quantita = float(quantita)
                        tab_total_price += prezzo_unitario * quantita
                    except ValueError:
                        prezzo_unitario = 0
                        quantita = 0

                    c.setFillColorRGB(128 / 256, 128 / 256, 128 / 256, alpha=0.3)
                    c.rect(50, y_position - 20, width - 100, 20, fill=1, stroke=0)
                    c.setFillColorRGB(0, 0, 0, alpha=1)
                    c.setFont("Times-Bold", 12)
                    c.drawString(60, y_position - 15, f"Nome: {nome}")
                    c.line(50, y_position - 20, width - 50, y_position - 20)
                    c.line(50, y_position, width - 50, y_position)

                    y_position -= 40
                    c.setFont("Times-Bold", 12)
                    c.drawString(50, y_position, "Descrizione:")
                    description_paragraph = Paragraph(descrizione, custom_style)
                    available_width = width - 100
                    _, para_height = description_paragraph.wrap(available_width, y_position - 15)
                    description_paragraph.drawOn(c, 50, y_position - 5 - para_height)
                    y_position -= 35 + para_height

                    c.setFont("Times-Bold", 12)
                    c.drawString(50, y_position, f"Prezzo Unitario: {format_price(prezzo_unitario)} €")
                    c.drawString(300, y_position, f"Quantità: {quantita:.0f}")
                    y_position -= 40

                c.setFont("Times-Bold", 14)
                c.drawString(50, height - 630, f"PREZZO FORNITURA: {format_price(tab_total_price)} €")
                
                # Aggiorna il prezzo totale dell'offerta
                total_offer_price += tab_total_price

                c.setDash(3, 2)
                c.line(50, height - 655, width - 50, height - 655)
                c.line(50, height - 660, width - 50, height - 660)
                c.setDash()
                
                # Footer
                c.setFont("Times-Roman", 9)
                diff = 740
                c.drawString(50, height - diff, "Valtservice")
                c.drawString(50, height - diff - 20, "Part. Iva:.00872020144")
                c.drawString(50, height - diff - 30, "Iscrizione R.E.A.SO - 65776")
                c.drawString(450, height - diff, "Filiale di Sondrio:")
                c.drawString(450, height - diff - 10, "Via  Valeriana, 103/A")
                c.drawString(450, height - diff - 20, "23019 TRAONA (SO)")
                c.drawString(450, height - diff - 30, "Tel. (+39) 0342590138")
                c.drawString(450, height - diff - 40, "info@valtservice.com")
                c.setFont("Times-Roman", 7)
                c.drawString(50, height - diff - 60, "I modelli e le specifiche tecniche dei prodotti indicati possono subire variazioni senza preavviso.")

        else:
            # Pagina per prodotto singolo
            c.showPage()

            try:
                img = ImageReader(logo_valtservice_path)
                img_width, img_height = img.getSize()
                aspect_ratio = img_width / img_height
                max_width, max_height = 200, 100
                if img_width > max_width or img_height > max_height:
                    if img_width > img_height:
                        new_width = max_width
                        new_height = new_width / aspect_ratio
                    else:
                        new_height = max_height
                        new_width = new_height * aspect_ratio
                else:
                    new_width, new_height = img_width, img_height
                c.drawImage(img, 50, height - new_height - 20, width=new_width, height=new_height)
            except Exception as e:
                print("Errore caricamento logo_valtservice:", e)

            try:
                img = ImageReader(logo_zanussi_path)
                img_width, img_height = img.getSize()
                aspect_ratio = img_width / img_height
                max_width, max_height = 80, 50
                if img_width > max_width or img_height > max_height:
                    if img_width > img_height:
                        new_width2 = max_width
                        new_height2 = new_width2 / aspect_ratio
                    else:
                        new_height2 = max_height
                        new_width2 = new_height2 * aspect_ratio
                else:
                    new_width2, new_height2 = img_width, img_height
                c.drawImage(img, 460, height - new_height2 - 20, width=new_width2, height=new_height2)
            except Exception as e:
                print("Errore caricamento logo_zanussi:", e)

            product_code = tab.get('product_code', '')
            product_name = tab.get('product_name', '')
            description = tab.get('description', '')
            power = tab.get('power_w', '')
            volts = tab.get('volts', '')
            size = tab.get('size', '')
            pos = tab.get('posizione', '')

            try:
                unit_price = float(tab.get('unit_price', 0))
            except ValueError:
                unit_price = 0

            try:
                quantity = float(tab.get('quantity', 0))
            except ValueError:
                quantity = 0

            prezzo_list = unit_price * quantity
            # Aggiorna il prezzo totale dell'offerta
            total_offer_price += prezzo_list

            c.line(50, height - 105, width - 50, height - 105)
        
            c.setLineWidth(1)
            c.setDash(6, 4)
            c.line(50, height - 675, width - 50, height - 675)
            c.line(50, height - 680, width - 50, height - 680)
            c.setDash()

            new_width = 0  # Default in caso non ci sia immagine
            
            if tab.get('product_image_path'):
                try:
                    # Path completo in base all'origine del path
                    if tab['product_image_path'].startswith('/static'):
                        img_path = os.path.join(app_root, tab['product_image_path'].lstrip('/'))
                    else:
                        img_path = tab['product_image_path']
                    
                    img = ImageReader(img_path)
                    img_width, img_height = img.getSize()
                    aspect_ratio = img_width / img_height
                    
                    max_width, max_height = 200, 150
                    if img_width > max_width or img_height > max_height:
                        if img_width > img_height:
                            new_width = max_width
                            new_height = new_width / aspect_ratio
                        else:
                            new_height = max_height
                            new_width = new_height * aspect_ratio
                    else:
                        new_width, new_height = img_width, img_height
                    
                    x_pos, y_pos = 50, height - 320  
                    c.drawImage(img, x_pos, y_pos, width=new_width, height=new_height)
                except Exception as e:
                    print(f"Could not load the product image: {e}")
                    new_width = 0

            fix = 180
            sp = 25
            c.setFont("Times-Bold", 12)

            text = [
                f"NOME PRODOTTO: {product_name}",
                f"CARATTERISTICHE TECNICHE",
                f"TENSIONE:                                     {volts}",
                f"POTENZA:                                      {power}",
                f"DIMENSIONI [LxPxH]:                {size}",
                f"PREZZO UNITARIO:                   {format_price(unit_price)} €",
                f"QUANTITA':                                   {quantity}",
                f"POS: {pos}"
            ]

            for i in range(len(text)):
                if i == 0:
                    c.setFillColorRGB(128 / 256, 128 / 256, 128 / 256, alpha=0.3)
                    c.setStrokeColorRGB(0, 0, 0, alpha=0)
                    c.rect(50, height - 150, width - 100, 20, fill=1, stroke=1)
                    c.setLineWidth(1)
                    c.setStrokeColorRGB(0, 0, 0, alpha=1)
                    c.line(50, height - 130, width - 50, height - 130)
                    c.line(50, height - 150, width - 50, height - 150)
                    c.setFillColorRGB(0, 0, 0, alpha=1)
                    c.drawString(60, height - 145, text[i])
                    c.setFont("Times-Roman", 12)
                    c.drawString(50, height - 125, text[7])
                elif i == 1:  # This now handles the "CARATTERISTICHE TECNICHE" section
                    c.setFillColorRGB(128 / 256, 128 / 256, 128 / 256, alpha=0.3)
                    c.setStrokeColorRGB(0, 0, 0, alpha=0)
                    c.rect(60 + new_width, height - (fix + 3), width - (new_width + 110), 20, fill=1, stroke=1)

                    c.setLineWidth(1)
                    c.setStrokeColorRGB(0, 0, 0, alpha=1)
                    c.line(60 + new_width, height - (fix - 17), width - 50, height - (fix - 17))
                    c.line(60 + new_width, height - (fix + 3), width - 50, height - (fix + 3))

                    c.setFillColorRGB(0, 0, 0, alpha=1)
                    c.drawString(80 + new_width, height - (fix - 2), text[1])

                    fix = fix + sp

                elif i not in (0, 1, 7):
                    c.setFont("Times-Roman", 12)
                    c.setLineWidth(0.5)
                    c.setStrokeColorRGB(0, 0, 0, alpha=0.6)
                    c.line(60 + new_width, height - (fix - 17), width - 50, height - (fix - 17))
                    c.line(60 + new_width, height - (fix + 3), width - 50, height - (fix + 3))

                    c.setFillColorRGB(0, 0, 0, alpha=1)
                    c.drawString(80 + new_width, height - (fix - 2), text[i])

                    fix = fix + sp

            fix = 350
            c.setFont("Times-Roman",12)
            spazio = 10
            c.setStrokeColorRGB(0, 0, 0, alpha=1)
            product_description_text = f"{description}"
            para = Paragraph(product_description_text, custom_style)
            available_width = width - 100
            available_height = height - (fix + spazio + 23)
            _, para_height3 = para.wrap(available_width, available_height)
            para.drawOn(c, 50, height - (fix + spazio + 15) - para_height3)
            c.setFont("Times-Bold",12)
            c.setFillColorRGB(0, 0, 0, alpha=1)
            c.drawString(50, height - (fix+spazio), f"DESCRIZIONE PRODOTTO")

            y_position = height - 565
            if tab.get('discount_flag'):
                c.setFillColorRGB(0, 0, 0, alpha=1)
                c.drawString(60, y_position, f"PREZZO DI LISTINO:")

                c.drawString(250, y_position, f"€ {format_price(prezzo_list)} iva ESCLUSA")
                y_position -= 30
                c.drawString(60, y_position, f"SCONTO")
                c.drawString(250, y_position, f"{tab.get('discount', '0')} %")
                y_position -= 30
                try:
                    discount = float(tab.get('discount', 0))
                except ValueError:
                    discount = 0
                c.drawString(60, y_position, f"PREZZO SCONTATO:")
                c.drawString(250, y_position, f"€ {format_price(prezzo_list - (discount / 100) * prezzo_list)} iva ESCLUSA")
            else:
                y_position1 = y_position - 43
                c.setFillColorRGB(0, 0, 0, alpha=1)
                c.drawString(60, y_position1, f"PREZZO SCONTATO:")
                c.drawString(250, y_position1, f"€ {format_price(prezzo_list)} iva ESCLUSA")
    
            # Footer
            c.setFont("Times-Roman", 9)
            diff = 740
            c.drawString(50, height - diff, "Valtservice")
            c.drawString(50, height - diff - 20, "Part. Iva:.00872020144")
            c.drawString(50, height - diff - 30, "Iscrizione R.E.A.SO - 65776")
            c.drawString(450, height - diff, "Filiale di Sondrio:")
            c.drawString(450, height - diff - 10, "Via  Valeriana, 103/A")
            c.drawString(450, height - diff - 20, "23019 TRAONA (SO)")
            c.drawString(450, height - diff - 30, "Tel. (+39) 0342590138")
            c.drawString(450, height - diff - 40, "info@valtservice.com")
            c.setFont("Times-Roman", 7)
            c.drawString(50, height - diff - 60, "I modelli e le specifiche tecniche dei prodotti indicati possono subire variazioni senza preavviso.")
    
    # Aggiungi pagina finale (condizioni)
    c.showPage()
    c.setFont("Times-Roman", 16)
    
    # Intestazione
    try:
        img = ImageReader(logo_valtservice_path)
        img_width, img_height = img.getSize()
        aspect_ratio = img_width / img_height
        max_width, max_height = 200, 100
        if img_width > max_width or img_height > max_height:
            if img_width > img_height:
                new_width = max_width
                new_height = new_width / aspect_ratio
            else:
                new_height = max_height
                new_width = new_height * aspect_ratio
        else:
            new_width, new_height = img_width, img_height
        c.drawImage(img, 50, height - new_height - 20, width=new_width, height=new_height)
    except Exception as e:
        print("Logo non caricato:", e)
    
    try:
        img = ImageReader(logo_zanussi_path)
        img_width, img_height = img.getSize()
        aspect_ratio = img_width / img_height
        max_width, max_height = 80, 50
        if img_width > max_width or img_height > max_height:
            if img_width > img_height:
                new_width2 = max_width
                new_height2 = new_width2 / aspect_ratio
            else:
                new_height2 = max_height
                new_width2 = new_height2 * aspect_ratio
        else:
            new_width2, new_height2 = img_width, img_height
        c.drawImage(img, 460, height - new_height2 - 20, width=new_width2, height=new_height2)
    except Exception as e:
        print("Logo Zanussi non caricato:", e)

    c.line(50, height - 105, width - 50, height - 105)

    # Condizioni dell'offerta
    c.setFont("Times-Roman", 12)
    y_position = 650
    sp = 35
    c.drawString(60, y_position, "Garanzia:")
    c.drawString(60, y_position-sp, "Validità Offerta:")
    c.drawString(60, y_position-2*sp, "Termini di consegna:")
    c.drawString(60, y_position-3*sp, "Spedizione :")
    c.drawString(60, y_position-4*sp, "Pagamento:")
    c.drawString(60, y_position-5*sp, "Oneri Bancari:")
    c.drawString(60, y_position-6*sp, "Imballo:")
    c.drawString(60, y_position-7*sp, "Montaggio:")
    c.drawString(60,y_position-8*sp, "Allacciamenti:")
    c.drawString(60, y_position-9*sp, "Riserve:")
    c.drawString(60, y_position-10*sp, "IVA:")

    c.drawString(250, y_position, "12 mesi su ricambi e manodopera")
    c.drawString(250, y_position-sp, "30 gg")
    c.drawString(250, y_position-2*sp, "Da convenire")
    c.drawString(250, y_position-3*sp, "ns carico")
    c.drawString(250, y_position-4*sp, "Da convenire")
    c.drawString(250, y_position-5*sp, "A Vs. carico")
    c.drawString(250, y_position-6*sp, "Standard, già compreso nel prezzo delle apparecchiature,")
    c.drawString(250, y_position-6*sp-10, "Smaltimento a Vs. carico.")
    c.drawString(250, y_position-7*sp, "Incluso, da Centri Servizi Tecnici ELECTROLUX SERVICE")
    c.drawString(250, y_position-8*sp, "Elettrici ed idraulici esclusi")
    c.drawString(250, y_position-9*sp, "Riserva di proprietà ai sensi dell'art. 1523 del Codice Civile.")
    c.drawString(250, y_position-10*sp, "I prezzi indicati in offerta sono da considerarsi al netto IVA")
    
    c.setFont("Times-Bold", 16)
    c.drawString(50,height-620, f"Prezzo totale offerta : {format_price(total_offer_price)} €")

    # Linea tratteggiata finale
    c.setDash(3, 2)
    c.line(50, height - 655, width - 50, height - 655)
    c.line(50, height - 660, width - 50, height - 660)
    c.setDash()

    # Footer
    diff = 740
    c.setFont("Times-Roman", 9)
    c.drawString(50, height - diff, "Valtservice")
    c.drawString(50, height - diff - 20, "Part. Iva:.00872020144")
    c.drawString(50, height - diff - 30, "Iscrizione R.E.A.SO - 65776")
    c.drawString(450, height - diff, "Filiale di Sondrio:")
    c.drawString(450, height - diff - 10, "Via  Valeriana, 103/A")
    c.drawString(450, height - diff - 20, "23019 TRAONA (SO)")
    c.drawString(450, height - diff - 30, "Tel. (+39) 0342590138")
    c.drawString(450, height - diff - 40, "info@valtservice.com")
    c.setFont("Times-Roman", 7)
    c.drawString(50, height - diff - 60, "I modelli e le specifiche tecniche dei prodotti indicati possono subire variazioni senza preavviso.")

    # Salva il PDF
    c.save()
    
    return output_path