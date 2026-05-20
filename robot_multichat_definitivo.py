import re
import pandas as pd
from io import BytesIO

def extract_price(text):
    price_pattern = r"(?:price|precio|tarifa)?\s?(\d{3,4})\s?(?:€|eur|euros)?"
    match = re.search(price_pattern, text, re.IGNORECASE)
    return f"Precio: {match.group(1)}€" if match else ""

def extract_phone(text):
    phone_pattern = r"(\+?\d{1,3}[\s-]?\d{3}[\s-]?\d{3,4}[\s-]?\d{0,4})"
    match = re.search(phone_pattern, text)
    if match:
        phone = match.group(1).strip()
        if len(re.sub(r'\D', '', phone)) >= 9:
            return phone
    return ""

def process_multichat(text):
    paises_map = {
        'FR': 'FRANCIA', 'IT': 'ITALIA', 'ES': 'ESPAÑA', 
        'GB': 'REINO UNIDO', 'NL': 'PAISES BAJOS', 'DE': 'ALEMANIA',
        'PL': 'POLONIA', 'BE': 'BELGICA', 'PT': 'PORTUGAL', 'CZ': 'REPUBLICA CHECA',
        'AT': 'AUSTRIA', 'RO': 'RUMANIA', 'BG': 'BULGARIA', 'HU': 'HUNGRIA'
    }
    
    # Separar el texto por bloques de chat (cada bloque empieza con una ruta tipo "XX 00 -> YY 00")
    # Usamos un split basado en el patrón de ruta
    blocks = re.split(r'(?=\b[A-Z]{2}\s\w+\s[\w\s]+->)', text)
    
    all_data = []
    columnas = [
        'Empresa', 'Email', 'Teléfono', 'Contacto', 
        'País Origen', 'Código Origen', 'Ciudad Origen', 
        'País Destino', 'Código Destino', 'Ciudad Destino', 
        'Tipo de Camión', 'Comentarios', 'Destinos'
    ]

    for block in blocks:
        if not block.strip(): continue
        
        entry = {col: "" for col in columnas}
        lines = block.strip().split('\n')
        
        # 1. Extraer Ruta (primera línea del bloque)
        ruta_match = re.search(r"([A-Z]{2})\s(\w+)\s([\w\s]+)\s->\s([A-Z]{2})\s(\w+)\s([\w\s]+)", lines[0])
        if ruta_match:
            entry['País Origen'] = paises_map.get(ruta_match.group(1), ruta_match.group(1))
            entry['Código Origen'] = ruta_match.group(2)
            entry['Ciudad Origen'] = ruta_match.group(3).strip()
            entry['País Destino'] = paises_map.get(ruta_match.group(4), ruta_match.group(4))
            entry['Código Destino'] = ruta_match.group(5)
            entry['Ciudad Destino'] = ruta_match.group(6).strip()
            entry['Destinos'] = entry['País Destino']
        
        # 2. Extraer Contacto y Empresa (segunda línea)
        if len(lines) > 1:
            ce_match = re.search(r"^([^\(]+)\s\(\"([^\"]+)\"", lines[1])
            if ce_match:
                entry['Contacto'] = ce_match.group(1).strip()
                entry['Empresa'] = ce_match.group(2).strip()
                entry['Email'] = f"info@{entry['Empresa'].lower().replace(' ', '')}.com"
        
        # 3. Extraer Precio y Teléfono del resto de líneas
        full_message = " ".join(lines[2:]) if len(lines) > 2 else ""
        if full_message:
            entry['Teléfono'] = extract_phone(full_message)
            precio = extract_price(full_message)
            entry['Comentarios'] = f"{precio} | Chat: {full_message}".strip(" | ")
        
        if not entry['Teléfono']: entry['Teléfono'] = "+00 000 000 000"
        entry['Tipo de Camión'] = "Lona"
        
        if entry['Empresa']:
            all_data.append(entry)

    return pd.DataFrame(all_data, columns=columnas)

if __name__ == "__main__":
    print("--- ROBOT MULTICHAT TIMOCOM ---")
    print("Pega todos los chats aquí (Pulsa Ctrl+D o Ctrl+Z en una línea nueva al terminar):")
    import sys
    input_text = sys.stdin.read()
    
    if input_text.strip():
        df = process_multichat(input_text)
        df.to_excel("IMPORTACION_MULTICHAT.xlsx", index=False)
        print(f"\n✅ Éxito! Se han procesado {len(df)} transportistas.")
        print("El archivo 'IMPORTACION_MULTICHAT.xlsx' está listo.")
    else:
        print("No se recibió texto.")
