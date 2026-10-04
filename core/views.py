from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from .models import Trainee, ConsentLedger, VerificationEvent, Provider
import random

# Avatar photos per role (Pexels stock photos)
AVATARS = {
    'gov_admin': 'https://images.pexels.com/photos/5668772/pexels-photo-5668772.jpeg?auto=compress&cs=tinysrgb&w=200',
    'employer1': 'https://images.pexels.com/photos/1181686/pexels-photo-1181686.jpeg?auto=compress&cs=tinysrgb&w=200',
    'trainee_demo': 'https://images.pexels.com/photos/1239291/pexels-photo-1239291.jpeg?auto=compress&cs=tinysrgb&w=200',
    'provider1': 'https://images.pexels.com/photos/3184292/pexels-photo-3184292.jpeg?auto=compress&cs=tinysrgb&w=200',
}


def home(request):
    trainees_count = Trainee.objects.count()
    verified_count = Trainee.objects.filter(score_level='HIGH').count()
    employers_count = Trainee.objects.exclude(company_name='').values('company_name').distinct().count()
    providers_count = Provider.objects.count()

    stats = {
        'trained': '4.12L',
        'verified': '1.02L',
        'employers': '8,650',
        'providers': providers_count,
        'trainees_db': trainees_count,
        'verified_db': verified_count,
        'employers_db': employers_count,
    }
    return render(request, 'home.html', {'stats': stats})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials. Use gov_admin / employer1 / trainee_demo / provider1 with password 1234')
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('home')


def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')
    username = request.user.username
    trainees = Trainee.objects.all()
    providers = Provider.objects.all()
    consents = ConsentLedger.objects.all()

    context = {
        'trainees': trainees[:10],
        'providers': providers,
        'total_trainees': trainees.count(),
        'total_verified': trainees.filter(score_level='HIGH').count(),
        'active_consents': consents.filter(status='Active').count(),
        'revoked_consents': consents.filter(status='Revoked').count(),
    }

    if username.startswith('gov_'):
        context['dashboard_title'] = 'Government Admin Dashboard'
        context['dashboard_template'] = 'dashboards/gov.html'
    elif username.startswith('employer'):
        context['dashboard_title'] = 'Employer Dashboard'
        context['dashboard_template'] = 'dashboards/employer.html'
    elif username.startswith('trainee'):
        context['dashboard_title'] = 'My Dashboard'
        my_trainee = trainees.filter(full_name__icontains='Rohan').first() or trainees.first()
        context['my_trainee'] = my_trainee
        context['dashboard_template'] = 'dashboards/trainee.html'
    elif username.startswith('provider'):
        context['dashboard_title'] = 'Provider Dashboard'
        provider = providers.filter(provider_id='TP-001').first() or providers.first()
        context['my_provider'] = provider
        context['provider_trainees'] = trainees.filter(provider=provider) if provider else []
        context['dashboard_template'] = 'dashboards/provider.html'
    else:
        context['dashboard_title'] = 'Dashboard'
        context['dashboard_template'] = 'dashboards/gov.html'

    return render(request, 'dashboard.html', context)


def trainee_form(request):
    if request.method == 'POST':
        master_id = f"MH{random.randint(100000, 999999)}"
        trainee = Trainee.objects.create(
            master_id=master_id,
            full_name=request.POST.get('full_name', ''),
            mobile=request.POST.get('mobile', ''),
            district=request.POST.get('district', 'Pune'),
            course=request.POST.get('course', 'Electrician'),
            company_name=request.POST.get('company_name', ''),
            salary=request.POST.get('salary', 0),
            salary_slip=request.FILES.get('salary_slip'),
            shop_photo=request.FILES.get('shop_photo'),
            confidence_score=20,
        )
        VerificationEvent.objects.create(trainee=trainee, type='self_declaration', points=20)

        consent_given = request.POST.get('consent') == 'on'
        if consent_given:
            consent_id = f"CN{random.randint(100000, 999999)}"
            ConsentLedger.objects.create(
                consent_id=consent_id,
                trainee=trainee,
                status='Active',
                duration_months=12,
            )

        messages.success(request, f'Registration successful! Your Master ID: {master_id}')
        return redirect('verification_detail', trainee_id=trainee.id)

    districts = [d[0] for d in Trainee.DISTRICT_CHOICES]
    courses = [c[0] for c in Trainee.COURSE_CHOICES]
    return render(request, 'trainee_form.html', {'districts': districts, 'courses': courses})


