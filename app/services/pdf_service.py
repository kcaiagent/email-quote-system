"""
PDF generation service for quotes
"""
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import os
from app.config import settings


class PDFService:
    """Service for generating PDF quotes"""
    
    @staticmethod
    def generate_quote_pdf(
        quote_number: str,
        customer_name: str,
        customer_email: str,
        product_name: str,
        length_inches: float,
        width_inches: float,
        area_sq_inches: float,
        unit_price: float,
        total_price: float,
        notes: str = None
    ) -> str:
        """
        Generate a PDF quote and return the file path
        
        Returns:
            str: Path to generated PDF file
        """
        # Create filename
        filename = f"quote_{quote_number}_{datetime.now().strftime('%Y%m%d')}.pdf"
        filepath = os.path.join(settings.PDF_OUTPUT_DIR, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        story = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#333333'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # Title
        story.append(Paragraph("KYOTO CUSTOM SURFACES", title_style))
        story.append(Paragraph("QUOTE", styles['Title']))
        story.append(Spacer(1, 0.2*inch))
        
        # Quote Information
        quote_info_data = [
            ['Quote Number:', quote_number],
            ['Date:', datetime.now().strftime('%B %d, %Y')],
            ['Valid Until:', (datetime.now() + timedelta(days=30)).strftime('%B %d, %Y')]
        ]
        
        quote_info_table = Table(quote_info_data, colWidths=[2*inch, 4*inch])
        quote_info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(quote_info_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Customer Information
        story.append(Paragraph("Bill To:", heading_style))
        customer_info = f"""
        <b>{customer_name}</b><br/>
        {customer_email}
        """
        story.append(Paragraph(customer_info, styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Product Details
        story.append(Paragraph("Product Details:", heading_style))
        product_data = [
            ['Description', 'Dimensions', 'Area', 'Unit Price', 'Total'],
            [
                product_name,
                f'{length_inches}" × {width_inches}"',
                f'{area_sq_inches:,.0f} sq in',
                f'${unit_price:.4f}/sq in',
                f'${total_price:,.2f}'
            ]
        ]
        
        product_table = Table(product_data, colWidths=[2*inch, 1.5*inch, 1*inch, 1.2*inch, 1*inch])
        product_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a5568')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(product_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Total
        total_data = [
            ['Subtotal:', f'${total_price:,.2f}'],
            ['Total:', f'<b>${total_price:,.2f}</b>']
        ]
        
        total_table = Table(total_data, colWidths=[4*inch, 2*inch])
        total_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica'),
            ('FONTNAME', (1, -1), (1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(total_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Notes
        if notes:
            story.append(Paragraph("Notes:", heading_style))
            story.append(Paragraph(notes, styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
        
        # Footer
        footer_text = """
        <i>Thank you for your business! This quote is valid for 30 days from the date of issue.</i>
        """
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(footer_text, styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        return filepath


# Singleton instance
pdf_service = PDFService()









