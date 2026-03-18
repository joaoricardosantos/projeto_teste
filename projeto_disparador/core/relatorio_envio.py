"""
relatorio_envio.py
Gera PDF de relatório de envio de mensagens usando ReportLab,
com o mesmo estilo visual dos relatórios de inadimplentes.
"""
from datetime import datetime
from io import BytesIO
from decimal import Decimal


def _fmt_phone(phone: str) -> str:
    """Formata telefone para exibição amigável."""
    import re
    if not phone:
        return "—"
    # Pega só o primeiro número se houver múltiplos
    phone = phone.split(";")[0].split(",")[0].strip()
    digits = re.sub(r"\D", "", phone)
    while digits.startswith("55") and len(digits) > 13:
        digits = digits[2:]
    if digits.startswith("55") and len(digits) > 11:
        digits = digits[2:]
    if len(digits) == 10:
        digits = digits[:2] + "9" + digits[2:]
    if len(digits) == 11:
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
    return phone


def gerar_pdf_relatorio_envio(
    condominio_nome: str,
    template_nome: str,
    enviados: list,
    falhas: list,
    sem_numero: list,
) -> bytes:
    """
    Gera PDF com relatório de envio.

    enviados: lista de dicts {"unidade", "nome", "telefone"}
    falhas:   lista de dicts {"phone", "error"}
    sem_numero: lista de dicts {"unidade", "nome", "motivo"}
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph,
        Spacer, HRFlowable,
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    import os

    COR_VERDE     = colors.HexColor("#006837")
    COR_VERDE_ESC = colors.HexColor("#004225")
    COR_ZEBRA     = colors.HexColor("#F2F2F2")
    COR_BRANCO    = colors.white
    COR_TEXTO     = colors.HexColor("#1A1A1A")
    COR_CINZA     = colors.HexColor("#666666")
    COR_ERRO      = colors.HexColor("#D32F2F")
    COR_ERRO_CLARO= colors.HexColor("#FFEBEE")
    COR_OK        = colors.HexColor("#006837")
    COR_OK_CLARO  = colors.HexColor("#E8F5E9")

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    style_title = ParagraphStyle(
        "titulo", fontSize=16, textColor=COR_VERDE,
        fontName="Helvetica-Bold", alignment=TA_LEFT, spaceAfter=4,
    )
    style_sub = ParagraphStyle(
        "sub", fontSize=9, textColor=COR_CINZA,
        fontName="Helvetica", alignment=TA_LEFT, spaceAfter=2,
    )
    style_cell = ParagraphStyle(
        "cell", fontSize=8, textColor=COR_TEXTO,
        fontName="Helvetica", leading=10,
    )
    style_cell_bold = ParagraphStyle(
        "cell_bold", fontSize=8, textColor=COR_BRANCO,
        fontName="Helvetica-Bold", leading=10, alignment=TA_CENTER,
    )
    style_section = ParagraphStyle(
        "section", fontSize=10, textColor=COR_VERDE,
        fontName="Helvetica-Bold", spaceAfter=4, spaceBefore=10,
    )

    def p(txt, style=None):
        return Paragraph(str(txt) if txt else "", style or style_cell)

    story = []

    # ── Cabeçalho ────────────────────────────────────────────────────────────
    _logo_path = os.path.join(os.path.dirname(__file__), "logo_pratika.png")
    if os.path.exists(_logo_path):
        from reportlab.platypus import Image as RLImage
        logo_img = RLImage(_logo_path, width=3.5*cm, height=1.8*cm)
    else:
        logo_img = Paragraph("", style_sub)

    header_table = Table(
        [[logo_img, Paragraph("Relatório de Envio de Mensagens", style_title)]],
        colWidths=[4*cm, None],
    )
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)

    data_hora = datetime.now().strftime("%d/%m/%Y %H:%M")
    story.append(Paragraph(
        f"Condomínio: {condominio_nome}  |  Template: {template_nome or 'Mensagem padrão'}  |  Gerado em: {data_hora}",
        style_sub
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=COR_VERDE, spaceAfter=10))

    # ── Resumo ────────────────────────────────────────────────────────────────
    resumo_data = [
        [
            Paragraph("✅ Enviados com sucesso", ParagraphStyle("r", fontSize=9, fontName="Helvetica-Bold", textColor=COR_BRANCO, alignment=TA_CENTER)),
            Paragraph("❌ Falhas no envio", ParagraphStyle("r", fontSize=9, fontName="Helvetica-Bold", textColor=COR_BRANCO, alignment=TA_CENTER)),
            Paragraph("📵 Sem número", ParagraphStyle("r", fontSize=9, fontName="Helvetica-Bold", textColor=COR_BRANCO, alignment=TA_CENTER)),
        ],
        [
            Paragraph(str(len(enviados)), ParagraphStyle("rv", fontSize=18, fontName="Helvetica-Bold", textColor=COR_BRANCO, alignment=TA_CENTER)),
            Paragraph(str(len(falhas)), ParagraphStyle("rv", fontSize=18, fontName="Helvetica-Bold", textColor=COR_BRANCO, alignment=TA_CENTER)),
            Paragraph(str(len(sem_numero)), ParagraphStyle("rv", fontSize=18, fontName="Helvetica-Bold", textColor=COR_BRANCO, alignment=TA_CENTER)),
        ],
    ]

    resumo_table = Table(resumo_data, colWidths=[6*cm, 6*cm, 6*cm])
    resumo_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), COR_VERDE),
        ("BACKGROUND", (1, 0), (1, -1), COR_ERRO),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#F57C00")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, COR_BRANCO),
        ("ROUNDEDCORNERS", [4]),
    ]))
    story.append(resumo_table)
    story.append(Spacer(1, 0.5*cm))

    # ── Tabela de enviados ────────────────────────────────────────────────────
    if enviados:
        story.append(Paragraph("✅ Enviados com sucesso", style_section))
        cab_env = [
            p("Unidade", style_cell_bold),
            p("Nome", style_cell_bold),
            p("Telefone", style_cell_bold),
        ]
        dados_env = [cab_env]
        for i, e in enumerate(enviados):
            dados_env.append([
                p(e.get("unidade", "")),
                p(e.get("nome", "")),
                p(_fmt_phone(e.get("telefone", ""))),
            ])

        zebra = []
        for idx in range(len(enviados)):
            cor = COR_BRANCO if idx % 2 == 0 else COR_ZEBRA
            zebra.append(("BACKGROUND", (0, idx+1), (-1, idx+1), cor))

        t_env = Table(dados_env, colWidths=[4*cm, 9*cm, 5*cm])
        t_env.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COR_VERDE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ] + zebra))
        story.append(t_env)
        story.append(Spacer(1, 0.5*cm))

    # ── Tabela de sem número ──────────────────────────────────────────────────
    if sem_numero:
        story.append(Paragraph("📵 Sem número cadastrado", style_section))
        cab_sn = [
            p("Unidade", style_cell_bold),
            p("Nome", style_cell_bold),
            p("Motivo", style_cell_bold),
        ]
        dados_sn = [cab_sn]
        for i, s in enumerate(sem_numero):
            dados_sn.append([
                p(s.get("unidade", "")),
                p(s.get("nome", "")),
                p("Sem número cadastrado"),
            ])

        zebra_sn = []
        for idx in range(len(sem_numero)):
            cor = colors.HexColor("#FFF8E1") if idx % 2 == 0 else colors.HexColor("#FFF3CD")
            zebra_sn.append(("BACKGROUND", (0, idx+1), (-1, idx+1), cor))

        t_sn = Table(dados_sn, colWidths=[4*cm, 9*cm, 5*cm])
        t_sn.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F57C00")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ] + zebra_sn))
        story.append(t_sn)
        story.append(Spacer(1, 0.5*cm))

    # ── Tabela de falhas ──────────────────────────────────────────────────────
    if falhas:
        story.append(Paragraph("❌ Falhas no envio", style_section))
        cab_f = [
            p("Telefone", style_cell_bold),
            p("Motivo", style_cell_bold),
        ]
        dados_f = [cab_f]
        for i, f in enumerate(falhas):
            erro = str(f.get("error", ""))
            if "instance does not exist" in erro.lower() or "instance" in erro.lower():
                motivo = "WhatsApp nao conectado"
            elif "400" in erro or "404" in erro:
                motivo = "Numero sem WhatsApp"
            elif "500" in erro:
                motivo = "Erro interno"
            elif "timeout" in erro.lower():
                motivo = "Tempo de conexao esgotado"
            else:
                motivo = "Nao foi possivel enviar"
            dados_f.append([
                p(f.get("unidade", "-")),
                p(f.get("nome", "-")),
                p(_fmt_phone(f.get("phone", ""))),
                p(motivo),
            ])

        zebra_f = []
        for idx in range(len(falhas)):
            cor = COR_ERRO_CLARO if idx % 2 == 0 else colors.HexColor("#FFCDD2")
            zebra_f.append(("BACKGROUND", (0, idx+1), (-1, idx+1), cor))

        t_f = Table(dados_f, colWidths=[3*cm, 5*cm, 4*cm, 6*cm])
        t_f.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COR_ERRO),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ] + zebra_f))
        story.append(t_f)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()