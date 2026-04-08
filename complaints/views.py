import os, joblib, json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from .forms import ComplaintForm
from .models import Complaint
from django.conf import settings
from django.db.models import Count
from django.db.utils import OperationalError

# Load model & vectorizer (trained by complaints/ml/train_model.py)
MODEL_PATH = os.path.join(settings.BASE_DIR, 'complaints', 'ml', 'model.joblib')
VECT_PATH = os.path.join(settings.BASE_DIR, 'complaints', 'ml', 'vectorizer.joblib')
model = None
vectorizer = None
if os.path.exists(MODEL_PATH) and os.path.exists(VECT_PATH):
    data = joblib.load(MODEL_PATH)
    model = data.get('model')
    vectorizer = joblib.load(VECT_PATH)

KEYWORD_HIGH = ['fire','danger','accident','leak','leakage','electrocution','explosion']
INFRA_WORDS = ['road','pothole','bridge','water','pipe','supply','power','electric','garbage','trash']


def landing(request):
    return render(request, 'landing.html')


def _style_auth_form(form):
    try:
        for name, field in form.fields.items():
            cls = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (cls + ' form-control').strip()
            if not field.widget.attrs.get('placeholder'):
                field.widget.attrs['placeholder'] = field.label
    except Exception:
        pass


def register_view(request):
    from .forms import CustomUserCreationForm
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        _style_auth_form(form)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(request, username=username, password=raw_password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Registration successful. You are now logged in.')
                return redirect('submit_complaint')
            else:
                messages.warning(request, 'Registered but automatic login failed — please log in.')
                return redirect('login')
        else:
            messages.error(request, 'Registration failed. Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
        _style_auth_form(form)
    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        _style_auth_form(form)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'Logged in successfully.')
            # Staff users land on admin dashboard; citizens on submit screen
            if user.is_staff:
                return redirect('admin_dashboard')
            return redirect('submit_complaint')
        else:
            messages.error(request, 'Login failed. Please check your username and password.')
    else:
        form = AuthenticationForm()
        _style_auth_form(form)
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('landing')

@login_required
def submit_complaint(request):
    from django.http import JsonResponse
    from django.shortcuts import render, redirect
    from django.contrib import messages
    from .forms import ComplaintForm
    from .models import Complaint
    from .ml import predict as predictor

    # Staff users should manage complaints from the admin dashboard, not submit new ones
    if request.user.is_staff:
        return redirect('admin_dashboard')

    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            instance = form.save(commit=False)
            desc = (instance.description or '') + ' ' + (instance.location or '')

            # Prevent accidental duplicate complaints: same user + same text + same location, still pending
            duplicate = Complaint.objects.filter(
                user=request.user if request.user.is_authenticated else None,
                description=instance.description,
                location=instance.location,
                status='Pending',
            ).order_by('-created_at').first()

            if duplicate:
                # Reuse existing complaint instead of creating a new one
                category = duplicate.category
                priority = duplicate.priority
                comp_obj = duplicate
            else:
                category, priority = predictor.predict_category_priority(desc)
                instance.category = category
                instance.priority = priority
                instance.user = request.user if request.user.is_authenticated else None
                instance.save()
                comp_obj = instance

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                comp_id_short = str(comp_obj.id)[:8].upper()
                return JsonResponse({
                    # keep 'ok' for existing frontend JS, also include rich fields
                    'status': 'ok',
                    'category': category,
                    'priority': priority,
                    'id': comp_id_short,
                    'complaint_id': comp_id_short,
                })

            messages.success(request, f'Submitted. Category: {category}. Priority: {priority}. ID: {str(instance.id)[:8].upper()}')
            return redirect('submit_complaint')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    else:
        form = ComplaintForm()
    return render(request, 'submit_complaint.html', {'form': form})


def track_complaint(request, pk):
    comp = get_object_or_404(Complaint, pk=pk)
    return render(request, 'tracking.html', {'comp': comp})

@login_required
def history(request):
    comps = Complaint.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'history.html', {'comps': comps})

@login_required
def user_dashboard(request):
    # Staff users don't have a personal dashboard; send them to admin dashboard
    if request.user.is_staff:
        return redirect('admin_dashboard')
    try:
        comps = Complaint.objects.filter(user=request.user).order_by('-created_at')
    except OperationalError:
        comps = []
        from django.contrib import messages as _m
        _m.error(request, 'Database not ready: run migrations (python manage.py migrate)')
    return render(request, 'user_dashboard.html', {'comps': comps})


