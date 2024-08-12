from django.shortcuts import render, redirect
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib import messages
from django.http import HttpRequest
from .forms import UploadFileForm
from .models import SanctionRecord, UploadStatistics
from .name_variations import generate_name_variations
from io import TextIOWrapper
from datetime import datetime
import csv
import uuid

from django.utils import timezone
from io import TextIOWrapper
import uuid
import csv
from .models import SanctionRecord, UploadStatistics

from django.utils import timezone
from io import TextIOWrapper
import uuid
import csv
from .models import SanctionRecord, UploadStatistics
from django.contrib import messages

def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%B %d, %Y')  # e.g., 'July 19, 2024'
    except ValueError:
        return None

def generate_watch_list_id():
    return SanctionRecord.objects.count() + 1

def process_file(file, list_name, request):
    start_time = timezone.now()
    dataset_id = uuid.uuid4()

    try:
        file_wrapper = TextIOWrapper(file, encoding='utf-8', errors='replace')
    except UnicodeDecodeError as e:
        messages.error(request, f"Error decoding file: {str(e)}")
        return

    reader = csv.DictReader(file_wrapper)
    new_records = 0
    updated_records = 0
    records_to_update = []

    for row in reader:
        record_id = row.get('Id_original')  # Ensure correct field name
        if not record_id:
            continue
        
        created_date = parse_date(row.get('Created Date', ''))
        modified_date = parse_date(row.get('Modified Date', ''))

        if created_date is None:
            created_date = timezone.now()
        
        watch_list_id = row.get('Watchlist ID', generate_watch_list_id())

        # Log the record being processed
        print(f"Processing record ID: {record_id}")

        obj, created = SanctionRecord.objects.update_or_create(
            id=record_id,
            defaults={
                'first_name': row.get('First Name', ''),
                'last_name': row.get('Last Name', ''),
                'list_name': list_name,
                'created_date': created_date,
                'modified_date': modified_date,
                'is_active': row.get('Is_active', 'False') == 'True',
                'id_original': row.get('Id_original', ''),  # Ensure correct field name
                'entity_type': row.get('Entity Type', ''),  # Ensure correct field name
                'identity_numbers': row.get('Identity Number', ''),  # Ensure correct field name
                'identity_types': row.get('Identity Type', ''),  # Ensure correct field name
                'city': row.get('City', ''),
                'country': row.get('Country', ''),
                'watchlist_country': row.get('Watchlist Country', ''),
                'alias': row.get('Alias', ''),
                'alias_type': row.get('Alias Type', ''),
                'watch_list_id': watch_list_id,
                'dataset_id': dataset_id
            }
        )

        if created:
            new_records += 1
        else:
            updated_records += 1

        records_to_update.append(record_id)

    if records_to_update:
        # Ensure records are correctly updated
        SanctionRecord.objects.filter(id__in=records_to_update).update(dataset_id=dataset_id)

    total_records = SanctionRecord.objects.filter(list_name=list_name).count()

    UploadStatistics.objects.update_or_create(
        list_name=list_name,
        defaults={
            'last_import_date': timezone.now().date(),
            'records_added': new_records,
            'records_updated': updated_records,
            'records_deleted': 0,  # You might need to track deletions if applicable
            'total_active_records': total_records,
            'start_time': start_time,
            'end_time': timezone.now(),
        }
    )


def list_management(request: HttpRequest):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            if form.cleaned_data.get('ofac_file'):
                process_file(form.cleaned_data['ofac_file'], 'ofac', request)
            if form.cleaned_data.get('un_file'):
                process_file(form.cleaned_data['un_file'], 'un', request)
            if form.cleaned_data.get('eu_file'):
                process_file(form.cleaned_data['eu_file'], 'eu', request)
                
            statistics = UploadStatistics.objects.all()
            total_added = sum(stat.records_added for stat in statistics)
            total_ofac = next((stat.records_added for stat in statistics if stat.list_name == 'ofac'), 0)
            total_un = next((stat.records_added for stat in statistics if stat.list_name == 'un'), 0)
            total_eu = next((stat.records_added for stat in statistics if stat.list_name == 'eu'), 0)
            
            messages.success(request, f'Total records added: {total_added}. OFAC: {total_ofac}, UN: {total_un}, EU: {total_eu}')
            
            return redirect('transactions:list_management')
    else:
        form = UploadFileForm()

    statistics = UploadStatistics.objects.all()
    context = {
        'form': form,
        'statistics': statistics
    }
    return render(request, 'transactions/list_management.html', context)

