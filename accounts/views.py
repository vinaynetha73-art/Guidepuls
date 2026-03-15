from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from collections import defaultdict
import json
import random
from django.contrib import admin
from .models import UserProfile,EmergencyContact,EmergencyCallHistory,EmergencyLog,Donor,FirstAidStep,FirstAidTopic,EmergencyAlert,Rescue
import math
from .models import UserLiveLocation


# ================= FIRST AID =================

def firstaid_view(request):
    topics = FirstAidTopic.objects.all()
    categories = defaultdict(list)

    for topic in topics:
        categories[topic.category].append(topic)

    all_categories = FirstAidTopic.objects.values_list('category', flat=True).distinct()

    return render(request, 'firstaid.html', {
        'categories': dict(categories),
        'all_categories': all_categories
    })
def home_page(request):
    return render(request, 'home.html')

def firstaid_detail(request, id):
    topic = FirstAidTopic.objects.get(id=id)
    steps = list(topic.steps.values_list('description', flat=True))

    return JsonResponse({
        "title": topic.title,
        "description": f"First aid steps for {topic.title}",
        "steps": steps
    })


# ================= EMERGENCY CONTACTS =================

@login_required
def save_contact(request):
    if request.method == "POST":
        data = json.loads(request.body)
        EmergencyContact.objects.create(
            user=request.user,
            name=data['name'],
            phone=data['phone']
        )
        return JsonResponse({"status": "saved"})
    return JsonResponse({"error": "Invalid request"}, status=400)


@login_required
def delete_contact(request, id):
    EmergencyContact.objects.filter(id=id, user=request.user).delete()
    return JsonResponse({"status": "deleted"})


@login_required
def get_contacts(request):
    contacts = EmergencyContact.objects.filter(user=request.user)
    data = list(contacts.values())
    return JsonResponse(data, safe=False)


# ================= CALL HISTORY =================

