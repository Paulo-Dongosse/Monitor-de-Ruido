from fpdf import FPDF
import sqlite3

def gerar_relatorio():
    conn = sqlite3.connect("backend/leituras.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leituras ORDER BY id DESC LIMIT 50")
    leituras = cursor.fetchall()
    conn.close()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Relatório de Ruído - Últimas Leituras", ln=True, align="C")

    for l in leituras:
        pdf.cell(200, 8, txt=f"Sensor: {l[1]} | Horário: {l[2]} | Nível: {l[3]:.2f} dB", ln=True)

    pdf.output("relatorio_ruido.pdf")
    print("📄 Relatório gerado com sucesso: relatorio_ruido.pdf")

if __name__ == "__main__":
    gerar_relatorio()
