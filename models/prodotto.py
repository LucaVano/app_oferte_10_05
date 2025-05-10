class BaseProdotto:
    """Classe base per i prodotti nelle offerte."""
    
    def __init__(self, nome='', modello='', prezzo_unitario=0.0, quantita=1, descrizione=''):
        """
        Inizializza un prodotto base
        
        Args:
            nome (str): Nome del prodotto
            modello (str): Modello o codice del prodotto
            prezzo_unitario (float): Prezzo unitario
            quantita (int): Quantità 
            descrizione (str): Descrizione del prodotto
        """
        self.nome = nome
        self.modello = modello
        self.prezzo_unitario = float(prezzo_unitario) if prezzo_unitario else 0.0
        self.quantita = int(quantita) if quantita else 1
        self.descrizione = descrizione
    
    def get_prezzo_totale(self):
        """
        Calcola il prezzo totale del prodotto
        
        Returns:
            float: Prezzo totale (prezzo unitario * quantità)
        """
        return self.prezzo_unitario * self.quantita
    
    def to_dict(self):
        """
        Converte il prodotto in un dizionario
        
        Returns:
            dict: Dizionario con i dati del prodotto
        """
        return {
            'nome': self.nome,
            'modello': self.modello,
            'prezzo_unitario': self.prezzo_unitario,
            'quantita': self.quantita,
            'descrizione': self.descrizione
        }