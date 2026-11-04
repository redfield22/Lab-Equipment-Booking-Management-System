from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from dashboard.views import AdminRequiredMixin
from .models import Department, Equipment
from .forms import DepartmentForm, EquipmentForm

# --- DEPARTMENT VIEWS ---

class DepartmentListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Department
    template_name = 'inventory/department_list.html'
    context_object_name = 'departments'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().order_by('-created_at')
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | Q(code__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        return context


class DepartmentCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'inventory/department_form.html'
    success_url = reverse_lazy('inventory:department_list')

    def form_valid(self, form):
        messages.success(self.request, "Department created successfully!")
        return super().form_valid(form)


class DepartmentUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'inventory/department_form.html'
    success_url = reverse_lazy('inventory:department_list')

    def form_valid(self, form):
        messages.success(self.request, "Department updated successfully!")
        return super().form_valid(form)


class DepartmentDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Department
    template_name = 'inventory/department_confirm_delete.html'
    success_url = reverse_lazy('inventory:department_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Department deleted successfully!")
        return super().delete(request, *args, **kwargs)


# --- EQUIPMENT VIEWS ---

class EquipmentListView(LoginRequiredMixin, ListView):
    model = Equipment
    template_name = 'inventory/equipment_list.html'
    context_object_name = 'equipment_list'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 1. Search Logic
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(equipment_name__icontains=query) |
                Q(equipment_code__icontains=query) |
                Q(manufacturer__icontains=query)
            )
            
        # 2. Filters Logic
        dept = self.request.GET.get('department')
        if dept:
            queryset = queryset.filter(department_id=dept)
            
        cond = self.request.GET.get('condition')
        if cond:
            queryset = queryset.filter(condition=cond)
            
        stat = self.request.GET.get('status')
        if stat:
            queryset = queryset.filter(status=stat)
            
        # 3. Sorting Logic
        sort = self.request.GET.get('sort', 'newest')
        if sort == 'oldest':
            queryset = queryset.order_by('created_at')
        elif sort == 'name':
            queryset = queryset.order_by('equipment_name')
        elif sort == 'quantity':
            queryset = queryset.order_by('-available_quantity')
        else: # newest
            queryset = queryset.order_by('-created_at')
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Send dropdown options to context
        context['departments'] = Department.objects.all()
        context['conditions'] = Equipment.CONDITION_CHOICES
        context['statuses'] = Equipment.STATUS_CHOICES
        
        # Keep track of current selections for inputs in template
        context['q'] = self.request.GET.get('q', '')
        context['selected_dept'] = self.request.GET.get('department', '')
        context['selected_cond'] = self.request.GET.get('condition', '')
        context['selected_stat'] = self.request.GET.get('status', '')
        context['selected_sort'] = self.request.GET.get('sort', 'newest')
        return context


class EquipmentDetailView(LoginRequiredMixin, DetailView):
    model = Equipment
    template_name = 'inventory/equipment_detail.html'
    context_object_name = 'equipment'


class EquipmentCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Equipment
    form_class = EquipmentForm
    template_name = 'inventory/equipment_form.html'
    success_url = reverse_lazy('inventory:equipment_list')

    def form_valid(self, form):
        messages.success(self.request, "Equipment added successfully!")
        return super().form_valid(form)


class EquipmentUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Equipment
    form_class = EquipmentForm
    template_name = 'inventory/equipment_form.html'
    success_url = reverse_lazy('inventory:equipment_list')

    def form_valid(self, form):
        messages.success(self.request, "Equipment updated successfully!")
        return super().form_valid(form)


class EquipmentDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Equipment
    template_name = 'inventory/equipment_confirm_delete.html'
    success_url = reverse_lazy('inventory:equipment_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Equipment deleted successfully!")
        return super().delete(request, *args, **kwargs)


from django.views import View
from django.http import HttpResponse

class EquipmentQRDownloadView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        eq = get_object_or_404(Equipment, pk=pk)
        svg_str = eq.qr_code_svg
        response = HttpResponse(svg_str, content_type='image/svg+xml')
        response['Content-Disposition'] = f'attachment; filename="QR_{eq.equipment_code}.svg"'
        return response