from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import render
from .models import SanctionRecord



from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Count
from .models import SanctionRecord

def records_variations(request):
    # Extract filter parameters from the GET request
    watch_list_id = request.GET.get('watch_list_id', '')
    id_original = request.GET.get('id_original', '')
    first_name = request.GET.get('first_name', '')
    last_name = request.GET.get('last_name', '')
    list_name = request.GET.get('list_name', '')

    # Initialize the query set
    sanction_records = SanctionRecord.objects.all()

    # Apply filters based on the provided parameters
    if watch_list_id:
        sanction_records = sanction_records.filter(watch_list_id=watch_list_id)
    if id_original:
        sanction_records = sanction_records.filter(id_original=id_original)
    if first_name:
        sanction_records = sanction_records.filter(first_name__icontains=first_name)
    if last_name:
        sanction_records = sanction_records.filter(last_name__icontains=last_name)
    if list_name:
        sanction_records = sanction_records.filter(list_name=list_name)

    # Annotate each record with the count of variations
    sanction_records = sanction_records.annotate(variation_count=Count('namevariation'))

    # Order by id_original in ascending order
    sanction_records = sanction_records.order_by('id_original')

    # Paginate the records
    paginator = Paginator(sanction_records, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Summary of records by list name
    list_summary = SanctionRecord.objects.values('list_name').annotate(total_records=Count('id')).order_by('list_name')

    # Prepare the context for rendering
    context = {
        'sanction_records': page_obj.object_list,
        'page_obj': page_obj,
        'watch_list_id': watch_list_id,
        'id_original': id_original,
        'first_name': first_name,
        'last_name': last_name,
        'list_name': list_name,
        'total_records': paginator.count,
        'list_summary': list_summary,
    }

    return render(request, 'transactions/records_variations.html', context)






from django.shortcuts import get_object_or_404, render, redirect
from transactions.models import SanctionRecord, NameVariation

from django.views.decorators.csrf import csrf_exempt



from django.http import JsonResponse

from .forms import NameVariationForm

import logging

logger = logging.getLogger(__name__)

from django.shortcuts import render, get_object_or_404
from .models import SanctionRecord, NameVariation
from .forms import NameVariationForm
import logging

logger = logging.getLogger(__name__)

from django.shortcuts import get_object_or_404, render
from .models import SanctionRecord, NameVariation
from .forms import NameVariationForm
import logging

logger = logging.getLogger(__name__)

def view_record(request, record_id, variation_id=None):
    # Retrieve the SanctionRecord instance or return a 404 if not found
    record = get_object_or_404(SanctionRecord, pk=record_id)
    
    # Process aliases if available
    aliases = []
    if record.alias and record.alias_type:
        alias_list = record.alias.split('\n')
        alias_type_list = record.alias_type.split('\n')
        aliases = list(zip(alias_list, alias_type_list))
    
    # Process identity numbers if available
    identities = [
        (item.split(':')[0].strip(), item.split(':')[1].strip())
        for item in (record.identity_numbers.split(', ') if record.identity_numbers else [])
        if ':' in item
    ]
    
    # Retrieve NameVariation instances associated with the SanctionRecord
    variations = NameVariation.objects.filter(sanction_record=record)
    logger.debug(f"Variations: {list(variations.values('variation_id'))}")
    
    # Retrieve a specific variation if provided
    specific_variation = variations.filter(pk=variation_id).first() if variation_id else None
    
    # Prepare variations with status and forms for editing
    variations_with_status = [
        {
            'variation_id': variation.variation_id,
            'variation': variation.variation,
            'score': variation.score,
            'status': 'Enabled' if variation.is_active else 'Disabled',
            'form': NameVariationForm(instance=variation)  # Form for editing
        }
        for variation in variations
    ]
    
    # Prepare context for rendering the template
    context = {
        'list_name': record.list_name,
        'record': record,
        'aliases': aliases,
        'identities': identities,
        'variations': variations_with_status,
        'full_name': f"{record.first_name} {record.last_name}",
        'specific_variation': specific_variation
    }
    
    # Render the view_record template with the context data
    return render(request, 'transactions/view_record.html', context)











import uuid
from django.db.models import Q
from django.shortcuts import render
from django.core.paginator import Paginator
from .models import SanctionRecord, NameVariation


from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.shortcuts import render
import uuid

def view_variations(request):
    # Initialize variables
    records = SanctionRecord.objects.all()
    data = []

    # Get filtering inputs and selections
    watch_list_id = request.GET.get('watch_list_id', '')
    name_filter = request.GET.get('name', '').strip()
    identity_type_filter = request.GET.get('identity_type', '').strip()
    country_filter = request.GET.get('country', '').strip()

    # Apply filters based on input
    if watch_list_id:
        records = records.filter(watch_list_id=watch_list_id)
    if name_filter:
        records = records.filter(
            Q(first_name__icontains=name_filter) | Q(last_name__icontains=name_filter)
        )
    if identity_type_filter:
        records = records.filter(identity_type__icontains=identity_type_filter)
    if country_filter:
        records = records.filter(country__icontains=country_filter)

    # Fetch records with the count of existing variations
    records = records.annotate(
        variation_count=Count('namevariation')
    )

    # Generate variations for records with no existing variations
    records_to_generate = records.filter(variation_count=0)
    if records_to_generate.exists():
        combined_names = [f"{record.first_name} {record.last_name}" for record in records_to_generate]
        variations = generate_bulk_name_variations(combined_names)
        
        name_variations_to_create = []
        for record, variations_for_name in zip(records_to_generate, variations):
            name_variations_to_create.extend(
                NameVariation(
                    sanction_record=record,
                    variation=variation,
                    score=score,
                    test_id=uuid.uuid4()  # Assign unique test_id
                )
                for variation, score in variations_for_name.items()
            )
        NameVariation.objects.bulk_create(name_variations_to_create)

    # Prepare data for rendering
    for record in records:
        combined_name = f"{record.first_name} {record.last_name}"
        variation_count = record.variation_count
        
        variations_list = list(NameVariation.objects.filter(sanction_record=record).values('variation_id', 'variation', 'score', 'test_id'))
        data.append({
            'combined_name': combined_name,
            'entity_type': record.entity_type,
            'created_date': record.created_date,
            'variations': variations_list,
            'variation_count': variation_count,
            'list_name': record.list_name,
            'dataset_id': record.dataset_id,
            'watch_list_id': record.watch_list_id,
        })

    # Paginate data
    paginator = Paginator(data, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'transactions/view_variations.html', {
        'page_obj': page_obj,
        'show_data': request.GET.get('generate'),  # Whether to show data based on "Generate" button click
        'watch_list_id': watch_list_id,  # Pass the filter parameter to the template
    })

def generate_bulk_name_variations(combined_names):
    # Bulk version of name variations generation
    variations = {}
    for name in combined_names:
        variations[name] = generate_name_variations(name)
    return variations







from django.shortcuts import render, redirect, get_object_or_404
from .models import NameVariation, SanctionRecord

def delete_variation(request, variation_id):
    variation = get_object_or_404(NameVariation, variation_id=variation_id)
    variation.delete()
    return redirect("transactions:view_record", record_id=variation.sanction_record.id)  # Adjusted to pass record_id

def update_variation(request, variation_id):
    variation = get_object_or_404(NameVariation, variation_id=variation_id)
    return render(request, "transactions/update_variation.html", {
        'variation': variation
    })

def do_update_variation(request, variation_id):
    if request.method == "POST":
        variation_name = request.POST.get("variation")
        score = request.POST.get("score")
        is_active = request.POST.get("is_active")

        variation = get_object_or_404(NameVariation, variation_id=variation_id)

        variation.variation = variation_name
        variation.score = int(score) if score else 0  # Ensure score is an integer
        variation.is_active = is_active == 'enabled'  # Checkbox for boolean value
        variation.save()

        # Redirect to the view_record with the record_id
        record_id = variation.sanction_record.id
        return redirect("transactions:view_record", record_id=record_id)  # Pass record_id to URL





from django.shortcuts import render, redirect, get_object_or_404
from .models import NameVariation, SanctionRecord

def add_variation(request, record_id):
    sanction_record = get_object_or_404(SanctionRecord, id=record_id)
    if request.method == "POST":
        variation_name = request.POST.get("variation")
        score = request.POST.get("score")
        is_active = request.POST.get("is_active")

        # Create and save the new variation
        NameVariation.objects.create(
            sanction_record=sanction_record,
            variation=variation_name,
            score=int(score) if score else 0,
            is_active=is_active == 'enabled'  # Checkbox for boolean value
        )

        # Redirect to the view_record with the record_id
        return redirect("transactions:view_record", record_id=record_id)

    return render(request, "transactions/add_variation.html", {
        'sanction_record': sanction_record
    })














from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import NameVariation
import json

@require_POST
def toggle_status(request):
    data = json.loads(request.body)
    variation_id = data.get('id')

    try:
        variation = NameVariation.objects.get(id=variation_id)
        variation.is_active = False  # Assuming you want to disable the variation
        variation.save()

        return JsonResponse({
            'success': True,
            'new_status_text': 'Disabled'
        })
    except NameVariation.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Variation not found'})






















from django.shortcuts import get_object_or_404, redirect, render
from .models import NameVariation

def disable_variation(request, variation_id):
    if request.method == 'POST':
        variation = get_object_or_404(NameVariation, variation_id=variation_id)
        variation.is_active = False
        variation.save()

        # Redirect to the view record page
        # Adjust this if necessary to match your URL configuration
        return redirect('transactions:view_record', record_id=variation.sanction_record.id)

    return render(request, 'transactions/disable_variation.html', {'variation_id': variation_id})















import csv
from django.http import HttpResponse

def export_variations(request):

    records = SanctionRecord.objects.all()
    data = []

    # Get filtering inputs and selections
    name_filter = request.GET.get('name', '').strip()
    identity_type_filter = request.GET.get('identity_type', '').strip()
    country_filter = request.GET.get('country', '').strip()

    # Initialize the HTTP response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="variations_export.csv"'
    
    writer = csv.writer(response)
    
    # Write header row
    writer.writerow([
        'Name', 'Test ID', 'Dataset ID', 'Entity Type', 'List Name', 
        'Variation ID', 'Variation', 'Score', 'Number of Entries', 
        'Filter Option', 'System Option', 'Test Option', 'Complexity Level'
    ])
    
    # Get filter values
    num_entries = request.GET.get('num_entries', '')
    filter_option = request.GET.get('filter_option', '')
    system_option = request.GET.get('system_option', '')
    test_option = request.GET.get('test_option', '')
    complexity_level = request.GET.get('complexity_level', '')

    # Query records based on filters
    records = SanctionRecord.objects.all()
    if filter_option:
        if filter_option == 'name':
            records = records.filter(first_name__icontains=name_filter) | records.filter(last_name__icontains=name_filter)
        elif filter_option == 'identity_type':
            records = records.filter(identity_type__icontains=identity_type_filter)
        elif filter_option == 'country':
            records = records.filter(country__icontains=country_filter)
    
    for record in records:
        combined_name = f"{record.first_name} {record.last_name}"
        existing_variations = NameVariation.objects.filter(sanction_record=record)
        for variation in existing_variations:
            writer.writerow([
                combined_name,
                variation.test_id,
                record.dataset_id,
                record.entity_type,
                record.list_name,
                variation.variation_id,
                variation.variation,
                variation.score,
                num_entries,
                filter_option,
                system_option,
                test_option,
                complexity_level
            ])
    
    return response





# views.py
from django.shortcuts import render
from django.http import JsonResponse
from .models import SanctionRecordDetail
import random

def generate_test_data(request):
    if request.method == 'POST':
        num_entries = int(request.POST.get('num_entries', 0))
        selected_fields = request.POST.getlist('fields')  # e.g., ['name', 'country', 'identity']
        
        if num_entries > 0:
            # Fetch random records
            all_records = list(SanctionRecordDetail.objects.all())
            random_records = random.sample(all_records, min(num_entries, len(all_records)))
            
            # Prepare the response data
            data = []
            for record in random_records:
                record_data = {
                    'name': record.name if 'name' in selected_fields else '',
                    'entity_type': record.entity_type if 'entity' in selected_fields else '',
                    'list_name': record.list_name if 'list_name' in selected_fields else '',
                    'score': record.score if 'score' in selected_fields else '',
                    'identity_type': record.sanction_record.identity_type if 'identity' in selected_fields else '',
                    'id': record.sanction_record.id_original if 'identity' in selected_fields else '',
                    'country': record.sanction_record.country if 'country' in selected_fields else ''
                }
                data.append(record_data)
            
            return JsonResponse({'data': data})
    
    return render(request, 'transactions/generate_test_data.html')



import csv
from django.http import HttpResponse
from .models import NameVariation  # Update with your actual model

def export_variations_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="variations.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Identity Type', 'Country'])  # Update with your actual column names

    variations = NameVariation.objects.all()  # Add filtering logic if needed
    for variation in variations:
        writer.writerow([variation.name, variation.identity_type, variation.country])  # Update with your actual fields

    return response




from django.core.paginator import Paginator
from django.shortcuts import render
from .models import SanctionRecord, NameVariation
from django.core.paginator import Paginator
from django.shortcuts import render
from .models import SanctionRecord, NameVariation


def all_variations(request):
    records = SanctionRecord.objects.all()
    data = []
    
    for record in records:
        combined_name = f"{record.first_name} {record.last_name}"
        
        # Check if variations exist for this record
        existing_variations = NameVariation.objects.filter(sanction_record=record)
        if not existing_variations.exists():
            # Generate variations if none exist
            variations = generate_name_variations(combined_name)
            
            variations_to_create = [
                NameVariation(
                    sanction_record=record,
                    variation=variation,
                    score=score
                )
                for variation, score in variations.items()
            ]
            
            # Bulk create new variations
            NameVariation.objects.bulk_create(variations_to_create)
        
        # Re-fetch variations for the view
        existing_variations = NameVariation.objects.filter(sanction_record=record)
        variations_list = list(existing_variations.values('variation', 'score'))
        
        data.append({
            'combined_name': combined_name,
            'entity_type': record.entity_type,
            'created_date': record.created_date,
            'variations': variations_list
        })

    paginator = Paginator(data, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'transactions/all_variations.html', {'page_obj': page_obj})




from django.shortcuts import render
from .models import SanctionRecord, UploadStatistics, NameVariation

def dashboard(request):
    # Retrieve total counts from SanctionRecord
    total_records = SanctionRecord.objects.count()
    
    # Retrieve total counts from NameVariation
    total_variations = NameVariation.objects.count()
    
    # Retrieve statistics from UploadStatistics
    statistics = UploadStatistics.objects.all()
    total_added = sum(stat.records_added for stat in statistics)
    
    # Prepare data for charts
    chart_data = {
        'labels': [],  # List of scores
        'metric_performance_data': [],  # Number of variations for each score
        'name_variations_labels': [],  # Example: ['Score1', 'Score2', ...]
        'name_variations_data': []  # Example: [20, 15, ...]
    }
    
    # Fetch and process NameVariation data
    score_variation_counts = {}
    for variation in NameVariation.objects.all():
        score = variation.score  # Assuming `score` is an attribute of NameVariation
        if score not in score_variation_counts:
            score_variation_counts[score] = 0
        score_variation_counts[score] += 1

    # Populate chart data
    chart_data['labels'] = list(score_variation_counts.keys())
    chart_data['metric_performance_data'] = list(score_variation_counts.values())

    context = {
        'total_records': total_records,
        'total_added': total_added,
        'total_ofac': next((stat.records_added for stat in statistics if stat.list_name == 'ofac'), 0),
        'total_un': next((stat.records_added for stat in statistics if stat.list_name == 'un'), 0),
        'total_eu': next((stat.records_added for stat in statistics if stat.list_name == 'eu'), 0),
        'total_variations': total_variations,
        'chart_data': chart_data  # Add this line
    }

    return render(request, 'transactions/dashboard_view.html', context)

