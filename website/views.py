import openai
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.urls import reverse

from website.forms import SignUpForm
from website.models import Code

# Assuming settings.KEY and settings.SELECTED_LANGUAGES are properly configured in your Django settings

KEY = settings.KEY
LANGUAGES = settings.SELECTED_LANGUAGES


def check_language(request, lang, code):
    if lang == "Select programming language":
        messages.success(request, "Please select a programming language.")
        return render(request, "home.html", {"lang_list": LANGUAGES, "code": code, "lang": lang})
    return None


def process_request(request, template_name, prompt, code, lang, explain=False):
    try:
        openai.api_key = KEY
        response = openai.Completion.create(
            engine="davinci-codex",
            prompt=prompt,
            temperature=0,
            max_tokens=1000,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )

        if explain:
            response = response.choices[0].text.replace("\n", "<br>")

        response = response.choices[0].text.strip()

        record = Code(question=code, code_answer=response, language=lang, user=request.user)
        record.save()

        share_url = request.build_absolute_uri(reverse("share", args=[record.id]))

        return render(
            request, template_name, {"lang_list": LANGUAGES, "response": response, "lang": lang, "share_url": share_url}
        )

    except Exception as e:
        return render(request, template_name, {"lang_list": LANGUAGES, "response": str(e), "lang": lang})


def home(request):
    if request.method == "POST":
        code = request.POST.get("code")
        lang = request.POST.get("lang")

        error_response = check_language(request, lang, code)
        if error_response:
            return error_response

        prompt = f"Respond only with code. Fix this {lang} code: {code}"
        return process_request(request, "home.html", prompt, code, lang)

    return render(request, "home.html", {"lang_list": LANGUAGES})


def suggest(request):
    if request.method == "POST":
        code = request.POST.get("code")
        lang = request.POST.get("lang")

        error_response = check_language(request, lang, code)
        if error_response:
            return error_response

        prompt = f"Respond only with code. {code}"
        return process_request(request, "suggest.html", prompt, code, lang)

    return render(request, "suggest.html", {"lang_list": LANGUAGES})


def explain_code(request):
    if request.method == "POST":
        code = request.POST.get("code")
        lang = request.POST.get("lang")

        error_response = check_language(request, lang, code)
        if error_response:
            return error_response

        prompt = f"Explain the following {lang} code: \n {code}"
        return process_request(request, "explain.html", prompt, code, lang)

    return render(request, "explain.html", {"lang_list": LANGUAGES})


def share(request, record_id):
    record = Code.objects.get(pk=record_id)
    share_url = request.build_absolute_uri(reverse("share", args=[record_id]))
    return render(request, "share.html", {"record": record, "share_url": share_url})


def login_user(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "You are logged in.")
            return redirect("welcome")
        else:
            messages.success(request, "Login error. Please try again...")
            return redirect("home")
    else:
        return render(request, "home.html", {})


def logout_user(request):
    logout(request)
    messages.success(request, "You are logged out.")
    return redirect("home")


def register_user(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password1"]
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, "You are registered!")
            return redirect("welcome")

    else:
        form = SignUpForm()

    return render(request, "register.html", {"form": form})


def past(request):
    if request.user.is_authenticated:
        code = Code.objects.filter(user_id=request.user.id)
        return render(request, "past.html", {"code": code})
    else:
        messages.success(request, "You must be logged in to view past code.")
        return redirect("home")


def delete_past(request, past_id):
    past = Code.objects.get(pk=past_id)
    past.delete()
    messages.success(request, "Successfully deleted.")
    return redirect("past")


def delete_all_past(request):
    if request.user.is_authenticated:
        Code.objects.filter(user_id=request.user.id).delete()
        messages.success(request, "Successfully deleted all history.")
    else:
        messages.success(request, "You must be logged in to delete history.")
    return redirect("past")


def welcome(request):
    return render(request, "welcome.html")
