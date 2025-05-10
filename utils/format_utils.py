def format_price(value):
    """
    Formatta un prezzo nel formato italiano (es: 10.345,00)
    
    Args:
        value (float|str): Il valore da formattare
    
    Returns:
        str: Il prezzo formattato
    """
    try:
        # Converte il valore in float se è una stringa
        if isinstance(value, str):
            value = float(value.replace(',', '.'))
        
        # Separa la parte intera dai decimali
        integer_part = int(value)
        decimal_part = int(round((value - integer_part) * 100))
        
        # Formatta la parte intera con i separatori delle migliaia
        formatted_integer = "{:,}".format(integer_part).replace(',', '.')
        
        # Combina con i decimali
        return f"{formatted_integer},{decimal_part:02d}"
    except (ValueError, TypeError):
        return "0,00"