@login_required
def save_call_history(request):
    if request.method == "POST":
        data = json.loads(request.body)
        EmergencyCallHistory.objects.create(
            user=request.user,
            name=data.get('name'),
            phone=data.get('phone'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude')
        )
        return JsonResponse({"status": "logged"})


@login_required
def get_call_history(request):
    history = EmergencyCallHistory.objects.filter(user=request.user).order_by('-called_at')
    data = list(history.values())
    return JsonResponse(data, safe=False)


# ================= AUTH =================

def register_view(request):
    if request.method == "POST":
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        cpassword = request.POST['cpassword']

        if password != cpassword:
            messages.error(request, "Passwords do not match")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken")
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
            return redirect('register')

        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()

        send_mail(
            subject="Welcome to GuidePuls 🎉",
            message=f"Hi {username},\n\nYour account has been created successfully.\n\nStay safe!\nGuidePuls Team",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=True
        )

        messages.success(request, "Account created successfully!")
        return redirect('login')

    return render(request, 'accounts/register.html')


def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Invalid credentials!")

    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


# ================= PROFILE =================

@login_required
def profile_view(request):
    user = request.user
    profile = UserProfile.objects.get(user=user)

    contacts = EmergencyContact.objects.filter(user=user)
    calls = EmergencyCallHistory.objects.filter(user=user).order_by("-called_at")

    return render(request, "accounts/profile.html", {
    "profile": profile,
    "contacts": contacts,
    "calls": calls
})



@login_required
def update_profile(request):
    if request.method == "POST":
        user = request.user
        profile = user.userprofile

        username = request.POST.get("username").strip()
        phone = request.POST.get("phone")
        email = request.POST.get("email")

        # 🔴 Username duplicate check
        if User.objects.filter(username=username).exclude(id=user.id).exists():
            messages.error(request, "Username already exists!")
            return redirect("profile")

        # Update username
        user.username = username

        # Update phone
        profile.phone = phone

        # Update profile pic
        if request.FILES.get("profile_pic"):
            profile.profile_pic = request.FILES["profile_pic"]

        # Update email
        if email != user.email:
            user.email = email

        user.save()
        profile.save()

        messages.success(request, "Profile updated successfully!")
        return redirect("profile")

    return redirect("profile")

from django.http import JsonResponse
from django.contrib.auth.models import User

@login_required
def check_username(request):
    username = request.GET.get("username")
    exists = User.objects.filter(username=username).exclude(id=request.user.id).exists()
    return JsonResponse({"exists": exists})


# ================= DONORS =================

def donors_view(request):
    donors = Donor.objects.all()

    group = request.GET.get('group')
    place = request.GET.get('place')

    if group:
        donors = donors.filter(group__iexact=group)

    if place:
        donors = donors.filter(place__icontains=place)

    return render(request, 'donors.html', {
        'donors': donors,
        'selected_group': group,
        'selected_place': place
    })


@login_required
def donor_register(request):
    if request.method == "POST":
        name = request.POST.get("name")
        place = request.POST.get("place")
        group = request.POST.get("group")
        phone = request.POST.get("phone")

        Donor.objects.create(
            name=name,
            place=place,
            group=group.upper(),
            phone=phone
        )

        messages.success(request, "Donor registered successfully!")
        return redirect("donors")

    return render(request, "donor_register.html")


# ================= OTP EMAIL VERIFICATION =================

otp_store = {}

def send_otp(request):
    data = json.loads(request.body)
    email = data.get("email")

    otp = random.randint(100000,999999)
    otp_store[email] = otp

    send_mail(
        "GuidePuls Email Verification",
        f"Your OTP is: {otp}",
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False
    )

    return JsonResponse({"status":"sent"})


def verify_otp(request):
    data = json.loads(request.body)
    otp = int(data.get("otp"))
    email = data.get("email")

    if otp_store.get(email) == otp:
        request.session["otp_verified_email"] = email
        return JsonResponse({"status":"verified"})
    return JsonResponse({"status":"invalid"})


# ================= FORGOT PASSWORD =================

reset_otp_store = {}

def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email")
        user = User.objects.filter(email=email).first()

        if not user:
            messages.error(request, "No user found with this email")
            return redirect("forgot_password")

        otp = random.randint(100000,999999)
        reset_otp_store[email] = otp

        send_mail(
            "GuidePuls Password Reset OTP",
            f"Your OTP is: {otp}",
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False
        )

        request.session["reset_email"] = email
        return redirect("verify_reset_otp")

    return render(request, "accounts/forgot_password.html")


def verify_reset_otp(request):
    email = request.session.get("reset_email")

    if request.method == "POST":
        otp = int(request.POST.get("otp"))

        if reset_otp_store.get(email) == otp:
            return redirect("reset_password")
        else:
            messages.error(request, "Invalid OTP")

    return render(request, "accounts/verify_reset_otp.html")


def reset_password(request):
    email = request.session.get("reset_email")

    if not email:
        return redirect("forgot_password")

    if request.method == "POST":
        password = request.POST.get("password")
        cpassword = request.POST.get("cpassword")

        if password != cpassword:
            messages.error(request, "Passwords do not match")
            return redirect("reset_password")

        user = User.objects.get(email=email)
        user.set_password(password)
        user.save()

        reset_otp_store.pop(email, None)
        del request.session["reset_email"]

        messages.success(request, "Password reset successful!")
        return redirect("login")

    return render(request, "accounts/reset_password.html")
import json
import math
from datetime import timedelta

from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.contrib.auth.decorators import login_required

from .models import EmergencyAlert, Rescue, UserLiveLocation

# ==========================================
# DISTANCE CALCULATION
# ==========================================

def calculate_distance(lat1, lon1, lat2, lon2):

    R = 6371

    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)

    a = (
        math.sin(dLat/2) * math.sin(dLat/2)
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dLon/2)
        * math.sin(dLon/2)
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c


# ==========================================
# SAVE LIVE LOCATION
# ==========================================

@login_required
def save_live_location(request):

    if request.method == "POST":

        data = json.loads(request.body)

        latitude = data.get("latitude")
        longitude = data.get("longitude")

        location, created = UserLiveLocation.objects.get_or_create(
            user=request.user
        )

        location.latitude = latitude
        location.longitude = longitude
        location.save()

        return JsonResponse({"status": "saved"})

    return JsonResponse({"error": "invalid request"})


# ==========================================
# TRIGGER EMERGENCY
# ==========================================

@login_required
def trigger_emergency(request):

    location = UserLiveLocation.objects.filter(
        user=request.user
    ).first()

    if not location:
        return JsonResponse({"error": "location missing"})

    alert = EmergencyAlert.objects.create(
        victim=request.user,
        latitude=location.latitude,
        longitude=location.longitude,
        is_active=True,
        accepted_count=0
    )

    return JsonResponse({"status": "active"})
@login_required
def update_location(request):

    if request.method == "POST":

        data = json.loads(request.body)

        lat = data.get("latitude")
        lng = data.get("longitude")

        location, created = UserLiveLocation.objects.get_or_create(
            user=request.user
        )

        location.latitude = lat
        location.longitude = lng
        location.save()

        return JsonResponse({"status": "updated"})

    return JsonResponse({"error": "invalid request"})@login_required

def get_active_rescue(request):

    rescue = Rescue.objects.filter(
        rescuer=request.user,
        status="accepted",
        is_active=True
    ).select_related("alert__victim").first()

    if not rescue:
        return JsonResponse({"active": False})

    return JsonResponse({
        "active": True,
        "victim": rescue.alert.victim.username
    })
