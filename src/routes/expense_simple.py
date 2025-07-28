from flask import Blueprint, request, jsonify, make_response
from src.models.expense import db, Expense
from datetime import datetime
import csv
import io

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

@expense_bp.route('/expenses/export-csv', methods=['GET'])
def export_csv():
    """تصدير المصاريف إلى CSV"""
    try:
        expenses = Expense.query.order_by(Expense.date_created.desc()).all()
        
        if not expenses:
            return jsonify({'success': False, 'error': 'لا توجد مصاريف للتصدير'}), 400
        
        # إنشاء ملف CSV في الذاكرة
        output = io.StringIO()
        writer = csv.writer(output)
        
        # كتابة العناوين
        writer.writerow(['الرقم', 'وصف المصروف', 'المبلغ (ريال)', 'التاريخ'])
        
        # كتابة البيانات
        for i, expense in enumerate(expenses, 1):
            date_str = expense.date_created.strftime('%Y-%m-%d %H:%M') if expense.date_created else ''
            writer.writerow([i, expense.description, f"{expense.amount:.2f}", date_str])
            
        # إضافة صف المجموع
        total = sum(expense.amount for expense in expenses)
        writer.writerow(['', 'المجموع الكلي', f"{total:.2f}", ''])
        
        # إنشاء الاستجابة
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=expense_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@expense_bp.route('/expenses/export-html', methods=['GET'])
def export_html():
    """تصدير المصاريف إلى HTML للطباعة"""
    try:
        expenses = Expense.query.order_by(Expense.date_created.desc()).all()
        
        if not expenses:
            return jsonify({'success': False, 'error': 'لا توجد مصاريف للتصدير'}), 400
        
        # إنشاء HTML
        html_content = f"""
        <!DOCTYPE html>
        <html lang="ar" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <title>تقرير المصاريف</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .date {{ color: #666; margin-bottom: 20px; }}
                table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: center; }}
                th {{ background-color: #f5f5f5; font-weight: bold; }}
                .total-row {{ background-color: #e8f5e8; font-weight: bold; }}
                @media print {{ body {{ margin: 0; }} }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>تقرير المصاريف</h1>
                <div class="date">تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>الرقم</th>
                        <th>وصف المصروف</th>
                        <th>المبلغ (ريال)</th>
                        <th>التاريخ</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        # إضافة البيانات
        for i, expense in enumerate(expenses, 1):
            date_str = expense.date_created.strftime('%Y-%m-%d %H:%M') if expense.date_created else ''
            html_content += f"""
                    <tr>
                        <td>{i}</td>
                        <td>{expense.description}</td>
                        <td>{expense.amount:.2f}</td>
                        <td>{date_str}</td>
                    </tr>
            """
        
        # إضافة صف المجموع
        total = sum(expense.amount for expense in expenses)
        html_content += f"""
                    <tr class="total-row">
                        <td colspan="2">المجموع الكلي</td>
                        <td>{total:.2f}</td>
                        <td></td>
                    </tr>
                </tbody>
            </table>
            
            <script>
                window.onload = function() {{
                    window.print();
                }}
            </script>
        </body>
        </html>
        """
        
        response = make_response(html_content)
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        
        return response
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

