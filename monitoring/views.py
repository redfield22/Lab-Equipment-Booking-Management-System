from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, get_object_or_404, render
from django.views.generic import TemplateView, View, ListView, UpdateView
from django.core.exceptions import PermissionDenied
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy
from django.contrib import messages
from inventory.models import Department, Equipment
from bookings.models import Booking, DamageReport
from dashboard.models import Notification, ActivityLog, SystemSettings
from dashboard.forms import SystemSettingsForm
from accounts.models import CustomUser
import datetime
import calendar
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ReportLab imports
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

# ====================================================
# UTILITIES & CANVAS DECORATORS
# ====================================================

class NumberedCanvas(canvas.Canvas):
    """
    Subclass of canvas.Canvas that enables two-pass page counting.
    Allows injecting 'Page X of Y' in headers or footers dynamically.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8.5)
        self.setFillColor(colors.HexColor("#666666"))
        
        # Draw running header rule & text
        self.setStrokeColor(colors.HexColor("#e5e5e5"))
        self.setLineWidth(0.5)
        self.line(54, 735, 558, 735)
        self.drawString(54, 742, "Lab Inventory System - Official Report")
        
        # Draw running footer rule & page number
        self.line(54, 50, 558, 50)
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 35, page_text)
        self.drawString(54, 35, "Academic & Resource Audit Log - Confidential")
        self.restoreState()


def create_pdf_report(title, headers, col_widths, rows, total_count_label=None):
    """
    Helper function to generate professional ReportLab PDF reports.
    """
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{title.lower().replace(" ", "_")}_report.pdf"'
    
    settings_obj = SystemSettings.get_settings()
    
    doc = SimpleDocTemplate(
        response,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=80,
        bottomMargin=80
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1F4E78'),
        spaceAfter=15
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#555555'),
        spaceAfter=25
    )
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#333333')
    )
    
    story = []
    story.append(Paragraph(title, title_style))
    
    current_time = timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S')
    subtitle_text = f"<b>College Name:</b> {settings_obj.college_name}<br/>" \
                    f"<b>Lab Name:</b> {settings_obj.lab_name}<br/>" \
                    f"<b>Exported Date:</b> {current_time}<br/>"
    if total_count_label:
        subtitle_text += f"<b>Total Records:</b> {total_count_label}<br/>"
    
    story.append(Paragraph(subtitle_text, subtitle_style))
    
    # Structure table flowables
    table_data = []
    header_row = [Paragraph(h, table_header_style) for h in headers]
    table_data.append(header_row)
    
    for r in rows:
        row_cells = []
        for cell_val in r:
            row_cells.append(Paragraph(str(cell_val) if cell_val is not None else "", table_cell_style))
        table_data.append(row_cells)
        
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2F5597')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E5E5')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F9FAFB')])
    ]))
    
    story.append(t)
    doc.build(story, canvasmaker=NumberedCanvas)
    return response


def generate_excel_response(filename, headers, rows):
    """
    Helper function to generate professional formatted Excel sheets.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Report"
    
    ws.views.sheetView[0].showGridLines = True
    settings_obj = SystemSettings.get_settings()
    
    ws.merge_cells('A1:G1')
    ws['A1'] = f"{settings_obj.college_name} - {settings_obj.lab_name}"
    ws['A1'].font = Font(name='Arial', size=13, bold=True, color='FFFFFF')
    ws['A1'].fill = PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid')
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 36
    
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col_num, value=header)
        cell.font = Font(name='Arial', size=10, bold=True, color='FFFFFF')
        cell.fill = PatternFill(start_color='2F5597', end_color='2F5597', fill_type='solid')
        cell.alignment = Alignment(horizontal='left', vertical='center')
        cell.border = Border(
            bottom=Side(style='medium', color='000000'),
            top=Side(style='thin', color='BFBFBF'),
            left=Side(style='thin', color='BFBFBF'),
            right=Side(style='thin', color='BFBFBF')
        )
    ws.row_dimensions[3].height = 24
    
    thin_border = Border(
        bottom=Side(style='thin', color='E0E0E0'),
        top=Side(style='thin', color='E0E0E0'),
        left=Side(style='thin', color='E0E0E0'),
        right=Side(style='thin', color='E0E0E0')
    )
    
    for row_num, row_data in enumerate(rows, 4):
        ws.row_dimensions[row_num].height = 18
        for col_num, val in enumerate(row_data, 1):
            cell = ws.cell(row=row_num, column=col_num, value=val)
            cell.border = thin_border
            cell.font = Font(name='Arial', size=9)
            
            if isinstance(val, (datetime.date, datetime.datetime)):
                cell.number_format = 'YYYY-MM-DD'
            elif isinstance(val, (int, float)):
                cell.number_format = '#,##0'
                cell.alignment = Alignment(horizontal='right')
                
    last_col_letter = get_column_letter(len(headers))
    ws.auto_filter.ref = f"A3:{last_col_letter}{len(rows) + 3}"
    
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            if cell.row == 1:
                continue
            if cell.value:
                max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)
        
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response