# ==========================================
# STOP EMERGENCY (VICTIM SAFE)
# ==========================================

@login_required
def stop_emergency(request):

    EmergencyAlert.objects.filter(
        victim=request.user,
        is_active=True
    ).update(is_active=False)

    Rescue.objects.filter(
        alert__victim=request.user,
        is_active=True
    ).update(is_active=False)

    return JsonResponse({"status":"stopped"})

# ==========================================
# CLOSE EMERGENCY
# ==========================================

@login_required
def close_emergency(request):

    alert = EmergencyAlert.objects.filter(
        victim=request.user,
        is_active=True
    ).first()

    if not alert:
        return JsonResponse({"status": "none"})

    # deactivate alert
    alert.is_active = False
    alert.save()

    # deactivate helpers
    Rescue.objects.filter(
        alert=alert,
        is_active=True
    ).update(
        is_active=False,
        victim_closed=True,
        left_at=timezone.now()
    )

    return JsonResponse({"status": "closed"})

# ==========================================
# GET NEARBY ALERTS
# ==========================================

from django.utils import timezone

@login_required
def get_nearby_alerts(request):

    user = request.user

    # helper already helping someone
    if Rescue.objects.filter(
        rescuer=user,
        status="accepted",
        is_active=True
    ).exists():
        return JsonResponse({"alerts": []})

    # user already victim with active emergency
    if EmergencyAlert.objects.filter(
        victim=user,
        is_active=True
    ).exists():
        return JsonResponse({"alerts": []})

    my_location = UserLiveLocation.objects.filter(
        user=user
    ).first()

    if not my_location:
        return JsonResponse({"alerts": []})

    alerts = EmergencyAlert.objects.filter(
        is_active=True
    ).exclude(victim=user)

    nearby_alerts = []

    # helper profile
    profile = UserProfile.objects.get(user=user)
    experience = profile.rescue_count
    vehicle = getattr(profile, "vehicle", "bike")

    # vehicle speed
    if vehicle == "car":
        speed = 35
    elif vehicle == "bike":
        speed = 40
    else:
        speed = 5

    for alert in alerts:

        # helper already interacted
        if Rescue.objects.filter(
            alert=alert,
            rescuer=user
        ).exists():
            continue

        # capacity full
        if alert.accepted_count >= alert.max_capacity:
            continue

        victim_location = UserLiveLocation.objects.filter(
            user=alert.victim
        ).first()

        victim_lat = alert.latitude
        victim_lon = alert.longitude

        if victim_location:
            victim_lat = victim_location.latitude
            victim_lon = victim_location.longitude

        distance = calculate_distance(
            my_location.latitude,
            my_location.longitude,
            victim_lat,
            victim_lon
        )

        # -------- PHASE-4 AUTO ESCALATION --------
        time_passed = timezone.now() - alert.created_at

        if time_passed.seconds > 30:
            radius = 12
        else:
            radius = 7
        # ----------------------------------------

        if distance <= radius:

            # dynamic ETA
            eta = max(1, round((distance / speed) * 60))

            # smart helper score
            score = distance - (experience * 0.2)

            nearby_alerts.append({
                "id": alert.id,
                "victim": alert.victim.username,
                "latitude": victim_lat,
                "longitude": victim_lon,
                "distance": round(distance, 2),
                "eta": eta,
                "score": round(score, 2)
            })

    # smart sorting (best helper first)
    nearby_alerts.sort(key=lambda x: x["score"])

    return JsonResponse({"alerts": nearby_alerts})

# ==========================================
# ACCEPT RESCUE
# ==========================================

@login_required
def accept_rescue(request):

    data = json.loads(request.body)

    alert_id = data.get("alert_id")

    alert = EmergencyAlert.objects.filter(
        id=alert_id,
        is_active=True
    ).first()

    if not alert:
        return JsonResponse({"status": "expired"})

    # create rescue
    Rescue.objects.create(
        alert=alert,
        rescuer=request.user,
        status="accepted",
        is_active=True
    )

    # increase accepted count
    alert.accepted_count += 1

    if alert.accepted_count >= alert.max_capacity:
        alert.is_active = False

    alert.save()

    # update helper experience
    profile = UserProfile.objects.get(user=request.user)
    profile.rescue_count += 1
    profile.save()

    return JsonResponse({"status": "accepted"})

# ==========================================
# DENY RESCUE
# ==========================================

