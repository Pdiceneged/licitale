import streamlit as st
import base64
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta
from dateutil import parser
import pytz

st.set_page_config(
    page_title="Prazo Licitações",
    page_icon="📝"
)
@st.cache_data()
def get_img_as_base64(file):
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

img = get_img_as_base64("fundocontrat5.png")

page_bg_img = f"""
<style>
[data-testid="stAppViewContainer"] > .main {{
    background-image: url("data:fundoesg4k/png;base64,{img}");
    background-size: 100%;
    background-position: top left;
    background-repeat: no-repeat;
    background-attachment: fixed;
}}

[data-testid="stHeader"] {{
    background: rgba(0,0,0,0);
}}

[data-testid="stToolbar"] {{
    right: 2rem;
}}
</style>
"""

st.markdown(page_bg_img, unsafe_allow_html=True)


secrets = st.secrets["google"]

API_KEY = secrets["api_key"]
SPREADSHEET_ID = secrets["spreadsheet_id"]
RANGE_NAME = "licit!A1:E"


def get_google_sheets_service(api_key):
    service = build("sheets", "v4", developerKey=api_key)
    return service


def read_sheet_data(sheet_service, spreadsheet_id, range):
    try:
        result = sheet_service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range).execute()
        values = result.get("values", [])
        return values
    except HttpError as e:
        st.error(f"Erro ao acessar a planilha: {e}")
        return None


def time_until_due(uf, número, cliente, prazo, observações):
    try:
        if not prazo:
            return None

        # Specify the exact format of the date string
        date_format = "%d/%m/%Y %H:%M:%S"

        # Try parsing with datetime.strptime or dateutil.parser
        try:
            due_datetime = datetime.strptime(prazo, date_format).replace(tzinfo=pytz.timezone('America/Sao_Paulo'))
        except ValueError:
            try:
                due_datetime = parser.parse(prazo).replace(tzinfo=pytz.timezone('America/Sao_Paulo'))
            except ValueError:
                return None  # Retorne None em caso de formato de data inválido

        # Ensure due_datetime is not in the past
        if due_datetime >= datetime.now(pytz.timezone('America/Sao_Paulo')):
            # Calculate the time remaining until the due date
            difference = due_datetime - datetime.now(pytz.timezone('America/Sao_Paulo'))

            # Calculate days, hours, and minutes using // and %
            days_remaining = difference.days
            hours_remaining = difference.seconds // 3600
            minutes_remaining = (difference.seconds % 3600) // 60

            return days_remaining, hours_remaining, minutes_remaining

        return None

    except (ValueError, TypeError) as e:
        st.error(f"Erro ao calcular tempo restante para {uf} {número}: {e}")
        return None


def display_alert(days, hours, minutes):
    if days is not None and days == 0 and hours <= 24:
        st.error("🚨 Urgente! Restam menos de 24h para o fim prazo!")
    elif days is not None and days < 3 and (hours * 3600 + minutes * 60) <= 23 * 3600:
        st.warning("⚠️ Atenção! Menos de 3 dias restantes para o fim do prazo!")


def format_time_until_due(days, hours, minutes):
    formatted_days = f"{days} dias, " if days > 0 else ""
    formatted_hours = f"{hours} horas, " if hours > 0 else ""
    formatted_minutes = f"{minutes} minutos" if minutes > 0 else ""

    return f"{formatted_days}{formatted_hours}{formatted_minutes}"

st.image("kkk.png", width=350, use_column_width=False)
st.title("Licitações")

sheet_service = get_google_sheets_service(API_KEY)

data = read_sheet_data(sheet_service, SPREADSHEET_ID, RANGE_NAME)

if data:
    st.subheader("Atenção aos prazos!")

    for row in data:
        if len(row) >= 5:
            uf, número, cliente, prazo, observações = row[:5]

            result = time_until_due(uf, número, cliente, prazo, observações)
            if result is not None:
                days, hours, minutes = result

                st.write("---")
                st.write(f"**UF:** {uf}")
                st.write(f"**Número:** {número}")
                st.write(f"**Cliente:** {cliente}")
                st.write(f"**Prazo:** {prazo}")
                st.write(f"**Observações:** {observações}")

                time_until_due_str = format_time_until_due(days, hours, minutes)
                st.write(f"**Tempo até o vencimento:** {time_until_due_str}")

                # Display alerts based on the remaining time gh
                display_alert(days, hours, minutes)

    st.markdown("---")
    st.markdown("Desenvolvido por [PedroFS](https://linktr.ee/Pedrofsf)")
