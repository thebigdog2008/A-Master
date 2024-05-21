from django.shortcuts import render


def store_redirect(request, name):
    return render(request, "store-redirect.html", {"first_name": name})