def consent_ledger(request):
    consents = ConsentLedger.objects.all().order_by('-granted_at')
    total = consents.count()
    active = consents.filter(status='Active').count()
    revoked = consents.filter(status='Revoked').count()
    return render(request, 'consent_ledger.html', {
        'consents': consents,
        'total': total,
        'active': active,
        'revoked': revoked,
        'display_total': '4.12L',
        'display_active': '3.80L',
        'display_revoked': '32k',
    })


def revoke_consent(request, consent_id):
    consent = get_object_or_404(ConsentLedger, id=consent_id)
    consent.status = 'Revoked'
    consent.revoked_at = timezone.now()
    consent.save()
    messages.success(request, f'Consent {consent.consent_id} has been revoked.')
    return redirect('consent_ledger')


def verification(request, trainee_id=None):
    trainees = Trainee.objects.all()
    selected = None
    events = []
    if trainee_id:
        selected = get_object_or_404(Trainee, id=trainee_id)
        events = selected.verification_events.all().order_by('-created_at')
    return render(request, 'verification.html', {
        'trainees': trainees,
        'selected': selected,
        'events': events,
    })


def verify_otp(request, trainee_id):
    trainee = get_object_or_404(Trainee, id=trainee_id)
    if request.method == 'POST':
        otp_entered = request.POST.get('otp', '').strip()
        otp_sent = request.session.get('otp_sent', '000000')
        if otp_entered == otp_sent:
            if not trainee.employer_otp_verified:
                trainee.employer_otp_verified = True
                trainee.confidence_score += 40
                trainee.save()
                VerificationEvent.objects.create(trainee=trainee, type='employer_otp', points=40)
                messages.success(request, f'OTP Verified! +40 points. New score: {trainee.confidence_score}')
            else:
                messages.info(request, 'Employer OTP already verified.')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')
        return redirect('verification_detail', trainee_id=trainee.id)

    otp = str(random.randint(100000, 999999))
    request.session['otp_sent'] = otp
    return JsonResponse({'otp': otp, 'trainee_id': trainee.id, 'master_id': trainee.master_id})


def confidence_engine(request):
    trainees = Trainee.objects.all()
    selected = None
    checklist = []
    if request.method == 'POST' or request.GET.get('trainee_id'):
        tid = request.POST.get('trainee_id') or request.GET.get('trainee_id')
        if tid:
            selected = get_object_or_404(Trainee, id=tid)

    if selected:
        checklist = [
            {'label': 'Self Declaration', 'points': 20, 'done': selected.confidence_score >= 20},
            {'label': 'Salary Slip Upload', 'points': 15, 'done': bool(selected.salary_slip)},
            {'label': 'Bank Verification', 'points': 10, 'done': selected.bank_verified},
            {'label': 'Udyam Verification', 'points': 15, 'done': selected.udyam_verified},
            {'label': 'Employer OTP Verification', 'points': 40, 'done': selected.employer_otp_verified},
        ]

    return render(request, 'confidence_engine.html', {
        'trainees': trainees,
        'selected': selected,
        'checklist': checklist,
    })


def provider_ranking(request):
    providers = Provider.objects.all().order_by('-placement')
    return render(request, 'provider_ranking.html', {'providers': providers})


