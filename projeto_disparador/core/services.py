import csv
import requests
from io import StringIO
from django.conf import settings

def send_message_to_condo(condo_name: str, contact: str, debt_amount: str):
    payload = {
        "condominium": condo_name,
        "contact": contact,
        "message": f"Prezado condomínio {condo_name}, consta um débito de {debt_amount}."
    }
    headers = {
        "Authorization": f"Bearer {settings.EXTERNAL_MESSAGING_API_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.post(
        settings.EXTERNAL_MESSAGING_API_URL, 
        json=payload, 
        headers=headers, 
        timeout=10
    )
    response.raise_for_status()

def process_defaulters_spreadsheet(file_obj):
    decoded_file = file_obj.read().decode('utf-8')
    csv_reader = csv.DictReader(StringIO(decoded_file))
    
    success_count = 0
    error_count = 0
    
    for row in csv_reader:
        try:
            condo_name = row.get('condominio')
            contact = row.get('contato')
            debt_amount = row.get('valor_debito')
            
            if condo_name and contact and debt_amount:
                send_message_to_condo(condo_name, contact, debt_amount)
                success_count += 1
            else:
                error_count += 1
        except Exception:
            error_count += 1
            
    return {"success": success_count, "errors": error_count}