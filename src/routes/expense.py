from flask import Blueprint, request, jsonify
from src.models.expense import db, Expense
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime
import io
import base64

expense_bp = Blueprint('expense', __name__)

@expense_bp.route('/expenses', methods=['GET'])
def get_expenses():
    """الحصول على جميع المصاريف"""
    try:
        expenses = Expense.query.order_by(Expense.date_created.desc()).all()
        return jsonify({
            'success': True,
            'expenses': [expense.to_dict() for expense in expenses],
            'total': sum(expense.amount for expense in expenses)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@expense_bp.route('/expenses', methods=['POST'])
def add_expense():
    """إضافة مصروف جديد"""
    try:
        data = request.get_json()
        
        if not data or 'description' not in data or 'amount' not in data:
            return jsonify({'success': False, 'error': 'البيانات المطلوبة مفقودة'}), 400
        
        description = data['description'].strip()
        amount = float(data['amount'])
        
        if not description:
            return jsonify({'success': False, 'error': 'وصف المصروف مطلوب'}), 400
        
        if amount < 0:
            return jsonify({'success': False, 'error': 'المبلغ يجب أن يكون موجباً'}), 400
        
        expense = Expense(description=description, amount=amount)
        db.session.add(expense)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم إضافة المصروف بنجاح',
            'expense': expense.to_dict()
        })
        
    except ValueError:
        return jsonify({'success': False, 'error': 'المبلغ يجب أن يكون رقماً صحيحاً'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@expense_bp.route('/expenses/<int:expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    """حذف مصروف"""
    try:
        expense = Expense.query.get(expense_id)
        if not expense:
            return jsonify({'success': False, 'error': 'المصروف غير موجود'}), 404
        
        db.session.delete(expense)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'تم حذف المصروف بنجاح'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@expense_bp.route('/expenses/clear', methods=['DELETE'])
def clear_all_expenses():
    """حذف جميع المصاريف"""
    try:
        Expense.query.delete()
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'تم حذف جميع المصاريف بنجاح'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@expense_bp.route('/expenses/export-pdf', methods=['GET'])
def export_pdf():
    """تصدير المصاريف إلى PDF"""
    try:
        expenses = Expense.query.order_by(Expense.date_created.desc()).all()
        
        if not expenses:
            return jsonify({'success': False, 'error': 'لا توجد مصاريف للتصدير'}), 400
        
        # إنشاء ملف PDF في الذاكرة
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # الأنماط
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1,  # وسط
            fontName='Helvetica-Bold'
        )
        
        # العنوان
        title = Paragraph("تقرير المصاريف", title_style)
        story.append(title)
        story.append(Spacer(1, 20))
        
        # معلومات التقرير
        info = Paragraph(f"تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal'])
        story.append(info)
        story.append(Spacer(1, 20))
        
        # بيانات الجدول
        data = [['الرقم', 'وصف المصروف', 'المبلغ (ريال)', 'التاريخ']]
        
        for i, expense in enumerate(expenses, 1):
            date_str = expense.date_created.strftime('%Y-%m-%d') if expense.date_created else ''
            data.append([str(i), expense.description, f"{expense.amount:.2f}", date_str])
            
        # إضافة صف المجموع
        total = sum(expense.amount for expense in expenses)
        data.append(['', '', f"{total:.2f}", 'المجموع الكلي'])
        
        # إنشاء الجدول
        table = Table(data, colWidths=[0.8*inch, 3*inch, 1.2*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        
        # بناء PDF
        doc.build(story)
        
        # تحويل إلى base64
        buffer.seek(0)
        pdf_data = buffer.getvalue()
        buffer.close()
        
        pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
        
        return jsonify({
            'success': True,
            'pdf_data': pdf_base64,
            'filename': f'expense_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