def fraud_detection(request):
    providers = Provider.objects.all()
    fraud_list = []
    for p in providers:
        flags = []
        if p.placement >= 80 and p.retention <= 20:
            flags.append('High placement but low retention - possible ghost placements')
            p.fraud_status = 'red_flag'
            p.save()
        elif p.placement > 70 and p.retention < 40:
            flags.append('Suspicious placement-retention gap')
            if p.fraud_status == 'clean':
                p.fraud_status = 'suspicious'
                p.save()
        else:
            flags.append('No anomaly detected')

        fraud_list.append({
            'provider': p,
            'flags': flags,
            'insight': flags[0] if flags else '',
        })
    return render(request, 'fraud_detection.html', {'fraud_list': fraud_list})


def seed_data(request):
    User.objects.filter(username__in=['gov_admin', 'employer1', 'trainee_demo', 'provider1']).delete()
    Trainee.objects.all().delete()
    Provider.objects.all().delete()
    ConsentLedger.objects.all().delete()
    VerificationEvent.objects.all().delete()

    for uname in ['gov_admin', 'employer1', 'trainee_demo', 'provider1']:
        User.objects.create_user(username=uname, password='1234')

    provider1 = Provider.objects.create(
        name='ITI Pune Vocational Training Center',
        provider_id='TP-001',
        placement=85.0,
        retention=22.0,
        fraud_status='red_flag',
        confidence=45.0,
        trainees_count=120,
    )
    Provider.objects.create(
        name='Mumbai Skill Development Institute',
        provider_id='TP-002',
        placement=72.0,
        retention=55.0,
        fraud_status='suspicious',
        confidence=68.0,
        trainees_count=95,
    )
    Provider.objects.create(
        name='Nagpur Industrial Training Council',
        provider_id='TP-003',
        placement=65.0,
        retention=70.0,
        fraud_status='clean',
        confidence=85.0,
        trainees_count=80,
    )

    trainee_data = [
        ('Rohan Patil', '9876543210', 'Pune', 'Electrician', 'Tata Motors', 18000, True, True, True),
        ('Sneha Deshmukh', '9823456712', 'Mumbai', 'Tailoring', 'Reliance Retail', 12000, True, False, True),
        ('Amit Kulkarni', '9923456789', 'Nagpur', 'Welder', 'L&T Construction', 22000, True, True, True),
        ('Priya Jadhav', '9812345678', 'Nashik', 'Beauty & Wellness', 'Naturals Salon', 10000, False, False, False),
        ('Vikram Shinde', '9834567812', 'Aurangabad', 'Automotive', 'Bajaj Auto', 15000, True, False, False),
    ]

    for i, (name, mobile, district, course, company, salary, bank, udyam, otp) in enumerate(trainee_data, 1):
        score = 20
        if bank:
            score += 10
        if udyam:
            score += 15
        if otp:
            score += 40
        trainee = Trainee.objects.create(
            master_id=f"MH{100000 + i}",
            full_name=name,
            mobile=mobile,
            district=district,
            course=course,
            company_name=company,
            salary=salary,
            confidence_score=score,
            bank_verified=bank,
            udyam_verified=udyam,
            employer_otp_verified=otp,
            provider=provider1,
        )
        trainee.save()
        VerificationEvent.objects.create(trainee=trainee, type='self_declaration', points=20)
        if bank:
            VerificationEvent.objects.create(trainee=trainee, type='bank', points=10)
        if udyam:
            VerificationEvent.objects.create(trainee=trainee, type='udyam', points=15)
        if otp:
            VerificationEvent.objects.create(trainee=trainee, type='employer_otp', points=40)

        ConsentLedger.objects.create(
            consent_id=f"CN{200000 + i}",
            trainee=trainee,
            status='Active' if i <= 4 else 'Revoked',
            duration_months=12,
            revoked_at=timezone.now() if i == 5 else None,
        )

    messages.success(request, 'Seed data created: 4 users, 3 providers, 5 trainees with consents and verification events.')
    return redirect('home')
