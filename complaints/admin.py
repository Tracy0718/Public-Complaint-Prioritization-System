from django.contrib import admin
from .models import Complaint

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('complaint_id','name','category','priority','status','created_at')
    list_filter = ('category','priority','status')
    search_fields = ('name','phone','location','description')
