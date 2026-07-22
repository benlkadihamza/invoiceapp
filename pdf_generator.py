from fpdf import FPDF
from datetime import datetime
from collections import defaultdict
import os

MONTHS_FR = [
    '', 'Janvier', 'Fevrier', 'Mars', 'Avril', 'Mai', 'Juin',
    'Juillet', 'Aout', 'Septembre', 'Octobre', 'Novembre', 'Decembre'
]

COLOR_PRIMARY = (13, 110, 253)
COLOR_SUCCESS = (25, 135, 84)
COLOR_DANGER = (220, 53, 69)
COLOR_HEADER_BG = (33, 37, 41)
COLOR_HEADER_FG = (255, 255, 255)
COLOR_ROW_ALT = (245, 245, 250)
COLOR_INCOME_BG = (212, 237, 218)
COLOR_EXPENSE_BG = (248, 215, 218)
COLOR_LIGHT_GRAY = (230, 230, 230)
COLOR_DARK = (33, 37, 41)
COLOR_WHITE = (255, 255, 255)
COLOR_SUMMARY_BG = (240, 244, 248)

LOGO_MAX_HEIGHT = 20
LOGO_X = 15
LOGO_Y = 10


def _safe(text):
    if text is None:
        return ''
    replacements = {
        '\u00e9': 'e', '\u00e8': 'e', '\u00ea': 'e', '\u00eb': 'e',
        '\u00e0': 'a', '\u00e2': 'a', '\u00e4': 'a',
        '\u00f4': 'o', '\u00f6': 'o',
        '\u00f9': 'u', '\u00fb': 'u', '\u00fc': 'u',
        '\u00ee': 'i', '\u00ef': 'i',
        '\u00e7': 'c', '\u00cb': 'E',
        '\u00c9': 'E', '\u00c8': 'E',
        '\u00d4': 'O', '\u00d6': 'O',
        '\u00dc': 'U', '\u00d9': 'U',
        '\u00c0': 'A', '\u00c2': 'A',
        '\u00b2': '2',
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode('latin-1', 'replace').decode('latin-1')


def _fmt(val):
    if val is None:
        return '0.00'
    return f'{val:,.2f}'


def _get_logo_path():
    try:
        from flask import current_app
        return os.path.join(current_app.root_path, 'static', 'img', 'logo.png')
    except RuntimeError:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'img', 'logo.png')


