from flask import Flask, render_template, request, send_file
from fpdf import FPDF
from datetime import datetime
from num2words import num2words
import re
import io

app = Flask(__name__)

# --- Funções do Recibo ---
def formatar_documento(doc):
    numeros = re.sub(r'\D', '', doc)
    if len(numeros) == 11:
        return f"{numeros[:3]}.{numeros[3:6]}.{numeros[6:9]}-{numeros[9:]}"
    elif len(numeros) == 14:
        return f"{numeros[:2]}.{numeros[2:5]}.{numeros[5:8]}/{numeros[8:12]}-{numeros[12:]}"
    return doc.upper()

class ReciboPDF(FPDF):
    def criar_grade(self):
        self.set_line_width(0.3)
        self.set_draw_color(0, 0, 0)
        self.rect(10, 10, 190, 120) 
        self.line(10, 45, 200, 45)  
        self.line(10, 75, 200, 75)  
        self.line(10, 90, 200, 90)  
        self.line(10, 105, 200, 105) 
        self.line(60, 10, 60, 45)   
        self.line(160, 10, 160, 45) 
        self.line(160, 20, 200, 20) 
        self.line(160, 32, 200, 32) 
        self.line(180, 10, 180, 20) 

# --- Rotas do Site ---

# 1. Rota principal: Mostra a página HTML
@app.route('/')
def index():
    return render_template('index.html')

# 2. Rota de geração: Recebe os dados do HTML e devolve o PDF
@app.route('/gerar', methods=['POST'])
def gerar():
    # Pegando os dados que o usuário digitou no site
    numero = request.form.get('numero')
    nome_cliente = request.form.get('nome_cliente')
    cpf_cliente = formatar_documento(request.form.get('cpf_cnpj'))
    end_cliente = request.form.get('end_cliente')
    valor_input = request.form.get('valor').replace(',', '.')
    motivo = request.form.get('motivo')
    
    valor_float = float(valor_input)
    extenso = num2words(valor_float, lang='pt_BR', to='currency').upper()
    valor_br = f"{valor_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    data_atual = datetime.now().strftime('%d/%m/%Y')

    # Criando o PDF (Em memória)
    pdf = ReciboPDF(orientation='L', unit='mm', format='A5')
    pdf.set_margins(0, 0, 0)
    pdf.set_auto_page_break(False, margin=0)
    pdf.add_page()
    pdf.criar_grade()

    # --- CABEÇALHO ---
    try:
        # ATENÇÃO: Agora a logo fica na pasta static!
        pdf.image("static/logo.png", 12, 18, 45) 
    except:
        pass

    pdf.set_text_color(20, 60, 120) 
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_xy(60, 13)
    pdf.cell(100, 8, "LOC TENDAS", align="C") # <----------------------------------------------------------- Nome da empresa
    
    pdf.set_text_color(0, 0, 0) 
    pdf.set_font("Helvetica", "", 7)
    pdf.set_xy(60, 20)
    pdf.cell(100, 5, "LOCAÇÃO DE TENDAS PARA EVENTOS EM GERAL", align="C")
    pdf.set_xy(60, 24)
    pdf.cell(100, 5, "CNPJ: 28.419.663/0001-46", align="C") # <--------------------------------------------- CNPJ da empresa
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_xy(60, 30)
    pdf.cell(100, 5, "99 99901-9770 / 99 98211-0487", align="C") # <---------------------------------------- Telefone da empresa 
    pdf.set_font("Helvetica", "", 7)
    pdf.set_xy(60, 38)
    pdf.cell(100, 5, "TRAV. CAPITÃO BORBA, 135 - BAIRRO POTOSÍ - BALSAS - MARANHÃO", align="C")

    pdf.set_font("Helvetica", "B", 8)
    pdf.set_xy(160, 12)
    pdf.cell(20, 8, "Nº", align="C")
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_xy(180, 12)
    pdf.cell(20, 8, numero, align="C")
    pdf.set_text_color(20, 60, 120) 
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_xy(160, 22)
    pdf.cell(40, 10, "RECIBO", align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_xy(162, 34)
    pdf.cell(10, 10, "R$")
    pdf.set_xy(170, 34)
    pdf.cell(28, 10, valor_br, align="R")

    # --- CORPO ---
    def desenhar_campo(label, valor, y):
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(80, 80, 80)
        pdf.set_xy(12, y)
        pdf.cell(30, 5, label)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(0, 0, 0)
        pdf.set_xy(40, y)
        pdf.cell(150, 5, valor)

    desenhar_campo("Recebi(emos) de:", nome_cliente.upper(), 50)
    desenhar_campo("CPF/CNPJ:", cpf_cliente, 58)
    desenhar_campo("Endereço:", end_cliente.upper(), 66)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_xy(12, 78)
    pdf.cell(35, 5, "Quantia supra de R$:")
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, f"#{extenso}#")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_xy(12, 93)
    pdf.cell(20, 5, "Referente a:")
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, f"#{motivo.upper()}#")

    # --- RODAPÉ ---
    pdf.set_font("Helvetica", "", 9)
    pdf.set_xy(12, 107)
    pdf.cell(0, 5, "para clareza firmo(amos) o presente.")
    pdf.set_xy(25, 120)
    pdf.cell(40, 5, data_atual, align="C")
    pdf.line(25, 125, 65, 125) 
    pdf.set_font("Helvetica", "", 7)
    pdf.set_xy(25, 125)
    pdf.cell(40, 4, "DATA", align="C")
    pdf.line(100, 125, 180, 125) 
    pdf.set_xy(100, 125)
    pdf.cell(80, 4, "Assinatura ou Carimbo.", align="C")

    # Finaliza e devolve pro navegador
    pdf_bytes = pdf.output()
    buffer = io.BytesIO(pdf_bytes)
    buffer.seek(0)
    
    return send_file(
        buffer, 
        as_attachment=True, 
        download_name=f"recibo_{numero}.pdf", 
        mimetype='application/pdf'
    )

if __name__ == '__main__':
    app.run(debug=True)