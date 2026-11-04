from django.views.generic import ListView, DetailView, CreateView, View
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from dashboard.views import AdminRequiredMixin
from inventory.models import Equipment, Department
from accounts.models import CustomUser
from .models import Booking, DamageReport
from .forms import (
    BookingCreateForm, AdminBookingActionForm,
    DamageReportCreateForm, AdminDamageReportActionForm
)
from dashboard.utils import create_notification, notify_admins, log_activity

# ====================================================
# BOOKING VIEWS
# ====================================================

class BookingCreateView(LoginRequiredMixin, CreateView):
    model = Booking
    form_class = BookingCreateForm
    template_name = 'bookings/booking_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'student':
            raise PermissionDenied("Only students or faculty can request bookings.")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        equipment_id = self.kwargs.get('equipment_id')
        equipment = get_object_or_404(Equipment, pk=equipment_id)
        kwargs['equipment'] = equipment
        kwargs['student'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        equipment_id = self.kwargs.get('equipment_id')
        context['equipment'] = get_object_or_404(Equipment, pk=equipment_id)
        return context

    def form_valid(self, form):
        form.instance.student = self.request.user
        equipment_id = self.kwargs.get('equipment_id')
        form.instance.equipment = get_object_or_404(Equipment, pk=equipment_id)
        form.instance.status = 'Pending'
        
        # Save first
        response = super().form_valid(form)
        booking = self.object

        # Notifications
        notify_admins(
            "New Booking Request Submitted",
            f"Student {self.request.user.full_name} submitted booking request {booking.booking_id} for {booking.quantity}x {booking.equipment.equipment_name}.",
            "Booking"
        )
        create_notification(
            self.request.user,
            "Booking Request Submitted",
            f"Your request {booking.booking_id} for {booking.quantity}x {booking.equipment.equipment_name} was received and is pending review.",
            "Booking"
        )
        
        # Activity Logging
        log_activity(
            self.request.user,
            "Booking Created",
            f"Student {self.request.user.full_name} requested booking {booking.booking_id} for {booking.quantity}x {booking.equipment.equipment_name}."
        )

        messages.success(self.request, "Booking request submitted successfully!")
        return response

    def get_success_url(self):
        return reverse('bookings:booking_list')


class BookingListView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = 'bookings/booking_list.html'
    context_object_name = 'bookings'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            queryset = Booking.objects.all().order_by('-created_at')
            
            # Text search mapping
            q = self.request.GET.get('q')
            if q:
                queryset = queryset.filter(
                    Q(booking_id__icontains=q) |
                    Q(student__full_name__icontains=q) |
                    Q(equipment__equipment_name__icontains=q)
                )
                
            # Filters logic
            status = self.request.GET.get('status')
            if status:
                queryset = queryset.filter(status=status)
                
            dept = self.request.GET.get('department')
            if dept:
                queryset = queryset.filter(equipment__department_id=dept)
                
            equip = self.request.GET.get('equipment')
            if equip:
                queryset = queryset.filter(equipment_id=equip)
                
            stud = self.request.GET.get('student')
            if stud:
                queryset = queryset.filter(student_id=stud)
                
            date_str = self.request.GET.get('booking_date')
            if date_str:
                queryset = queryset.filter(booking_date=date_str)
        else:
            # Students can only view their own bookings
            queryset = Booking.objects.filter(student=user).order_by('-created_at')
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if user.role == 'admin':
            context['departments'] = Department.objects.all()
            context['equipment_options'] = Equipment.objects.all()
            context['student_options'] = CustomUser.objects.filter(role='student')
            context['status_choices'] = Booking.STATUS_CHOICES
            
            context['q'] = self.request.GET.get('q', '')
            context['selected_status'] = self.request.GET.get('status', '')
            context['selected_dept'] = self.request.GET.get('department', '')
            context['selected_equip'] = self.request.GET.get('equipment', '')
            context['selected_student'] = self.request.GET.get('student', '')
            context['selected_date'] = self.request.GET.get('booking_date', '')
            
        return context


class BookingDetailView(LoginRequiredMixin, DetailView):
    model = Booking
    template_name = 'bookings/booking_detail.html'
    context_object_name = 'booking'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if self.request.user.role == 'student' and obj.student != self.request.user:
            raise PermissionDenied("You are not authorized to view this booking.")
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.role == 'admin':
            context['action_form'] = AdminBookingActionForm(instance=self.get_object())
        return context


class BookingCancelView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        booking = get_object_or_404(Booking, pk=pk)
        
        if booking.student != request.user:
            raise PermissionDenied("You can only cancel your own bookings.")
            
        if booking.status != 'Pending':
            messages.error(request, "Only pending bookings can be cancelled.")
            return redirect('bookings:booking_detail', pk=pk)
            
        booking.status = 'Cancelled'
        booking.save()

        # Alert Notifications
        notify_admins(
            "Booking Request Cancelled",
            f"Student {request.user.full_name} cancelled booking request {booking.booking_id}.",
            "Booking"
        )
        create_notification(
            request.user,
            "Booking Cancelled",
            f"You have successfully cancelled booking request {booking.booking_id}.",
            "Booking"
        )
        log_activity(
            request.user,
            "Booking Cancelled",
            f"Student {request.user.full_name} cancelled pending booking {booking.booking_id}."
        )
        
        messages.success(request, "Booking cancelled successfully.")
        return redirect('bookings:booking_detail', pk=pk)


class AdminBookingActionView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        booking = get_object_or_404(Booking, pk=pk)
        old_status = booking.status
        form = AdminBookingActionForm(request.POST, instance=booking)
        
        if form.is_valid():
            booking = form.save(commit=False)
            booking.approved_by = request.user
            booking.save()
            
            # Check for changes and trigger appropriate notifications
            if old_status != booking.status:
                if booking.status == 'Approved':
                    create_notification(
                        booking.student,
                        "Booking Request Approved",
                        f"Your booking request {booking.booking_id} for {booking.quantity}x {booking.equipment.equipment_name} has been approved.",
                        "Approval"
                    )
                    log_activity(request.user, "Booking Approved", f"Approved booking {booking.booking_id} for student {booking.student.full_name}.")
                    
                elif booking.status == 'Rejected':
                    create_notification(
                        booking.student,
                        "Booking Request Rejected",
                        f"Your booking request {booking.booking_id} for {booking.equipment.equipment_name} was rejected. Remarks: {booking.remarks}",
                        "Rejection"
                    )
                    log_activity(request.user, "Booking Rejected", f"Rejected booking {booking.booking_id} for student {booking.student.full_name}.")
                    
                elif booking.status == 'Returned':
                    create_notification(
                        booking.student,
                        "Equipment Returned",
                        f"Your booking request {booking.booking_id} for {booking.equipment.equipment_name} has been marked as returned.",
                        "Booking"
                    )
                    notify_admins(
                        "Equipment Returned",
                        f"Equipment for booking {booking.booking_id} (borrowed by {booking.student.full_name}) has been returned.",
                        "Booking"
                    )
                    log_activity(request.user, "Equipment Returned", f"Marked booking {booking.booking_id} as returned.")

            messages.success(request, f"Booking status updated to {booking.status} successfully!")
        else:
            messages.error(request, "Invalid entries. Status update failed.")
            
        return redirect('bookings:booking_detail', pk=pk)


# ====================================================
# DAMAGE REPORT VIEWS
# ====================================================

class DamageReportCreateView(LoginRequiredMixin, CreateView):
    model = DamageReport
    form_class = DamageReportCreateForm
    template_name = 'damage_reports/report_form.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'student':
            raise PermissionDenied("Only students or faculty can submit damage reports.")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['student'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.student = self.request.user
        form.instance.equipment = form.instance.booking.equipment
        form.instance.status = 'Pending'
        
        response = super().form_valid(form)
        report = self.object

        # Notifications
        notify_admins(
            "New Damage Report Submitted",
            f"Student {self.request.user.full_name} submitted damage report {report.report_id} for '{report.equipment.equipment_name}' (Booking: {report.booking.booking_id}). Severity: {report.severity}.",
            "Damage Report"
        )
        create_notification(
            self.request.user,
            "Damage Report Filed",
            f"Your damage report {report.report_id} for '{report.equipment.equipment_name}' was successfully received and is under review.",
            "Damage Report"
        )
        
        # Log activity
        log_activity(
            self.request.user,
            "Damage Report Submitted",
            f"Student {self.request.user.full_name} filed damage report {report.report_id} on {report.equipment.equipment_name}."
        )

        messages.success(self.request, "Damage report submitted successfully!")
        return response

    def get_success_url(self):
        return reverse('bookings:report_list')


class DamageReportListView(LoginRequiredMixin, ListView):
    model = DamageReport
    template_name = 'damage_reports/report_list.html'
    context_object_name = 'reports'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            queryset = DamageReport.objects.all().order_by('-created_at')
            
            # Search parameters
            q = self.request.GET.get('q')
            if q:
                queryset = queryset.filter(
                    Q(report_id__icontains=q) |
                    Q(student__full_name__icontains=q) |
                    Q(equipment__equipment_name__icontains=q) |
                    Q(title__icontains=q)
                )

            # Filtering parameters
            status = self.request.GET.get('status')
            if status:
                queryset = queryset.filter(status=status)
                
            severity = self.request.GET.get('severity')
            if severity:
                queryset = queryset.filter(severity=severity)
                
            stud = self.request.GET.get('student')
            if stud:
                queryset = queryset.filter(student_id=stud)
                
            equip = self.request.GET.get('equipment')
            if equip:
                queryset = queryset.filter(equipment_id=equip)
                
            date_str = self.request.GET.get('created_date')
            if date_str:
                queryset = queryset.filter(created_at__date=date_str)
        else:
            # Students can only view their own damage reports
            queryset = DamageReport.objects.filter(student=user).order_by('-created_at')
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if user.role == 'admin':
            context['status_choices'] = DamageReport.STATUS_CHOICES
            context['severity_choices'] = DamageReport.SEVERITY_CHOICES
            context['student_options'] = CustomUser.objects.filter(role='student')
            context['equipment_options'] = Equipment.objects.all()
            
            # Persist filter settings
            context['q'] = self.request.GET.get('q', '')
            context['selected_status'] = self.request.GET.get('status', '')
            context['selected_severity'] = self.request.GET.get('severity', '')
            context['selected_student'] = self.request.GET.get('student', '')
            context['selected_equip'] = self.request.GET.get('equipment', '')
            context['selected_date'] = self.request.GET.get('created_date', '')
            
        return context


class DamageReportDetailView(LoginRequiredMixin, DetailView):
    model = DamageReport
    template_name = 'damage_reports/report_detail.html'
    context_object_name = 'report'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if self.request.user.role == 'student' and obj.student != self.request.user:
            raise PermissionDenied("You are not authorized to view this damage report.")
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.role == 'admin':
            context['action_form'] = AdminDamageReportActionForm(instance=self.get_object())
        return context


class AdminDamageReportActionView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        report = get_object_or_404(DamageReport, pk=pk)
        old_status = report.status
        form = AdminDamageReportActionForm(request.POST, instance=report)
        
        if form.is_valid():
            report = form.save()
            
            # Notify student of update if status changed
            if old_status != report.status:
                create_notification(
                    report.student,
                    "Damage Report Status Updated",
                    f"Your damage report {report.report_id} for '{report.equipment.equipment_name}' has been updated to '{report.status}'. Remarks: {report.admin_remarks}",
                    "Damage Report"
                )
                log_activity(
                    request.user,
                    "Damage Report Updated",
                    f"Admin updated damage report {report.report_id} status to '{report.status}'."
                )

            messages.success(request, f"Damage report status updated to {report.status} successfully!")
        else:
            messages.error(request, "Failed to update damage report status.")
            
        return redirect('bookings:report_detail', pk=pk)
