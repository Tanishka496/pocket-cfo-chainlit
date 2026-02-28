"""
Export utilities for generating CSV and PDF reports.

This module provides functions to export transaction data to CSV and PDF formats.
"""

import csv
import io
from datetime import date, datetime
from decimal import Decimal
from typing import List, Dict, Any, Tuple
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors


def generate_csv_content(transactions: List[Dict[str, Any]]) -> bytes:
    """
    Generate CSV content from transactions.
    
    Args:
        transactions: List of transaction dictionaries
        
    Returns:
        Bytes containing CSV data
    """
    output = io.StringIO()
    
    fieldnames = ["Date", "Description", "Category", "Type", "Amount"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    
    writer.writeheader()
    
    if transactions:
        for transaction in transactions:
            writer.writerow({
                "Date": transaction["transaction_date"],
                "Description": transaction["description"],
                "Category": transaction["category"],
                "Type": transaction["type"].capitalize(),
                "Amount": f"${float(transaction['amount']):.2f}",
            })
    
    output.seek(0)
    return output.getvalue().encode('utf-8')


def calculate_summary(transactions: List[Dict[str, Any]]) -> Tuple[Decimal, Decimal, Decimal]:
    """
    Calculate total income, expense, and net profit.
    
    Args:
        transactions: List of transaction dictionaries
        
    Returns:
        Tuple of (total_income, total_expense, net_profit)
    """
    total_income = Decimal("0")
    total_expense = Decimal("0")
    
    for transaction in transactions:
        amount = Decimal(str(transaction["amount"]))
        if transaction["type"] == "income":
            total_income += amount
        else:
            total_expense += amount
    
    net_profit = total_income - total_expense
    
    return total_income, total_expense, net_profit


def generate_pdf_content(
    transactions: List[Dict[str, Any]],
    filename: str = "transaction_report.pdf"
) -> bytes:
    """
    Generate PDF content from transactions.
    
    Args:
        transactions: List of transaction dictionaries
        filename: Output filename
        
    Returns:
        Bytes containing PDF data
    """
    # Create PDF buffer
    pdf_buffer = io.BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=letter,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch,
    )
    
    # Container for PDF elements
    elements = []
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=30,
        alignment=1,  # Center alignment
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#374151'),
        spaceAfter=15,
        spaceBefore=15,
    )
    
    # Title
    title = Paragraph("Transaction Report", title_style)
    elements.append(title)
    
    # Generate date
    date_text = Paragraph(
        f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
        styles['Normal']
    )
    elements.append(date_text)
    elements.append(Spacer(1, 0.3*inch))
    
    if transactions:
        # Table data with header
        table_data = [["Date", "Description", "Category", "Type", "Amount"]]
        
        for transaction in transactions:
            table_data.append([
                str(transaction["transaction_date"]),
                transaction["description"][:30] + ("..." if len(transaction["description"]) > 30 else ""),
                transaction["category"],
                transaction["type"].capitalize(),
                f"${float(transaction['amount']):.2f}",
            ])
        
        # Create table
        table = Table(table_data, colWidths=[1.2*inch, 2*inch, 1.2*inch, 0.8*inch, 1*inch])
        
        # Apply table style
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f2937')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')]),
            ('RIGHTPADDING', (4, 0), (4, -1), 10),
        ]))
        
        elements.append(table)
    else:
        elements.append(Paragraph("No transactions found.", styles['Normal']))
    
    elements.append(Spacer(1, 0.3*inch))
    
    # Summary section
    total_income, total_expense, net_profit = calculate_summary(transactions)
    
    summary_heading = Paragraph("Summary", heading_style)
    elements.append(summary_heading)
    
    summary_data = [
        ["Total Income:", f"${float(total_income):.2f}"],
        ["Total Expense:", f"${float(total_expense):.2f}"],
        ["Net Profit:", f"${float(net_profit):.2f}"],
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 1.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0fdf4')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('RIGHTPADDING', (1, 0), (1, -1), 10),
    ]))
    
    elements.append(summary_table)
    
    # Build PDF
    doc.build(elements)
    
    # Get PDF content
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()


def get_csv_filename() -> str:
    """
    Generate a timestamped CSV filename.
    
    Returns:
        Filename string in format: transactions_YYYYMMDD_HHMMSS.csv
    """
    now = datetime.now()
    return f"transactions_{now.strftime('%Y%m%d_%H%M%S')}.csv"


def get_pdf_filename() -> str:
    """
    Generate a timestamped PDF filename.
    
    Returns:
        Filename string in format: transaction_report_YYYYMMDD_HHMMSS.pdf
    """
    now = datetime.now()
    return f"transaction_report_{now.strftime('%Y%m%d_%H%M%S')}.pdf"
