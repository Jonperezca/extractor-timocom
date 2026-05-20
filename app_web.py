import streamlit as st
import pandas as pd
import re
import json
import os
from io import BytesIO

# Archivo para guardar la "memoria" de los transportistas
DB_FILE = "transportistas_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f)

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

def process_with_memory(text, db):
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
        return pd.DataFrame(), db

    all_data = []
    columnas = ['Empresa', 'Email', 'Teléfono', 'Contacto', 'País Origen', 'Código Origen', 'Ciudad Origen', 'País Destino', 'Código Destino', 'Ciudad Destino', 'Tipo de Camión', 'Comentarios', 'Destinos']

    for i in range(len(route_matches)):
        start = route_matches[i].start()
        end = route_matches[i+1].start() if i+1 < len(route_matches) else len(text)
        block = text[max(0, start-200):end]
        
        entry = {col: "" for col in columnas}
        
        # 1. Ruta
        m = route_matches[i]
        entry['País Origen'] = paises_map.get(m.group(1), m.group(1))
        entry['Código Origen'] = m.group(2)
        entry['Ciudad Origen'] = m.group(3).split('(')[0].strip()
        entry['País Destino'] = paises_map.get(m.group(4), m.group(4))
        entry['Código Destino'] = m.group(5)
        entry['Ciudad Destino'] = m.group(6).split('(')[0].strip()
        entry['Destinos'] = entry['País Destino']
        
        # 2. Empresa
        empresa_match = re.search(r"([A-Z][\w\s\.\-&]+(?:sp\. z o\.o\.|S\.L\.|GmbH|Ltd|S\.A\.|Srl|Kft))", block, re.IGNORECASE)
        empresa_name = empresa_match.group(1).strip() if empresa_match else ""
        if not empresa_name:
            lines = [l.strip() for l in block.split('\n') if l.strip()]
            if lines: empresa_name = lines[0]
        
        entry['Empresa'] = empresa_name
        
        # 3. Contacto
        contacto_match = re.search(r"(?:Habla:|Contacto:)\s?([\w\s]+)", block, re.IGNORECASE)
        entry['Contacto'] = contacto_match.group(1).strip() if contacto_match else ""
        if not entry['Contacto']:
            names = re.findall(r"\b([A-Z][a-z]+\s[A-Z][a-z]+)\b", block)
            if names: entry['Contacto'] = names[0]

        # 4. Teléfono y Email (Intentar extraer del texto)
        entry['Teléfono'] = extract_phone(block)
        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", block)
        entry['Email'] = email_match.group(0) if email_match else ""
        
        # 5. MEMORIA: Si no hay datos, buscar en la DB. Si hay datos nuevos, guardar en la DB.
        if empresa_name:
            if not entry['Email'] or not entry['Teléfono'] or not entry['Contacto']:
                # Recuperar de memoria
                if empresa_name in db:
                    mem = db[empresa_name]
                    if not entry['Email']: entry['Email'] = mem.get('Email', "")
                    if not entry['Teléfono']: entry['Teléfono'] = mem.get('Teléfono', "")
                    if not entry['Contacto']: entry['Contacto'] = mem.get('Contacto', "")
            
            # Actualizar memoria con datos nuevos
            if empresa_name not in db: db[empresa_name] = {}
            if entry['Email']: db[empresa_name]['Email'] = entry['Email']
            if entry['Teléfono']: db[empresa_name]['Teléfono'] = entry['Teléfono']
            if entry['Contacto']: db[empresa_name]['Contacto'] = entry['Contacto']

        # 6. Precio y Comentarios
        entry['Comentarios'] = extract_price(block)
        
        # Valores por defecto
        if not entry['Teléfono']: entry['Teléfono'] = "+00 000 000 000"
        if not entry['Email'] and entry['Empresa']:
            domain = entry['Empresa'].lower().split(' ')[0].replace('.', '')
            entry['Email'] = f"info@{domain}.com"
        entry['Tipo de Camión'] = "Lona"
        
        all_data.append(entry)

    return pd.DataFrame(all_data, columns=columnas), db

# Interfaz Streamlit
st.set_page_config(page_title="Robot Inteligente v5", page_icon="🧠")
st.title("🧠 Robot con Memoria para Timocom")
st.markdown("Este robot 'aprende' los contactos. Cuanto más lo uses, menos datos tendrás que pegar.")

db = load_db()

input_text = st.text_area("Pega los chats aquí...", height=400)

if st.button("🚀 Procesar y Aprender"):
    if input_text:
        df, updated_db = process_with_memory(input_text, db)
        if not df.empty:
            save_db(updated_db)
            st.success(f"¡Procesado! Encontrados {len(df)} transportistas. Memoria actualizada.")
            st.dataframe(df)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Sheet1')
            st.download_button(label="📥 Descargar Excel para Maptruck", data=output.getvalue(), file_name="IMPORTACION_MAPTRUCK.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.error("No se encontró ninguna ruta válida.")
    else:
        st.warning("Pega el texto del chat para comenzar.")

if st.sidebar.checkbox("Ver memoria del robot"):
    st.sidebar.json(db)
