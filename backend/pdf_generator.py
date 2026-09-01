import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

class MedicalReportPDFGenerator:
    @staticmethod
    def generate_pdf(output_path, patient_name, condition, confidence, prediction_latency, api_latency, timestamp):
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title Style
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=22,
            textColor=colors.HexColor("#1A365D"),
            spaceAfter=12
        )
        
        story.append(Paragraph("Cloud Medical AI Diagnosis Report", title_style))
        story.append(Paragraph("Serverless AWS Lambda Diagnostic Summary", styles['SubTitle']))
        story.append(Spacer(1, 15))
        
        # Patient & Diagnostic Details Table
        data = [
            ["Patient Name:", patient_name],
            ["Diagnosis Timestamp:", str(timestamp)],
            ["Predicted Condition:", condition],
            ["AI Confidence Score:", f"{confidence * 100:.1f}%"],
            ["ML Prediction Latency:", f"{prediction_latency} ms (Target: 30-50 ms)"],
            ["Total API Response Time:", f"{api_latency} ms (Target: 100-200 ms)"],
            ["Infrastructure:", "AWS Lambda Serverless FaaS + SQLite"]
        ]
        
        table = Table(data, colWidths=[160, 300])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#EDF2F7')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2D3748')),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 20))
        story.append(Paragraph("Notice: This report was generated automatically by the Serverless Cloud Medical AI System.", styles['Italic']))
        
        doc.build(story)
        return output_path
