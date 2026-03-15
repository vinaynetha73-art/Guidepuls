from django.shortcuts import render

def emergency_home(request):
    return render(request, 'emergency.html')
def home_page(request):
    return render(request, 'home.html')
def donors_page(request):
    all_donors = [
        {"name":"Ravi", "group":"A+", "place":"Hyderabad", "phone":"9876543210"},
        {"name":"Sita", "group":"O+", "place":"Narmul", "phone":"9123456789"},
        {"name":"Kiran", "group":"B+", "place":"Warangal", "phone":"9988776655"},
        {"name":"Anil", "group":"AB+", "place":"Karimnagar", "phone":"9012345678"},
    ]

    group = request.GET.get("group")
    place = request.GET.get("place")

    donors = all_donors

    if group:
        donors = [d for d in donors if d["group"] == group]

    if place:
        donors = [d for d in donors if place.lower() in d["place"].lower()]

    return render(request, 'donors.html', {
        "donors": donors,
        "selected_group": group,
        "selected_place": place
    })

