class Offerta:
    """Classe che rappresenta un'offerta commerciale."""
    
    def __init__(self, id=None, offer_number=None, date=None, customer=None, customer_email=None, 
                 address=None, offer_description=None, tabs=None, status='pending'):
        """
        Inizializza un'offerta con i dati forniti
        
        Args:
            id (str): ID dell'offerta
            offer_number (str): Numero dell'offerta
            date (str): Data dell'offerta
            customer (str): Nome del cliente
            customer_email (str): Email del cliente
            address (str): Indirizzo del cliente
            offer_description (str): Descrizione dell'offerta
            tabs (list): Lista di tabulazioni dell'offerta
            status (str): Stato dell'offerta ('pending' o 'accepted')
        """
        self.id = id
        self.offer_number = offer_number
        self.date = date
        self.customer = customer
        self.customer_email = customer_email
        self.address = address
        self.offer_description = offer_description
        self.tabs = tabs or []
        self.status = status
        self.pdf_path = ''
    
    def to_dict(self):
        """
        Converte l'offerta in un dizionario
        
        Returns:
            dict: Dizionario con i dati dell'offerta
        """
        return {
            'id': self.id,
            'offer_number': self.offer_number,
            'date': self.date,
            'customer': self.customer,
            'customer_email': self.customer_email,
            'address': self.address,
            'offer_description': self.offer_description,
            'tabs': self.tabs,
            'pdf_path': self.pdf_path,
            'status': self.status
        }
    
    def get_total_price(self):
        """
        Calcola il prezzo totale dell'offerta
        
        Returns:
            float: Prezzo totale dell'offerta
        """
        total = 0.0
        
        for tab in self.tabs:
            if tab.get('type') == 'single_product':
                try:
                    price = float(tab.get('unit_price', 0))
                    quantity = float(tab.get('quantity', 0))
                    discount = float(tab.get('discount', 0)) if tab.get('discount_flag') else 0
                    
                    # Applica lo sconto se necessario
                    if discount > 0:
                        price = price * (1 - discount / 100)
                    
                    total += price * quantity
                except (ValueError, TypeError):
                    pass
            
            elif tab.get('type') == 'multi_product':
                products = tab.get('products', [])
                for product in products:
                    try:
                        if len(product) >= 4:  # Nome, modello, prezzo, quantità
                            price = float(product[2])
                            quantity = float(product[3])
                            total += price * quantity
                    except (ValueError, TypeError, IndexError):
                        pass
        
        return total
    
    def get_product_count(self):
        """
        Restituisce il numero totale di prodotti nell'offerta
        
        Returns:
            int: Numero di prodotti
        """
        count = 0
        
        for tab in self.tabs:
            if tab.get('type') == 'single_product':
                count += 1
            elif tab.get('type') == 'multi_product':
                count += len(tab.get('products', []))
        
        return count