# ====================================================
# REDIRECTS, ROLES, & DASHBOARD VIEWS
# ====================================================

class DashboardRedirectView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if request.user.role == 'admin':
            return redirect('dashboard:admin_dashboard')
        return redirect('dashboard:student_dashboard')


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'admin'

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("You are not authorized to access this page.")
        return super().handle_no_permission()


class StudentRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'student'

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("You are not authorized to access this page.")
        return super().handle_no_permission()


class AdminDashboardView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    template_name = 'dashboard/admin_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Stat cards (10 metrics)
        total_depts = Department.objects.count()
        total_equip = Equipment.objects.count()
        avail_equip = Equipment.objects.aggregate(total=Sum('available_quantity'))['total'] or 0
        booked_equip = Booking.objects.filter(status='Approved').aggregate(total=Sum('quantity'))['total'] or 0
        
        pending_requests = Booking.objects.filter(status='Pending').count()
        approved_bookings = Booking.objects.filter(status='Approved').count()
        rejected_bookings = Booking.objects.filter(status='Rejected').count()
        returned_bookings = Booking.objects.filter(status='Returned').count()
        
        low_stock = Equipment.objects.filter(available_quantity__lte=2).count()
        damage_reports = DamageReport.objects.count()

        recent_activities = ActivityLog.objects.order_by('-created_at')[:8]
        latest_bookings = Booking.objects.order_by('-created_at')[:5]
        latest_reports = DamageReport.objects.order_by('-created_at')[:5]
        low_stock_items = Equipment.objects.filter(available_quantity__lte=2).order_by('available_quantity')[:5]

        context['stats'] = {
            'total_departments': total_depts,
            'total_equipment': total_equip,
            'available_equipment': avail_equip,
            'booked_equipment': booked_equip,
            'pending_requests': pending_requests,
            'approved_bookings': approved_bookings,
            'rejected_bookings': rejected_bookings,
            'returned_bookings': returned_bookings,
            'low_stock_alerts': low_stock,
            'damage_reports': damage_reports,
        }
        context['recent_activities'] = recent_activities
        context['latest_bookings'] = latest_bookings
        context['latest_reports'] = latest_reports
        context['low_stock_items'] = low_stock_items
        return context


class StudentDashboardView(LoginRequiredMixin, StudentRequiredMixin, TemplateView):
    template_name = 'dashboard/student_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        active_bookings = Booking.objects.filter(student=user, status='Approved').count()
        pending_requests = Booking.objects.filter(student=user, status='Pending').count()
        returned_equipment = Booking.objects.filter(student=user, status='Returned').count()
        unread_notifications = Notification.objects.filter(user=user, is_read=False).count()
        my_reports = DamageReport.objects.filter(student=user).count()

        context['stats'] = {
            'active_bookings': active_bookings,
            'pending_requests': pending_requests,
            'returned_equipment': returned_equipment,
            'unread_notifications': unread_notifications,
            'my_reports': my_reports,
        }
        return context


# ====================================================
# GLOBAL SEARCH VIEW
# ====================================================

