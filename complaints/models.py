from django.db import models
from django.contrib.auth.models import User
import uuid

PRIORITY_CHOICES = [
    ('Low', 'Low'),
    ('Medium', 'Medium'),
    ('High', 'High'),
    ('Critical', 'Critical'),
]
STATUS_CHOICES = [
    ('Pending', 'Pending'),
    ('In Progress', 'In Progress'),
    # Stored as "Verified" in DB; shown as "Completed" label for admins.
    ('Verified', 'Verified'),
]

class Complaint(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30)
    location = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=100)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    image = models.ImageField(upload_to='complaint_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def complaint_id(self):
        return str(self.id).split('-')[0].upper()