@login_required
def deny_rescue(request):

    data = json.loads(request.body)

    alert_id = data.get("alert_id")

    alert = EmergencyAlert.objects.filter(id=alert_id).first()

    if not alert:
        return JsonResponse({"status": "error"})

    Rescue.objects.create(
        alert=alert,
        rescuer=request.user,
        status="rejected",
        is_active=False
    )

    return JsonResponse({"status": "rejected"})


# ==========================================
# LEAVE RESCUE
# ==========================================

from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

@login_required
def leave_rescue(request):

    if request.method != "POST":
        return JsonResponse({"status":"invalid"})

    rescue = Rescue.objects.filter(
        rescuer=request.user,
        status="accepted",
        is_active=True
    ).select_related("alert").first()

    if not rescue:
        return JsonResponse({"status": "none"})

    alert = rescue.alert

    rescue.is_active = False
    rescue.left_at = timezone.now()
    rescue.save()

    alert.accepted_count = max(0, alert.accepted_count - 1)

    if alert.accepted_count < alert.max_capacity:
        alert.is_active = True

    alert.save()

    return JsonResponse({"status": "left"})
#==========================================
# COMPLETE RESCUE (ARRIVED)
# ==========================================

@login_required
def complete_rescue(request):

    rescue = Rescue.objects.filter(
        rescuer=request.user,
        is_active=True
    ).first()

    if rescue:

        rescue.status = "completed"
        rescue.is_active = False
        rescue.completed = True
        rescue.completed_at = timezone.now()

        rescue.save()

    return JsonResponse({"status": "completed"})


# ==========================================
# GET LIVE LOCATIONS
# ==========================================

@login_required
def get_live_locations(request):

    rescue = Rescue.objects.filter(
        rescuer=request.user,
        status="accepted",
        is_active=True
    ).select_related("alert__victim").first()

    if not rescue:
        return JsonResponse({"error": "No active rescue"})

    alert = rescue.alert

    helper_location = UserLiveLocation.objects.filter(
        user=request.user
    ).first()

    victim_location = UserLiveLocation.objects.filter(
        user=alert.victim
    ).first()

    if not helper_location or not victim_location:
        return JsonResponse({"error": "location missing"})

    return JsonResponse({

        "helper":{
            "latitude": helper_location.latitude,
            "longitude": helper_location.longitude
        },

        "victim":{
            "latitude": victim_location.latitude,
            "longitude": victim_location.longitude,
            "name": alert.victim.username
        }

    })
# ==========================================
# CHECK HELPING STATUS
# ==========================================

@login_required
def check_helping_status(request):

    rescue = Rescue.objects.filter(
        rescuer=request.user,
        status="accepted",
        is_active=True
    ).select_related("alert__victim").first()

    if not rescue:
        return JsonResponse({"helping": False})

    return JsonResponse({
        "helping": True,
        "victim": rescue.alert.victim.username
    })

@login_required
def check_alert_status(request):

    rescue = Rescue.objects.filter(
        rescuer=request.user,
        is_active=True
    ).first()

    if not rescue:
        return JsonResponse({"safe": True, "victim": "Victim"})

    if not rescue.alert.is_active:
        return JsonResponse({
            "safe": True,
            "victim": rescue.alert.victim.username
        })

    return JsonResponse({"safe": False})

# ==========================================
# GET ACTIVE HELPERS (VICTIM SIDE)
# ==========================================

@login_required
def get_active_helpers(request):

    alert = EmergencyAlert.objects.filter(
        victim=request.user,
        is_active=True
    ).first()

    if not alert:
        return JsonResponse({"active": False})

    rescues = Rescue.objects.filter(
        alert=alert,
        status="accepted",
        is_active=True
    ).select_related("rescuer")

    helpers = [
        {"username": r.rescuer.username}
        for r in rescues
    ]

    return JsonResponse({
        "active": True,
        "count": rescues.count(),
        "max": alert.max_capacity,
        "helpers": helpers
    })


# ==========================================
# CHECK MY EMERGENCY
# ==========================================

@login_required
def check_my_emergency(request):

    alert = EmergencyAlert.objects.filter(
        victim=request.user,
        is_active=True
    ).first()

    if not alert:
        return JsonResponse({"active": False})

    return JsonResponse({"active": True})

@login_required
def send_emergency_alert(request):

    victim = request.user

    # users who are already helping
    busy_helpers = Rescue.objects.filter(
        is_active=True
    ).values_list("rescuer_id", flat=True)

    helpers = User.objects.exclude(
        id__in=busy_helpers
    ).exclude(
        id=victim.id
    )

    for helper in helpers:
        EmergencyAlert.objects.create(
            victim=victim,
            helper=helper
        )

    return JsonResponse({"status":"alert sent"})

@login_required
def live_tracking(request):

    return render(request, "live_tracking.html")