class GlobalSearchView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/global_search.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        q = self.request.GET.get('q', '').strip()
        context['q'] = q
        
        if q:
            # Querysets with select_related optimizing Database pulls
            equipments = Equipment.objects.filter(
                Q(equipment_name__icontains=q) |
                Q(equipment_code__icontains=q) |
                Q(description__icontains=q) |
                Q(location__icontains=q)
            ).select_related('department')
            
            departments = Department.objects.filter(
                Q(name__icontains=q) |
                Q(code__icontains=q) |
                Q(description__icontains=q)
            )
            
            if self.request.user.role == 'admin':
                students = CustomUser.objects.filter(
                    Q(full_name__icontains=q) |
                    Q(email__icontains=q) |
                    Q(phone_number__icontains=q)
                )
            else:
                students = CustomUser.objects.none()

            bookings_qs = Booking.objects.all() if self.request.user.role == 'admin' else Booking.objects.filter(student=self.request.user)
            bookings = bookings_qs.filter(
                Q(booking_id__icontains=q) |
                Q(purpose__icontains=q) |
                Q(equipment__equipment_name__icontains=q) |
                Q(student__full_name__icontains=q)
            ).select_related('equipment', 'student')

            reports_qs = DamageReport.objects.all() if self.request.user.role == 'admin' else DamageReport.objects.filter(student=self.request.user)
            damage_reports = reports_qs.filter(
                Q(report_id__icontains=q) |
                Q(title__icontains=q) |
                Q(description__icontains=q) |
                Q(equipment__equipment_name__icontains=q) |
                Q(student__full_name__icontains=q)
            ).select_related('equipment', 'student', 'booking')
        else:
            equipments = Equipment.objects.none()
            departments = Department.objects.none()
            students = CustomUser.objects.none()
            bookings = Booking.objects.none()
            damage_reports = DamageReport.objects.none()

        context['results'] = {
            'equipments': equipments,
            'departments': departments,
            'students': students,
            'bookings': bookings,
            'damage_reports': damage_reports,
            'total_count': (equipments.count() + departments.count() + students.count() + bookings.count() + damage_reports.count())
        }
        return context


# ====================================================
# SYSTEM SETTINGS VIEW
# ====================================================

class SystemSettingsView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = SystemSettings
    form_class = SystemSettingsForm
    template_name = 'dashboard/settings.html'
    success_url = reverse_lazy('dashboard:settings')

    def get_object(self, queryset=None):
        return SystemSettings.get_settings()

    def form_valid(self, form):
        response = super().form_valid(form)
        from dashboard.utils import log_activity
        log_activity(self.request.user, "Settings Updated", "Admin updated the system configuration settings.")
        messages.success(self.request, "System settings updated successfully!")
        return response


# ====================================================
# ADVANCED REPORTS PAGE VIEW
# ====================================================

class ReportsDashboardView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    template_name = 'dashboard/reports_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        total_equip = Equipment.objects.count()
        avail_equip = Equipment.objects.aggregate(total=Sum('available_quantity'))['total'] or 0
        booked_equip = Booking.objects.filter(status='Approved').aggregate(total=Sum('quantity'))['total'] or 0
        out_of_stock = Equipment.objects.filter(available_quantity=0).count()
        
        total_depts = Department.objects.count()
        total_bookings = Booking.objects.count()
        total_damages = DamageReport.objects.count()
        
        recent_activities = ActivityLog.objects.order_by('-created_at')[:10]

        context['stats'] = {
            'total_equipment': total_equip,
            'available_equipment': avail_equip,
            'booked_equipment': booked_equip,
            'out_of_stock': out_of_stock,
            'total_departments': total_depts,
            'total_bookings': total_bookings,
            'total_damages': total_damages
        }
        context['recent_activities'] = recent_activities
        return context


# ====================================================
# PDF REPORT EXPORTS (ReportLab)
# ====================================================

