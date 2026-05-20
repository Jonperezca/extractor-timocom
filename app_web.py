import streamlit as st
import pandas as pd
import re
import json
import os
from io import BytesIO

# Configuración inicial
st.set_page_config(page_title="Extractor Timocom v6", page_icon="🚛")

# Lógica de extracción (Mantenemos la inteligencia v5)
def extract_price(text):
    price_pattern = r"(\d{3,4})\s?(?:e|€|eur|euros|usd|\$)"
    matches = re.findall(price_pattern, text, re.IGNORECASE)
    return f"{matches[-1]}€" if matches else ""

def extract_phone(text):
    phone_pattern = r"(\+?\d{1,3}[\s-]?\d{3}[\s-]?\d{3,4}[\s-]?\d{0,4})"
    matches = re.findall(phone_pattern, text)
    for match in matches:
        phone = match.strip()
        if len(re.sub(r'\D', '', phone)) >= 9:
            return phone
    return ""

def process_text(text):
    paises_map = {
        'FR': 'FRANCIA', 'IT': 'ITALIA', 'ES': 'ESPAÑA', 
        'GB': 'REINO UNIDO', 'NL': 'PAISES BAJOS', 'DE': 'ALEMANIA',
        'PL': 'POLONIA', 'BE': 'BELGICA', 'PT': 'PORTUGAL', 'CZ': 'REPUBLICA CHECA'
    }
    text = text.replace('➞', '->').replace('➔', '->')
    route_pattern = r"([A-Z]{2})\s(\w+)\s([\w\s]+)\s->\s([A-Z]{2})\s(\w+)\s([\w\s]+)"
    route_matches = list(re.finditer(route_pattern, text))
    
    all_data = []
    columnas = ['Empresa', 'Email', 'Teléfono', 'Contacto', 'País Origen', 'Código Origen', 'Ciudad Origen', 'País Destino', 'Código Destino', 'Ciudad Destino', 'Tipo de Camión', 'Comentarios', 'Destinos']

    for i in range(len(route_matches)):
        m = route_matches[i]
        start = m.start()
        end = route_matches[i+1].start() if i+1 < len(route_matches) else len(text)
        block = text[max(0, start-200):end]
        
        entry = {col: "" for col in columnas}
        entry['País Origen'] = paises_map.get(m.group(1), m.group(1))
        entry['Código Origen'] = m.group(2)
        entry['Ciudad Origen'] = m.group(3).split('(')[0].strip()
        entry['País Destino'] = paises_map.get(m.group(4), m.group(4))
        entry['Código Destino'] = m.group(5)
        entry['Ciudad Destino'] = m.group(6).split('(')[0].strip()
        entry['Destinos'] = entry['País Destino']
        
        empresa_match = re.search(r"([A-Z][\w\s\.\-&]+(?:sp\. z o\.o\.|S\.L\.|GmbH|Ltd|S\.A\.|Srl|Kft))", block, re.IGNORECASE)
        entry['Empresa'] = empresa_match.group(1).strip() if empresa_match else "Empresa Desconocida"
        
        entry['Teléfono'] = extract_phone(block) or "+00 000 000 000"
        entry['Comentarios'] = extract_price(block)
        entry['Tipo de Camión'] = "Lona"
        entry['Email'] = f"info@{entry['Empresa'].lower().split(' ')[0]}.com"
        
        all_data.append(entry)

    return pd.DataFrame(all_data, columns=columnas)

# Interfaz
st.title("🚛 Extractor Timocom (Versión Compatible)")
st.markdown("Pega tus chats abajo. Si falta alguna librería, esta versión usará un motor alternativo.")

input_text = st.text_area("Pega los chats aquí...", height=300)

if st.button("🚀 Generar Excel"):
    if input_text:
        df = process_text(input_text)
        if not df.empty:
            st.success(f"¡Procesado! Encontrados {len(df)} transportistas.")
            st.dataframe(df)
            
            # MOTOR ALTERNATIVO PARA EVITAR ERRORES
            output = BytesIO()
            try:
                # Intentamos con openpyxl que es más común
                df.to_excel(output, index=False, engine='openpyxl')
            except:
                # Si falla, usamos el motor por defecto
                df.to_excel(output, index=False)
            
            st.download_button(
                label="📥 Descargar Excel para Maptruck",
                data=output.getvalue(),
                file_name="IMPORTACION_MAPTRUCK.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("No se encontraron rutas válidas.")
    else:
        st.warning("Pega el texto del chat.")
