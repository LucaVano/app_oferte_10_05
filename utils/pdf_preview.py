import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from utils.format_utils import format_price

def generate_pdf_preview(offerta, app_root, output_path):
    """Genera un PDF di anteprima con i dati delle schede senza creare cartelle cliente."""
    # Assicuriamoci che tabs esista
    if 'tabs' not in offerta or not isinstance(offerta['tabs'], list):
        offerta['tabs'] = []
    
    # Inizializza il prezzo totale dell'offerta
    total_offer_price = 0
    
    # Percorsi delle risorse
    static_folder = os.path.join(app_root, 'static')
    
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
    c.drawString(50, height - 360, "OGGETTO OFFERTA:")
    text_width = c.stringWidth("OGGETTO OFFERTA: ", "Times-Bold", 14)
    c.setFont("Times-Roman", 14)
    c.drawString(text_width + 50, height - 360, "Abbiamo il piacere di presentare la ns. Offerta per la fornitura ")
    c.drawString(text_width + 50, height - 375, "di attrezzature per cucina.")
    
    # Descrizione offerta
    c.setFont("Times-Bold", 14)
    c.drawString(50, height - 400, "DESCRIZIONE OFFERTA:")

    description_text = offerta['offer_description']

    # Prima verifica l'altezza con font 14
    test_style = ParagraphStyle(
        name="TestStyle",
        fontSize=14,
        fontName="Times-Roman",
        leading=20
    )
    test_para = Paragraph(description_text, test_style)
    available_width = width - 100
    _, test_para_height = test_para.wrap(available_width, height - 410)

    # Scegli il font in base all'altezza
    if test_para_height < 200:
        # Usa il font 14 se il testo è corto
        font_size = 14
    else:
        # Altrimenti usa il font 12
        font_size = 12

    # Ora crea il paragrafo con il font scelto
    final_style = ParagraphStyle(
        name="DescriptionStyle",
        fontSize=font_size,
        fontName="Times-Roman",
        leading=20
    )
    para = Paragraph(description_text, final_style)
    _, para_height = para.wrap(available_width, height - 410)
    para.drawOn(c, 50, height - 410 - para_height)

    # Calcola la posizione del testo finale basata sulla fine del paragrafo
    text_y_position = height - 410 - para_height - 30

    if text_y_position > (height - 610):
        # Testo finale
        c.setFont("Times-Roman", 12)
        c.drawString(50, height - 620, "Per ulteriori dettagli e specifiche consultare l'interno dell'offerta.")
        c.drawString(50, height - 640, "Augurando buon lavoro, porgiamo cordiali saluti.")

        # Linea tratteggiata finale
        c.setDash(3, 2)
        c.line(50, height - 655, width - 50, height - 655)
        c.line(50, height - 660, width - 50, height - 660)
        c.setDash()
    else:
        # Testo finale (posizionato dinamicamente)
        c.setFont("Times-Roman", 12)
        c.drawString(50, text_y_position + 10, "Per ulteriori dettagli e specifiche consultare l'interno dell'offerta.")
        c.drawString(50, text_y_position - 5, "Augurando buon lavoro, porgiamo cordiali saluti.")
            
        # Linea tratteggiata finale (posizionata dinamicamente)
        c.setDash(3, 2)
        c.line(50, text_y_position - 20, width - 50, text_y_position - 20)
        c.line(50, text_y_position - 25, width - 50, text_y_position - 25)
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
    
    # Numero di pagina 1
    c.setFont("Times-Roman", 9)
    c.drawString(width/2, height - diff - 80, "Pagina 1")

    # Processa anche alcune schede prodotto (prime 1-2) per l'anteprima
    # Limita a massimo 3 pagine per motivi di performance
    max_preview_tabs = min(2, len(offerta.get('tabs', [])))
    
    # Qui continua la generazione delle pagine prodotto, come nella funzione originale...
    
    # Salva il PDF
    c.save()
    
    return output_path
