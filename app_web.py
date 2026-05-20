import streamlit as st
import pandas as pd
import re
from io import BytesIO

# Reutilizamos la lógica del robot
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
    blocks = re.split(r'(?=\b[A-Z]{2}\s\w+\s[\w\s]+->)', text)
    all_data = []
    columnas = ['Empresa', 'Email', 'Teléfono', 'Contacto', 'País Origen', 'Código Origen', 'Ciudad Origen', 'País Destino', 'Código Destino', 'Ciudad Destino', 'Tipo de Camión', 'Comentarios', 'Destinos']
    for block in blocks:
        if not block.strip(): continue
        entry = {col: "" for col in columnas}
        lines = block.strip().split('\n')
        ruta_match = re.search(r"([A-Z]{2})\s(\w+)\s([\w\s]+)\s->\s([A-Z]{2})\s(\w+)\s([\w\s]+)", lines[0])
        if ruta_match:
            entry['País Origen'] = paises_map.get(ruta_match.group(1), ruta_match.group(1))
            entry['Código Origen'] = ruta_match.group(2)
            entry['Ciudad Origen'] = ruta_match.group(3).strip()
            entry['País Destino'] = paises_map.get(ruta_match.group(4), ruta_match.group(4))
            entry['Código Destino'] = ruta_match.group(5)
            entry['Ciudad Destino'] = ruta_match.group(6).strip()
            entry['Destinos'] = entry['País Destino']
        if len(lines) > 1:
            ce_match = re.search(r"^([^\(]+)\s\(\"([^\"]+)\"", lines[1])
            if ce_match:
                entry['Contacto'] = ce_match.group(1).strip()
                entry['Empresa'] = ce_match.group(2).strip()
                entry['Email'] = f"info@{entry['Empresa'].lower().replace(' ', '')}.com"
        full_message = " ".join(lines[2:]) if len(lines) > 2 else ""
        if full_message:
            entry['Teléfono'] = extract_phone(full_message)
            precio = extract_price(full_message)
            entry['Comentarios'] = f"{precio} | Chat: {full_message}".strip(" | ")
        if not entry['Teléfono']: entry['Teléfono'] = "+00 000 000 000"
        entry['Tipo de Camión'] = "Lona"
        if entry['Empresa']: all_data.append(entry)
    return pd.DataFrame(all_data, columns=columnas)

# Interfaz Streamlit
st.set_page_config(page_title="Extractor Timocom -> Maptruck", page_icon="🚛")
st.title("🚛 Extractor de Chats Timocom")
st.markdown("Pega aquí todos los chats de Timocom que quieras procesar:")

input_text = st.text_area("Pega los chats aquí...", height=300)

if st.button("Generar Excel para Maptruck"):
    if input_text:
        df = process_multichat(input_text)
        if not df.empty:
            st.success(f"¡Se han procesado {len(df)} transportistas!")
            st.dataframe(df)
            
            # Convertir a Excel para descarga
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Sheet1')
            
            st.download_button(
                label="📥 Descargar Excel para Maptruck",
                data=output.getvalue(),
                file_name="IMPORTACION_MAPTRUCK.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("No se pudo extraer información. Verifica el formato del texto.")
    else:
        st.warning("Por favor, pega algún texto primero.")