@login_required
def edit_complaint(request, pk):
    comp = get_object_or_404(Complaint, pk=pk)
    # Only allow owner or staff to edit
    if comp.user != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to edit this complaint.')
        return redirect('user_dashboard')
    
    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES, instance=comp)
        if form.is_valid():
            instance = form.save(commit=False)
            # Re-predict category and priority based on updated description
            from .ml import predict as predictor
            desc = (instance.description or '') + ' ' + (instance.location or '')
            category, priority = predictor.predict_category_priority(desc)
            instance.category = category
            instance.priority = priority
            instance.save()
            messages.success(request, f'Complaint updated. New Category: {category}, Priority: {priority}')
            return redirect('track_complaint', pk=pk)
    else:
        form = ComplaintForm(instance=comp)
    
    return render(request, 'edit_complaint.html', {'form': form, 'comp': comp})

@login_required
def delete_complaint(request, pk):
    comp = get_object_or_404(Complaint, pk=pk)
    # Only allow owner or staff to delete
    if comp.user != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to delete this complaint.')
        return redirect('user_dashboard')
    
    if request.method == 'POST':
        comp_id = comp.complaint_id
        comp.delete()
        messages.success(request, f'Complaint {comp_id} has been deleted.')
        return redirect('user_dashboard')
    
    return render(request, 'delete_complaint.html', {'comp': comp})


def is_admin(user):
    return user.is_staff

@user_passes_test(is_admin)
def admin_dashboard(request):
    total = Complaint.objects.count()
    # Treat both High and Critical as high-priority for summary count
    high = Complaint.objects.filter(priority__in=['High', 'Critical']).count()
    categories = Complaint.objects.values('category').annotate(count=Count('id'))
    priorities = Complaint.objects.values('priority').annotate(count=Count('id'))
    monthly = Complaint.objects.extra(select={'month': "strftime('%Y-%m', created_at)"}).values('month').annotate(count=Count('id')).order_by('month')
    return render(request, 'admin_dashboard.html', {
        'total': total, 'high': high,
        'categories': json.dumps(list(categories)),
        'priorities': json.dumps(list(priorities)),
        'monthly': json.dumps(list(monthly)),
    })

@user_passes_test(is_admin)
def admin_complaint_action(request):
    # Handles AJAX/fetch actions: change status or delete.
    # Accept any POST with JSON body (modern fetch API); no is_ajax() check.
    if request.method != 'POST':
        return HttpResponseBadRequest('Bad request')
    data = json.loads(request.body.decode('utf-8'))
    action = data.get('action')
    cid = data.get('id')
    if not cid:
        return JsonResponse({'status':'error','message':'Missing id'}, status=400)
    try:
        comp = Complaint.objects.get(id=cid)
    except Complaint.DoesNotExist:
        return JsonResponse({'status':'error','message':'Not found'}, status=404)
    if action == 'status':
        new = data.get('value')
        # Backwards compatibility: older frontend may send "Completed"
        if new == 'Completed':
            new = 'Verified'
        if new in dict(Complaint._meta.get_field('status').choices):
            comp.status = new
            comp.save()
            return JsonResponse({'status':'ok'})
        return JsonResponse({'status':'error','message':'Invalid status'}, status=400)
    elif action == 'verify':
        # Explicit verify action from "Mark Verified" button
        comp.status = 'Verified'
        comp.save()
        return JsonResponse({'status':'ok'})
    elif action == 'delete':
        comp.delete()
        return JsonResponse({'status':'ok'})
    return JsonResponse({'status':'error','message':'Unknown action'}, status=400)

def complaints_data_api(request):
    qs = Complaint.objects.all()
    cat = request.GET.get('category')
    pri = request.GET.get('priority')
    status = request.GET.get('status')
    if cat: qs = qs.filter(category=cat)
    if pri: qs = qs.filter(priority=pri)
    if status: qs = qs.filter(status=status)
    data = list(qs.values('id','name','phone','location','description','category','priority','status','image','created_at'))
    return JsonResponse(data, safe=False)

@login_required
def user_complaints_api(request):
    qs = Complaint.objects.filter(user=request.user).order_by('-created_at')
    data = list(qs.values('id','name','location','category','priority','status','image','created_at'))
    return JsonResponse(data, safe=False)