class FinanceReportPDF(FPDF):
    def __init__(self, orientation='P', title='Rapport Financier', month=None, year=None):
        super().__init__(orientation, 'mm', 'A4')
        self.report_title = title
        self.report_month = month
        self.report_year = year
        self._logo_path = _get_logo_path()
        self._logo_w = 0
        self._logo_h = 0
        self._load_logo()
        self.set_auto_page_break(auto=True, margin=25)
        self.set_margins(15, 15, 15)

    def _load_logo(self):
        if os.path.isfile(self._logo_path):
            try:
                img_w, img_h = self._get_image_dimensions(self._logo_path)
                if img_h > 0:
                    scale = LOGO_MAX_HEIGHT / img_h
                    self._logo_w = img_w * scale
                    self._logo_h = LOGO_MAX_HEIGHT
                else:
                    self._logo_w = 0
                    self._logo_h = 0
            except Exception:
                self._logo_w = 0
                self._logo_h = 0
        else:
            self._logo_w = 0
            self._logo_h = 0

    @staticmethod
    def _get_image_dimensions(path):
        try:
            from PIL import Image
            with Image.open(path) as img:
                return img.size
        except ImportError:
            pass
        try:
            import struct
            with open(path, 'rb') as f:
                header = f.read(32)
                if header[:8] == b'\x89PNG\r\n\x1a\n':
                    f.seek(16)
                    w, h = struct.unpack('>II', f.read(8))
                    return w, h
                if header[:2] == b'\xff\xd8':
                    f.seek(0)
                    data = f.read()
                    idx = 2
                    while idx < len(data) - 1:
                        if data[idx] == 0xFF:
                            marker = data[idx + 1]
                            if marker in (0xC0, 0xC1, 0xC2):
                                h = struct.unpack('>H', data[idx + 5:idx + 7])[0]
                                w = struct.unpack('>H', data[idx + 7:idx + 9])[0]
                                return w, h
                            if marker == 0xD9:
                                break
                            length = struct.unpack('>H', data[idx + 2:idx + 4])[0]
                            idx += 2 + length
                        else:
                            idx += 1
        except Exception:
            pass
        return 1, 1

    def header(self):
        if self._logo_w > 0 and self._logo_h > 0:
            try:
                self.image(self._logo_path, x=LOGO_X, y=LOGO_Y, h=self._logo_h)
            except Exception:
                pass

    def footer(self):
        self.set_y(-20)
        self.set_font('Helvetica', 'I', 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, _safe('COCINA ESPAÑOLA - MDF Art'), align='L')
        self.cell(0, 5, f'Page {self.page_no()}/{{nb}}', align='R', new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(200, 200, 200)
        self.line(15, self.get_y(), 195, self.get_y())

    def _draw_header_block(self):
        title_x = LOGO_X
        if self._logo_w > 0:
            title_x = LOGO_X + self._logo_w + 5

        self.set_xy(title_x, LOGO_Y + 2)
        self.set_font('Helvetica', 'B', 18)
        self.set_text_color(*COLOR_DARK)
        self.cell(0, 10, _safe(self.report_title), new_x="LMARGIN", new_y="NEXT")

        self.set_xy(title_x, LOGO_Y + 13)
        self.set_font('Helvetica', '', 10)
        self.set_text_color(100, 100, 100)
        if self.report_month and self.report_year:
            subtitle = f'{MONTHS_FR[self.report_month]} {self.report_year}'
        elif self.report_year:
            subtitle = f'Annee {self.report_year}'
        else:
            subtitle = 'Toutes les transactions'
        self.cell(0, 6, _safe(subtitle), new_x="LMARGIN", new_y="NEXT")

        self.set_xy(title_x, LOGO_Y + 20)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(130, 130, 130)
        self.cell(0, 5, _safe(f'Genere le {datetime.now().strftime("%d/%m/%Y a %H:%M")}'), new_x="LMARGIN", new_y="NEXT")

        header_bottom = LOGO_Y + max(self._logo_h, 0) + 12
        self.set_y(header_bottom)
        self.set_draw_color(*COLOR_PRIMARY)
        self.set_line_width(0.8)
        self.line(15, self.get_y(), 195, self.get_y())
        self.ln(5)

    def _draw_summary_cards(self, total_income, total_expense, net, closing_balance=None):
        self.set_font('Helvetica', 'B', 9)
        y_start = self.get_y()

        card_w = 42
        gap = 3
        cards = [
            ('Total Revenus', _fmt(total_income) + ' DH', COLOR_SUCCESS),
            ('Total Depenses', _fmt(total_expense) + ' DH', COLOR_DANGER),
            ('Net', _fmt(net) + ' DH', COLOR_PRIMARY if net >= 0 else COLOR_DANGER),
        ]
        if closing_balance is not None:
            cards.append(('Solde Cloture', _fmt(closing_balance) + ' DH', COLOR_PRIMARY))

        total_w = len(cards) * card_w + (len(cards) - 1) * gap
        x_start = 15 + (180 - total_w) / 2

        for i, (label, value, color) in enumerate(cards):
            x = x_start + i * (card_w + gap)
            self.set_fill_color(*COLOR_SUMMARY_BG)
            self.rect(x, y_start, card_w, 20, style='F')
            self.set_fill_color(*color)
            self.rect(x, y_start, card_w, 3, style='F')

            self.set_xy(x, y_start + 5)
            self.set_font('Helvetica', '', 7)
            self.set_text_color(120, 120, 120)
            self.cell(card_w, 4, _safe(label), align='C')

            self.set_xy(x, y_start + 10)
            self.set_font('Helvetica', 'B', 9)
            self.set_text_color(*color)
            self.cell(card_w, 7, _safe(value), align='C')

        self.set_y(y_start + 26)
        self.set_text_color(0, 0, 0)

    def _draw_table_header(self, columns, col_widths):
        self.set_font('Helvetica', 'B', 7)
        self.set_fill_color(*COLOR_HEADER_BG)
        self.set_text_color(*COLOR_HEADER_FG)
        h = 8
        for i, (col, w) in enumerate(zip(columns, col_widths)):
            align = 'R' if i >= len(columns) - 3 else 'L'
            if i == 0:
                align = 'C'
            self.cell(w, h, _safe(col), border=0, fill=True, align=align)
        self.ln(h)
        self.set_text_color(0, 0, 0)

    def _check_page_break(self, needed=12):
        if self.get_y() + needed > self.h - 25:
            self.add_page()
            return True
        return False

    def _draw_transaction_row(self, t, col_widths, idx, running_balance=None):
        self._check_page_break(12)
        row_h = 7
        if t.notes:
            row_h = 10

        is_expense = t.expense > 0
        if is_expense:
            self.set_fill_color(*COLOR_EXPENSE_BG)
        else:
            self.set_fill_color(*COLOR_INCOME_BG)

        self.set_font('Helvetica', '', 7)
        y_before = self.get_y()

        values = [
            t.formatted_date,
            (t.person.name if t.person else '-')[:16],
            t.description[:28],
            _fmt(t.income) if t.income > 0 else '-',
            _fmt(t.expense) if t.expense > 0 else '-',
            (_fmt(t.net) if t.net >= 0 else _fmt(t.net)),
            _fmt(running_balance) if running_balance is not None else '-',
        ]

        aligns = ['C', 'L', 'L', 'R', 'R', 'R', 'R']

        for i, (val, w) in enumerate(zip(values, col_widths)):
            self.set_xy(15 + sum(col_widths[:i]), y_before)
            self.set_font('Helvetica', '', 7)
            if i == 5:
                self.set_font('Helvetica', 'B', 7)
                if t.net >= 0:
                    self.set_text_color(*COLOR_SUCCESS)
                else:
                    self.set_text_color(*COLOR_DANGER)
            elif i == 6 and running_balance is not None:
                self.set_font('Helvetica', 'B', 7)
                if running_balance >= 0:
                    self.set_text_color(*COLOR_SUCCESS)
                else:
                    self.set_text_color(*COLOR_DANGER)
            elif i == 3 and t.income > 0:
                self.set_text_color(*COLOR_SUCCESS)
            elif i == 4 and t.expense > 0:
                self.set_text_color(*COLOR_DANGER)
            else:
                self.set_text_color(0, 0, 0)
            self.cell(w, row_h, _safe(val), border=0, fill=True, align=aligns[i])

        if t.notes:
            self.set_xy(15, y_before + 5)
            self.set_font('Helvetica', 'I', 5)
            self.set_text_color(100, 100, 100)
            note_text = t.notes[:80]
            self.cell(sum(col_widths), 4, _safe(note_text), border=0, fill=True, align='L')

        self.set_y(y_before + row_h)
        self.set_text_color(0, 0, 0)

    def _draw_daily_totals(self, transactions, col_widths):
        self._check_page_break(20)
        daily = defaultdict(lambda: {'income': 0.0, 'expense': 0.0})
        for t in transactions:
            daily[t.date]['income'] += t.income
            daily[t.date]['expense'] += t.expense

        self.ln(3)
        self.set_font('Helvetica', 'B', 9)
        self.set_text_color(*COLOR_DARK)
        self.cell(0, 6, _safe('Totaux Quotidiens'), new_x="LMARGIN", new_y="NEXT")

        self._draw_table_header(
            ['Date', 'Revenus (DH)', 'Depenses (DH)', 'Net (DH)'],
            [45, 40, 40, 40]
        )

        self.set_font('Helvetica', '', 7)
        total_i = 0.0
        total_e = 0.0
        for d in sorted(daily.keys()):
            self._check_page_break(8)
            data = daily[d]
            net = data['income'] - data['expense']
            total_i += data['income']
            total_e += data['expense']

            if net >= 0:
                self.set_fill_color(*COLOR_INCOME_BG)
            else:
                self.set_fill_color(*COLOR_EXPENSE_BG)

            vals = [
                d.strftime('%d/%m/%Y'),
                _fmt(data['income']),
                _fmt(data['expense']),
                _fmt(net),
            ]
            aligns = ['C', 'R', 'R', 'R']
            for i, (v, w) in enumerate(zip(vals, [45, 40, 40, 40])):
                self.set_font('Helvetica', 'B' if i == 3 else '', 7)
                if i == 3:
                    self.set_text_color(*COLOR_SUCCESS if net >= 0 else COLOR_DANGER)
                else:
                    self.set_text_color(0, 0, 0)
                self.cell(w, 7, _safe(v), border=0, fill=True, align=aligns[i])
            self.ln(7)

        self.set_fill_color(*COLOR_HEADER_BG)
        self.set_text_color(*COLOR_HEADER_FG)
        self.set_font('Helvetica', 'B', 7)
        self.cell(45, 7, 'TOTAUX', border=0, fill=True, align='L')
        self.cell(40, 7, _fmt(total_i), border=0, fill=True, align='R')
        self.cell(40, 7, _fmt(total_e), border=0, fill=True, align='R')
        self.set_text_color(*COLOR_WHITE)
        self.cell(40, 7, _fmt(total_i - total_e), border=0, fill=True, align='R')
        self.ln(7)
        self.set_text_color(0, 0, 0)

    def _draw_person_summary(self, transactions):
        persons = defaultdict(lambda: {'income': 0.0, 'expense': 0.0, 'count': 0})
        for t in transactions:
            pname = t.person.name if t.person else 'Inconnu'
            persons[pname]['income'] += t.income
            persons[pname]['expense'] += t.expense
            persons[pname]['count'] += 1

        if not persons:
            return

        self._check_page_break(30)
        self.ln(3)
        self.set_font('Helvetica', 'B', 9)
        self.set_text_color(*COLOR_DARK)
        self.cell(0, 6, _safe('Totaux par Personne'), new_x="LMARGIN", new_y="NEXT")

        self._draw_table_header(
            ['Personne', 'Transactions', 'Revenus (DH)', 'Depenses (DH)', 'Net (DH)'],
            [40, 25, 35, 35, 35]
        )

        self.set_font('Helvetica', '', 7)
        for name, data in sorted(persons.items()):
            self._check_page_break(8)
            net = data['income'] - data['expense']
            self.set_fill_color(*COLOR_ROW_ALT if list(persons.keys()).index(name) % 2 == 0 else COLOR_WHITE)

            vals = [
                name[:22],
                str(data['count']),
                _fmt(data['income']),
                _fmt(data['expense']),
                _fmt(net),
            ]
            aligns = ['L', 'C', 'R', 'R', 'R']
            for i, (v, w) in enumerate(zip(vals, [40, 25, 35, 35, 35])):
                self.set_font('Helvetica', 'B' if i == 4 else '', 7)
                if i == 4:
                    self.set_text_color(*COLOR_SUCCESS if net >= 0 else COLOR_DANGER)
                else:
                    self.set_text_color(0, 0, 0)
                self.cell(w, 7, _safe(v), border=0, fill=True, align=aligns[i])
            self.ln(7)

    def _draw_final_totals(self, total_income, total_expense, balance):
        self._check_page_break(25)
        self.ln(3)
        self.set_draw_color(*COLOR_PRIMARY)
        self.set_line_width(0.5)
        self.line(15, self.get_y(), 195, self.get_y())
        self.ln(3)

        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(*COLOR_DARK)
        self.cell(0, 8, _safe('TOTAUX FINAUX'), new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

        y = self.get_y()
        items = [
            ('Total Revenus:', _fmt(total_income) + ' DH', COLOR_SUCCESS),
            ('Total Depenses:', _fmt(total_expense) + ' DH', COLOR_DANGER),
            ('Benefice Net:', _fmt(total_income - total_expense) + ' DH', COLOR_SUCCESS if total_income - total_expense >= 0 else COLOR_DANGER),
            ('Solde Final:', _fmt(balance) + ' DH', COLOR_PRIMARY),
        ]

        for i, (label, value, color) in enumerate(items):
            self.set_xy(15, y + i * 8)
            self.set_font('Helvetica', '', 9)
            self.set_text_color(80, 80, 80)
            self.cell(50, 7, _safe(label), align='L')
            self.set_font('Helvetica', 'B', 10)
            self.set_text_color(*color)
            self.cell(0, 7, _safe(value), align='R')

        self.set_y(y + len(items) * 8 + 5)
        self.set_text_color(0, 0, 0)


def generate_monthly_pdf(year, month):
    from models import Transaction
    from sqlalchemy import extract

    transactions = Transaction.query.filter(
        extract('month', Transaction.date) == month,
        extract('year', Transaction.date) == year
    ).order_by(Transaction.date.asc(), Transaction.id.asc()).all()

    all_txns = Transaction.query.order_by(Transaction.date.asc(), Transaction.id.asc()).all()
    running = 0.0
    closing_balance = 0.0
    for t in all_txns:
        running += t.income - t.expense
        if t.date.year == year and t.date.month == month:
            closing_balance = running

    total_income = sum(t.income for t in transactions)
    total_expense = sum(t.expense for t in transactions)

    pdf = FinanceReportPDF(title='Rapport Mensuel', month=month, year=year)
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf._draw_header_block()
    pdf._draw_summary_cards(total_income, total_expense, total_income - total_expense, closing_balance)

    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_text_color(*COLOR_DARK)
    pdf.cell(0, 6, _safe('Details des Transactions'), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    columns = ['Date', 'Personne', 'Description', 'Revenu', 'Depense', 'Net', 'Mode']
    col_widths = [20, 24, 38, 24, 24, 24, 22]

    if transactions:
        pdf._draw_table_header(columns, col_widths)
        for idx, t in enumerate(transactions):
            pdf._draw_transaction_row(t, col_widths, idx)

        pdf.ln(2)
        pdf._draw_table_header(['', '', 'TOTAUX', _fmt(total_income), _fmt(total_expense), _fmt(total_income - total_expense), ''], col_widths)
    else:
        pdf.set_font('Helvetica', 'I', 9)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 10, _safe('Aucune transaction pour cette periode'), align='C', new_x="LMARGIN", new_y="NEXT")

    pdf._draw_daily_totals(transactions, col_widths)
    pdf._draw_person_summary(transactions)
    pdf._draw_final_totals(total_income, total_expense, closing_balance)

    return pdf.output()


def generate_daily_pdf(year, month, day):
    from models import Transaction
    from datetime import date as d

    selected_date = d(year, month, day)
    transactions = Transaction.query.filter(
        Transaction.date == selected_date
    ).order_by(Transaction.date.asc(), Transaction.id.asc()).all()

    total_income = sum(t.income for t in transactions)
    total_expense = sum(t.expense for t in transactions)

    pdf = FinanceReportPDF(title='Rapport Quotidien')
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf._draw_header_block()

    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(*COLOR_DARK)
    pdf.cell(0, 6, _safe(f'Journal du {selected_date.strftime("%d/%m/%Y")}'), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf._draw_summary_cards(total_income, total_expense, total_income - total_expense)

    columns = ['Date', 'Personne', 'Description', 'Revenu', 'Depense', 'Net', 'Solde']
    col_widths = [20, 24, 38, 24, 24, 24, 22]

    if transactions:
        running_balances = []
        balance = 0.0
        for t in transactions:
            balance += t.net
            running_balances.append(balance)

        pdf._draw_table_header(columns, col_widths)
        for idx, t in enumerate(transactions):
            pdf._draw_transaction_row(t, col_widths, idx, running_balance=running_balances[idx])
    else:
        pdf.set_font('Helvetica', 'I', 9)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 10, _safe('Aucune transaction ce jour'), align='C', new_x="LMARGIN", new_y="NEXT")

    pdf._draw_final_totals(total_income, total_expense, total_income - total_expense)

    return pdf.output()


def generate_weekly_pdf(start_date, end_date):
    from models import Transaction

    transactions = Transaction.query.filter(
        Transaction.date >= start_date,
        Transaction.date <= end_date
    ).order_by(Transaction.date.asc(), Transaction.id.asc()).all()

    total_income = sum(t.income for t in transactions)
    total_expense = sum(t.expense for t in transactions)

    pdf = FinanceReportPDF(title='Rapport Hebdomadaire')
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf._draw_header_block()

    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(*COLOR_DARK)
    pdf.cell(0, 6, _safe(f'Du {start_date.strftime("%d/%m/%Y")} au {end_date.strftime("%d/%m/%Y")}'), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf._draw_summary_cards(total_income, total_expense, total_income - total_expense)

    columns = ['Date', 'Personne', 'Description', 'Revenu', 'Depense', 'Net', 'Mode']
    col_widths = [20, 24, 38, 24, 24, 24, 22]

    if transactions:
        pdf._draw_table_header(columns, col_widths)
        for idx, t in enumerate(transactions):
            pdf._draw_transaction_row(t, col_widths, idx)
    else:
        pdf.set_font('Helvetica', 'I', 9)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 10, _safe('Aucune transaction cette semaine'), align='C', new_x="LMARGIN", new_y="NEXT")

    pdf._draw_daily_totals(transactions, col_widths)
    pdf._draw_person_summary(transactions)
    pdf._draw_final_totals(total_income, total_expense, total_income - total_expense)

    return pdf.output()


def generate_yearly_pdf(year):
    from models import Transaction
    from sqlalchemy import extract

    transactions = Transaction.query.filter(
        extract('year', Transaction.date) == year
    ).order_by(Transaction.date.asc(), Transaction.id.asc()).all()

    total_income = sum(t.income for t in transactions)
    total_expense = sum(t.expense for t in transactions)

    pdf = FinanceReportPDF(title='Rapport Annuel', year=year)
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf._draw_header_block()

    pdf._draw_summary_cards(total_income, total_expense, total_income - total_expense)

    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_text_color(*COLOR_DARK)
    pdf.cell(0, 6, _safe('Resume Mensuel'), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    self_check = ['Mois', 'Revenus (DH)', 'Depenses (DH)', 'Net (DH)']
    pdf._draw_table_header(self_check, [45, 38, 38, 38])

    for m in range(1, 13):
        pdf._check_page_break(8)
        mi = sum(t.income for t in transactions if t.date.month == m)
        me = sum(t.expense for t in transactions if t.date.month == m)
        net = mi - me

        if net >= 0:
            pdf.set_fill_color(*COLOR_INCOME_BG)
        else:
            pdf.set_fill_color(*COLOR_EXPENSE_BG)

        vals = [MONTHS_FR[m], _fmt(mi), _fmt(me), _fmt(net)]
        aligns = ['L', 'R', 'R', 'R']
        for i, (v, w) in enumerate(zip(vals, [45, 38, 38, 38])):
            pdf.set_font('Helvetica', 'B' if i == 3 else '', 7)
            if i == 3:
                pdf.set_text_color(*COLOR_SUCCESS if net >= 0 else COLOR_DANGER)
            else:
                pdf.set_text_color(0, 0, 0)
            pdf.cell(w, 7, _safe(v), border=0, fill=True, align=aligns[i])
        pdf.ln(7)

    pdf._draw_daily_totals(transactions, [45, 38, 38, 38])
    pdf._draw_person_summary(transactions)
    pdf._draw_final_totals(total_income, total_expense, total_income - total_expense)

    return pdf.output()


def generate_person_pdf(year, month):
    from models import Transaction
    from sqlalchemy import extract

    transactions = Transaction.query.filter(
        extract('month', Transaction.date) == month,
        extract('year', Transaction.date) == year
    ).order_by(Transaction.date.asc(), Transaction.id.asc()).all()

    total_income = sum(t.income for t in transactions)
    total_expense = sum(t.expense for t in transactions)

    pdf = FinanceReportPDF(title='Rapport par Personne', month=month, year=year)
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf._draw_header_block()
    pdf._draw_summary_cards(total_income, total_expense, total_income - total_expense)

    pdf._draw_person_summary(transactions)

    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_text_color(*COLOR_DARK)
    pdf.ln(3)
    pdf.cell(0, 6, _safe('Transactions Detaillees'), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    columns = ['Date', 'Personne', 'Description', 'Revenu', 'Depense', 'Net', 'Mode']
    col_widths = [20, 24, 38, 24, 24, 24, 22]

    if transactions:
        pdf._draw_table_header(columns, col_widths)
        for idx, t in enumerate(transactions):
            pdf._draw_transaction_row(t, col_widths, idx)

    pdf._draw_final_totals(total_income, total_expense, total_income - total_expense)

    return pdf.output()


def generate_full_pdf():
    from models import Transaction

    transactions = Transaction.query.order_by(
        Transaction.date.asc(), Transaction.id.asc()
    ).all()

    total_income = sum(t.income for t in transactions)
    total_expense = sum(t.expense for t in transactions)

    pdf = FinanceReportPDF(title='Rapport Financier Complet')
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf._draw_header_block()
    pdf._draw_summary_cards(total_income, total_expense, total_income - total_expense)

    columns = ['Date', 'Personne', 'Description', 'Revenu', 'Depense', 'Net', 'Mode']
    col_widths = [20, 24, 38, 24, 24, 24, 22]

    if transactions:
        pdf._draw_table_header(columns, col_widths)
        for idx, t in enumerate(transactions):
            pdf._draw_transaction_row(t, col_widths, idx)
    else:
        pdf.set_font('Helvetica', 'I', 9)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 10, _safe('Aucune transaction'), align='C', new_x="LMARGIN", new_y="NEXT")

    pdf._draw_person_summary(transactions)
    pdf._draw_final_totals(total_income, total_expense, total_income - total_expense)

    return pdf.output()
