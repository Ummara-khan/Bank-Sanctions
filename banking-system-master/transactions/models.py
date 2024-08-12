from django.db import models

from .constants import TRANSACTION_TYPE_CHOICES

import uuid


from django.db import models

from django.db import models
import uuid

class SanctionRecord(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    list_name = models.CharField(max_length=255, blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    modified_date = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=False)
    id_original = models.CharField(max_length=255, blank=True, null=True)
    entity_type = models.CharField(max_length=255, blank=True, null=True)
    identity_numbers = models.CharField(max_length=255, blank=True, null=True)
    identity_types = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    watchlist_country = models.CharField(max_length=255, blank=True, null=True)
    alias = models.CharField(max_length=255, blank=True, null=True)
    alias_type = models.CharField(max_length=255, blank=True, null=True)
    watch_list_id = models.UUIDField(default=uuid.uuid4, editable=False)
    dataset_id = models.UUIDField(default=uuid.uuid4, editable=False)  # Ensure this is here

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

class UploadStatistics(models.Model):
    list_name = models.CharField(max_length=255)
    last_import_date = models.DateField()
    records_added = models.IntegerField()
    records_updated = models.IntegerField()
    records_deleted = models.IntegerField()
    total_active_records = models.IntegerField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    
# transactions/models.py

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after_transaction = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=10)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Transaction by {self.user.email} on {self.timestamp}'




# models.py

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

from django.db import models
import uuid

class NameVariation(models.Model):
    sanction_record = models.ForeignKey(SanctionRecord, on_delete=models.CASCADE)
    variation = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    algorithm = models.CharField(max_length=50, default='unknown')
    score = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    variation_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    test_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):
        return self.variation

    @property
    def is_active_display(self):
        return 'v' if self.is_active else 'Disabled'


    # New model to combine fields from SanctionRecord and NameVariation
class SanctionRecordDetail(models.Model):
    sanction_record = models.ForeignKey(SanctionRecord, on_delete=models.CASCADE)
    name = models.CharField(max_length=510)  # Combine first name and last name
    entity_type = models.CharField(max_length=50)
    list_name = models.CharField(max_length=255)
    variations = models.ManyToManyField(NameVariation)  # Many-to-many relationship to handle multiple variations
    score = models.IntegerField(default=0)  # You might need to aggregate or set this based on variations
    class_name = models.CharField(max_length=255, default='NameVariation')

    def save(self, *args, **kwargs):
        # Combine first name and last name to create the full name
        self.name = f'{self.sanction_record.first_name} {self.sanction_record.last_name}'
        super(SanctionRecordDetail, self).save(*args, **kwargs)

    def __str__(self):
        return self.name