class ExportEquipmentPDFView(LoginRequiredMixin, AdminRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        headers = ["Code", "Name", "Department", "Location", "Total Qty", "Avail Qty", "Status"]
        col_widths = [60, 110, 90, 80, 50, 50, 64]
        
        queryset = Equipment.objects.select_related('department').order_by('equipment_code')
        rows = []
        for eq in queryset:
            rows.append([
                eq.equipment_code,
                eq.equipment_name,
                eq.department.name,
                eq.location or "N/A",
                eq.total_quantity,
                eq.available_quantity,
                eq.status
            ])
            
        return create_pdf_report("Equipment Inventory Report", headers, col_widths, rows, str(len(rows)))


class ExportDepartmentPDFView(LoginRequiredMixin, AdminRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        headers = ["Dept Code", "Department Name", "Equipment Types Count", "Description"]
        col_widths = [80, 140, 100, 184]
        
        queryset = Department.objects.annotate(equip_count=Count('equipment')).order_by('code')
        rows = []
        for d in queryset:
            rows.append([
                d.code,
                d.name,
                d.equip_count,
                d.description or "N/A"
            ])
            
        return create_pdf_report("Department Classification Report", headers, col_widths, rows, str(len(rows)))


class ExportBookingPDFView(LoginRequiredMixin, AdminRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        headers = ["Booking ID", "Student", "Equipment", "Qty", "Booking Date", "Expected Return", "Status"]
        col_widths = [65, 95, 95, 35, 75, 75, 64]
        
        queryset = Booking.objects.select_related('student', 'equipment').order_by('-created_at')
        rows = []
        for b in queryset:
            rows.append([
                b.booking_id,
                b.student.full_name,
                b.equipment.equipment_name,
                b.quantity,
                b.booking_date.strftime('%Y-%m-%d'),
                b.expected_return_date.strftime('%Y-%m-%d'),
                b.status
            ])
            
        return create_pdf_report("Equipment Reservation Requests Report", headers, col_widths, rows, str(len(rows)))


class ExportDamagePDFView(LoginRequiredMixin, AdminRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        headers = ["Report ID", "Booking ID", "Student", "Equipment", "Severity", "Status", "Date Reported"]
        col_widths = [65, 65, 95, 95, 55, 65, 64]
        
        queryset = DamageReport.objects.select_related('booking', 'student', 'equipment').order_by('-created_at')
        rows = []
        for d in queryset:
            rows.append([
                d.report_id,
                d.booking.booking_id,
                d.student.full_name,
                d.equipment.equipment_name,
                d.severity,
                d.status,
                d.created_at.strftime('%Y-%m-%d')
            ])
            
        return create_pdf_report("Equipment Damages & Repairs Report", headers, col_widths, rows, str(len(rows)))


class ExportSummaryPDFView(LoginRequiredMixin, AdminRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        headers = ["Module Category", "Metric Key", "Statistic Count Description"]
        col_widths = [150, 150, 204]
        
        total_equip = Equipment.objects.count()
        avail_equip = Equipment.objects.aggregate(total=Sum('available_quantity'))['total'] or 0
        booked_equip = Booking.objects.filter(status='Approved').aggregate(total=Sum('quantity'))['total'] or 0
        out_of_stock = Equipment.objects.filter(available_quantity=0).count()
        total_depts = Department.objects.count()
        total_bookings = Booking.objects.count()
        total_damages = DamageReport.objects.count()
        
        rows = [
            ["Inventory Management", "Equipment Types Count", f"{total_equip} registered equipment groups"],
            ["Inventory Management", "Total Available Units", f"{avail_equip} units currently in storage"],
            ["Inventory Management", "Booked Out Units", f"{booked_equip} units approved on student loans"],
            ["Inventory Management", "Out of Stock Items", f"{out_of_stock} equipment types currently unavailable"],
            ["Department Structure", "Departments Count", f"{total_depts} department classifications"],
            ["Reservations System", "Booking Requests Count", f"{total_bookings} registered reservations transactions"],
            ["Damage Audit logs", "Damage Reports Count", f"{total_damages} filed damage records"]
        ]
        
        return create_pdf_report("Inventory General Summary Report", headers, col_widths, rows, "Aggregates summary")


# ====================================================
# EXCEL REPORT EXPORTS (openpyxl)
# ====================================================

class ExportEquipmentExcelView(LoginRequiredMixin, AdminRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        headers = ["Equipment Code", "Equipment Name", "Department", "Location", "Condition", "Total Qty", "Available Qty", "Status", "Date Created"]
        queryset = Equipment.objects.select_related('department').order_by('equipment_code')
        
        rows = []
        for eq in queryset:
            rows.append([
                eq.equipment_code,
                eq.equipment_name,
                eq.department.name,
                eq.location or "N/A",
                eq.condition,
                eq.total_quantity,
                eq.available_quantity,
                eq.status,
                eq.created_at.date()
            ])
            
        return generate_excel_response("equipment_inventory.xlsx", headers, rows)


class ExportDepartmentExcelView(LoginRequiredMixin, AdminRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        headers = ["Department Code", "Department Name", "Equipment Types Count", "Description", "Date Created"]
        queryset = Department.objects.annotate(equip_count=Count('equipment')).order_by('code')
        
        rows = []
        for d in queryset:
            rows.append([
                d.code,
                d.name,
                d.equip_count,
                d.description or "N/A",
                d.created_at.date()
            ])
            
        return generate_excel_response("departments_list.xlsx", headers, rows)


class ExportBookingExcelView(LoginRequiredMixin, AdminRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        headers = ["Booking ID", "Student Email", "Student Name", "Equipment Code", "Equipment Name", "Requested Qty", "Booking Date", "Expected Return", "Status"]
        queryset = Booking.objects.select_related('student', 'equipment').order_by('-created_at')
        
        rows = []
        for b in queryset:
            rows.append([
                b.booking_id,
                b.student.email,
                b.student.full_name,
                b.equipment.equipment_code,
                b.equipment.equipment_name,
                b.quantity,
                b.booking_date,
                b.expected_return_date,
                b.status
            ])
            
        return generate_excel_response("reservations_log.xlsx", headers, rows)


class ExportDamageExcelView(LoginRequiredMixin, AdminRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        headers = ["Report ID", "Booking ID", "Student Email", "Student Name", "Equipment Code", "Equipment Name", "Severity", "Status", "Date Reported"]
        queryset = DamageReport.objects.select_related('booking', 'student', 'equipment').order_by('-created_at')
        
        rows = []
        for d in queryset:
            rows.append([
                d.report_id,
                d.booking.booking_id,
                d.student.email,
                d.student.full_name,
                d.equipment.equipment_code,
                d.equipment.equipment_name,
                d.severity,
                d.status,
                d.created_at.date()
            ])
            
        return generate_excel_response("damage_reports.xlsx", headers, rows)


# ====================================================
# NOTIFICATION VIEWS & ENDPOINTS (Existing)
# ====================================================

class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'dashboard/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 15

    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user).order_by('-created_at')
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) |
                Q(message__icontains=q) |
                Q(notification_type__icontains=q)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        return context


class NotificationMarkReadView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        notif = get_object_or_404(Notification, pk=pk, user=request.user)
        notif.is_read = True
        notif.save()
        return JsonResponse({'status': 'success'})


class NotificationMarkAllReadView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'status': 'success'})


# ====================================================
# ACTIVITY FEED VIEWS (Existing)
# ====================================================

class ActivityLogListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = ActivityLog
    template_name = 'dashboard/activity_list.html'
    context_object_name = 'activities'
    paginate_by = 20

    def get_queryset(self):
        queryset = ActivityLog.objects.all().order_by('-created_at')
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(action_type__icontains=q) |
                Q(message__icontains=q) |
                Q(actor__full_name__icontains=q) |
                Q(actor__email__icontains=q)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        return context


# ====================================================
# ANALYTICS GRAPH JSON DATA ENDPOINT (Existing)
# ====================================================

class DashboardChartsDataView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        total_avail = Equipment.objects.aggregate(total=Sum('available_quantity'))['total'] or 0
        total_booked = Booking.objects.filter(status='Approved').aggregate(total=Sum('quantity'))['total'] or 0
        
        status_counts = Booking.objects.values('status').annotate(count=Count('id'))
        status_dict = {'Pending': 0, 'Approved': 0, 'Rejected': 0, 'Returned': 0, 'Cancelled': 0}
        for sc in status_counts:
            if sc['status'] in status_dict:
                status_dict[sc['status']] = sc['count']
            
        dept_counts = Department.objects.annotate(equip_count=Count('equipment')).values('name', 'equip_count')
        dept_labels = [d['name'] for d in dept_counts]
        dept_values = [d['equip_count'] for d in dept_counts]
        
        today = timezone.localtime(timezone.now()).date()
        months_labels = []
        months_values = []
        for i in range(5, -1, -1):
            year = today.year
            month = today.month - i
            if month <= 0:
                month += 12
                year -= 1
            month_name = calendar.month_name[month][:3]
            months_labels.append(f"{month_name} {year}")
            
            cnt = Booking.objects.filter(created_at__year=year, created_at__month=month).count()
            months_values.append(cnt)
            
        severity_counts = DamageReport.objects.values('severity').annotate(count=Count('id'))
        severity_dict = {'Low': 0, 'Medium': 0, 'High': 0, 'Critical': 0}
        for sc in severity_counts:
            if sc['severity'] in severity_dict:
                severity_dict[sc['severity']] = sc['count']
            
        data = {
            'availability': {
                'labels': ['Available Units', 'Booked Units'],
                'values': [total_avail, total_booked]
            },
            'booking_statuses': {
                'labels': list(status_dict.keys()),
                'values': list(status_dict.values())
            },
            'departments': {
                'labels': dept_labels,
                'values': dept_values
            },
            'monthly_trend': {
                'labels': months_labels,
                'values': months_values
            },
            'damage_severity': {
                'labels': list(severity_dict.keys()),
                'values': list(severity_dict.values())
            }
        }
        return JsonResponse(data)
