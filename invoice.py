import os
import pandas as pd
from dotenv import load_dotenv
import openai
from fpdf import FPDF

# Load API key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Define the function schema for OpenAI function calling
function_descriptions = [
    {
        "name": "generate_invoice",
        "description": "Generate structured invoice data from CSV row",
        "parameters": {
            "type": "object",
            "properties": {
                "invoice_number": {"type": "string"},
                "customer_name": {"type": "string"},
                "customer_address": {"type": "string"},
                "invoice_date": {"type": "string"},
                "due_date": {"type": "string"},
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "description": {"type": "string"},
                            "quantity": {"type": "number"},
                            "unit_price": {"type": "number"},
                            "total": {"type": "number"}
                        }
                    }
                },
                "total_amount": {"type": "number"}
            },
            "required": ["invoice_number", "customer_name", "items", "total_amount"]
        }
    }
]

# Read CSV file
df = pd.read_csv("invoices.csv")

def call_openai_function(row):
    # Prepare a prompt from the row data
    prompt = f"""
    You are an AI assistant. Given the following invoice data, generate a structured invoice in JSON matching the function schema.
    Data: {row.to_dict()}
    """

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        functions=function_descriptions,
        function_call={"name": "generate_invoice"}
    )
    # Extract function call arguments (JSON)
    args = response.choices[0].message["function_call"]["arguments"]
    import json
    return json.loads(args)

def generate_pdf(invoice, output_dir="output_invoices"):
    os.makedirs(output_dir, exist_ok=True)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Invoice #{invoice['invoice_number']}", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Customer: {invoice['customer_name']}", ln=True)
    pdf.cell(200, 10, txt=f"Address: {invoice['customer_address']}", ln=True)
    pdf.cell(200, 10, txt=f"Date: {invoice['invoice_date']}", ln=True)
    pdf.cell(200, 10, txt=f"Due Date: {invoice['due_date']}", ln=True)
    pdf.ln(10)
    pdf.cell(40, 10, "Description", 1)
    pdf.cell(30, 10, "Qty", 1)
    pdf.cell(40, 10, "Unit Price", 1)
    pdf.cell(40, 10, "Total", 1)
    pdf.ln()
    for item in invoice['items']:
        pdf.cell(40, 10, item['description'], 1)
        pdf.cell(30, 10, str(item['quantity']), 1)
        pdf.cell(40, 10, f"${item['unit_price']:.2f}", 1)
        pdf.cell(40, 10, f"${item['total']:.2f}", 1)
        pdf.ln()
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Total Amount: ${invoice['total_amount']:.2f}", ln=True, align='R')
    pdf.output(f"{output_dir}/invoice_{invoice['invoice_number']}.pdf")

# Process each row in the CSV
for idx, row in df.iterrows():
    invoice_struct = call_openai_function(row)
    generate_pdf(invoice_struct)
    print(f"Invoice {invoice_struct['invoice_number']} generated.")

