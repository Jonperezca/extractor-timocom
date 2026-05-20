import streamlit as st
import pandas as pd
import re
from io import BytesIO

def extract_price(text):
    """Busca precios en formatos: 1900e, 1900 €, 1900 eur, etc."""
    price_pattern = r"(\d{3,4})\s?(?:e|€|eur|euros|usd|\$)"
    matches = re.findall(price_pattern, text, re.IGNORECASE)
    if matches:
        return f"{matches[-1]}€"
    return ""

def extract_phone(text):
    """Busca teléfonos con diversos formatos"""
    phone_pattern = r"(\+?\d{1,3}[\s-]?\d{3}[\s-]?\d{3,4}[\s-]?\d{0,4})"
    matches = re.findall(phone_pattern, text)
    for match in matches:
        phone = match.strip()
        if len(re.sub(r'\D', '', phone)) >= 9:
            return phone
    return ""

def process_final_clean(text):
    paises_map = {
        'FR': 'FRANCIA', 'IT': 'ITALIA', 'ES': 'ESPAÑA', 
        'GB': 'REINO UNIDO', 'NL': 'PAISES BAJOS', 'DE': 'ALEMANIA',
        'PL': 'POLONIA', 'BE': 'BELGICA', 'PT': 'PORTUGAL', 'CZ': 'REPUBLICA CHECA',
        'AT': 'AUSTRIA', 'RO': 'RUMANIA', 'BG': 'BULGARIA', 'HU': 'HUNGRIA'
    }
    
    text = text.replace('➞', '->').replace('➔', '->').replace('–', '-')
    route_pattern = r"([A-Z]{2})\s(\w+)\s([\w\s]+)\s->\s([A-Z]{2})\s(\w+)\s([\w\s]+)"
    route_matches = list(re.finditer(route_pattern, text))
    
    if not route_matches:
        return pd.DataFrame()

    all_data = []
    columnas = ['Empresa', 'Email', 'Teléfono', 'Contacto', 'País Origen', 'Código Origen', 'Ciudad Origen', 'País Destino', 'Código Destino', 'Ciudad Destino', 'Tipo de Camión', 'Comentarios', 'Destinos']

    for i in range(len(route_matches)):
        start = route_matches[i].start()
        end = route_matches[i+1].start() if i+1 < len(route_matches) else len(text)
        block_start = max(0, start - 200)
        block = text[block_start:end]
        
        entry = {col: "" for col in columnas}
        
        # 1. Datos de la Ruta
        m = route_matches[i]
        entry['País Origen'] = paises_map.get(m.group(1), m.group(1))
        entry['Código Origen'] = m.group(2)
        entry['Ciudad Origen'] = m.group(3).split('(')[0].strip()
        entry['País Destino'] = paises_map.get(m.group(4), m.group(4))
        entry['Código Destino'] = m.group(5)
        entry['Ciudad Destino'] = m.group(6).split('(')[0].strip()
        entry['Destinos'] = entry['País Destino']
        
        # 2. Buscar Empresa (Logaro, etc.)
        empresa_match = re.search(r"([A-Z][\w\s\.\-&]+(?:sp\. z o\.o\.|S\.L\.|GmbH|Ltd|S\.A\.|Srl|Kft))", block, re.IGNORECASE)
        if empresa_match:
            entry['Empresa'] = empresa_match.group(1).strip()
        else:
            # Si no hay sufijo, buscamos la primera línea capitalizada del bloque
            lines = [l.strip() for l in block.split('\n') if l.strip()]
            if lines: entry['Empresa'] = lines[0]
        
        # 3. Buscar Contacto
        contacto_match = re.search(r"(?:Habla:|Contacto:)\s?([\w\s]+)", block, re.IGNORECASE)
        if contacto_match:
            entry['Contacto'] = contacto_match.group(1).strip()
        else:
            names = re.findall(r"\b([A-Z][a-z]+\s[A-Z][a-z]+)\b", block)
            if names: entry['Contacto'] = names[0]

        # 4. Precio y Teléfono
        entry['Teléfono'] = extract_phone(block)
        entry['Comentarios'] = extract_price(block) # SOLO EL PRECIO EN COMENTARIOS
        
        # Valores por defecto y limpieza final
        if not entry['Teléfono']: entry['Teléfono'] = "+00 000 000 000"
        if entry['Empresa']:
            domain = entry['Empresa'].lower().split(' ')[0].replace('.', '')
            entry['Email'] = f"info@{domain}.com"
        entry['Tipo de Camión'] = "Lona"
        
        all_data.append(entry)

    return pd.DataFrame(all_data, columns=columnas)

# Interfaz Streamlit
st.set_page_config(page_title="Extractor Timocom Final", page_icon="🚛")
st.title("🚛 Extractor Limpio para Maptruck")
st.markdown("Ahora los comentarios **solo incluyen el precio**.")

input_text = st.text_area("Pega los chats aquí...", height=450)

if st.button("🚀 Generar Excel Limpio"):
    if input_text:
        df = process_final_clean(input_text)
        if not df.empty:
            st.success(f"¡Procesado! Encontrados {len(df)} transportistas.")
            st.dataframe(df)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Sheet1')
            st.download_button(label="📥 Descargar Excel para Maptruck", data=output.getvalue(), file_name="IMPORTACION_MAPTRUCK.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.error("No se encontró ninguna ruta válida.")
    else:
        st.warning("Pega el texto del chat para comenzar.")
    
 
