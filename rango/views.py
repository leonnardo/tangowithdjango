from datetime import datetime

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from registration.backends.simple.views import RegistrationView

from rango.models import Category, Page
from .forms import CategoryForm, PageForm, UserForm, UserProfileForm
from .bing_search import run_query


# Helper Functions
def get_server_side_cookie(request, cookie, default_val=None):
    val = request.session.get(cookie)
    if not val:
        val = default_val
    return val


def visitor_cookie_handler(request):
    visits = int(get_server_side_cookie(request, 'visits', '1'))
    last_visit_cookie = get_server_side_cookie(request,
                                               'last_visit',
                                               str(datetime.now()))
    last_visit_time = datetime.strptime(last_visit_cookie[:-7],
                                        '%Y-%m-%d %H:%M:%S')

    if (datetime.now() - last_visit_time).days > 0:
        visits += 1
        request.session['last_visit'] = str(datetime.now())
    else:
        visits = 1
        request.session['last_visit'] = last_visit_cookie

    request.session['visits'] = visits


# Views
def index(request):
    """
    Consulta o banco de dados por uma lista de todas as categorias atualmente armazenadas
    Ordena as categorias pelo numero de likes de forma decrescente.
    Pega apenas as 5 categorias com mais likes, ou todas se existirem menos de 5 categorias.
    Poe a lista no dicionario context_dict que sera passado para o template engine.
    """
    category_list = Category.objects.order_by('-likes')[:5]
    pages_list = Page.objects.order_by('-views')[:5]

    context = {'categories': category_list, 'pages': pages_list}
    visitor_cookie_handler(request)
    context['visits'] = request.session['visits']
    return render(request, 'rango/index.html', context)


def about(request):
    context = { 'name' : 'Leonnardo'}
    visitor_cookie_handler(request)
    context['visits'] = request.session['visits']
    return render(request,'rango/about.html', context=context)


def show_category(request, category_name_slug):
    context_dict = {}
    try:
        category = Category.objects.get(slug=category_name_slug)
        pages = Page.objects.filter(category=category)
        context_dict['category'] = category
        context_dict['pages'] = pages


    except Category.DoesNotExist:
        context_dict['category'] = None
        context_dict['pages'] = None

    return render(request, 'rango/category.html', context_dict)


@login_required
def add_category(request):
    """
    Form to add a new category
    """
    form = CategoryForm()

    # Is HTTP POST?
    if request.method == 'POST':
        form = CategoryForm(request.POST)

        # Is this form a valid form?
        if form.is_valid():
            # Save new category to the database
            form.save(commit=True)
            # now, just return to index page to show new category added
            # in index page
            return index(request)
        else:
            # Supplied form has errors, print them to the terminal!
            print(form.errors)

    return render(request, 'rango/add_category.html', {'form': form})


@login_required
def add_page(request, category_name_slug):
    try:
        category = Category.objects.get(slug=category_name_slug)
    except Category.DoesNotExist:
        category = None

    form = PageForm()
    if request.method == 'POST':
        form = PageForm(request.POST)
        if form.is_valid():
            if category:
                page = form.save(commit=False)
                page.category = category
                page.views = 0
                page.save()
                return show_category(request, category_name_slug)
        else:
            print(form.errors)

    context_dict = { 'form': form, 'category': category }
    return render(request, 'rango/add_page.html', context_dict)


def register(request):
    # A boolean value for telling the template
    # whether the registration was successful.
    # Set to False initially. Code changes value to # True when registration succeeds.
    registered = False

    # In HTTP POST, we're interested in processing form data
    if request.method == 'POST':
        # Attempt to grab information from the raw form information. 
        # Note that we make use of both UserForm and UserProfileForm.
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            # save user's form data to the database
            user = user_form.save()

            # hash password and update user
            user.set_password(user.password)
            user.save()

            # no need to commit now until we're ready to save
            profile = profile_form.save(commit=False)
            profile.user = user

            # save user picture if provided
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            # ready to save UserProfile instance
            profile.save()

            # Registered user now
            registered = True
        
        else:
            print(user_form.errors, profile_form.errors)

    # not HTTP POST, render our blank forms
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    # render template
    return render(request,
                  'rango/register.html',
                  {'user_form': user_form,
                   'profile_form': profile_form,
                   'registered':  registered})


def user_login(request):
    # If the request is a HTTP POST, try to pull out the relevant information.
    if request.method == 'POST':
        # Gather the username and password provided by the user.
        # This information is obtained from the login form.
        # We use request.POST.get('<variable>') as opposed
        # to request.POST['<variable>'], because the
        # request.POST.get('<variable>') returns None if the
        # value does not exist, while request.POST['<variable>'] # will raise a KeyError exception.
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Use Django's machinery to attempt to see if the username/password
        # combination is valid - a User object is returned if it is.
        user = authenticate(username=username, password=password)

        # if theres a user object, so details are correct
        # if none, no user with matching credentials was found
        if user:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect(reverse('index'))
            else:
                return HttpResponse('Your Rango account is disabled.')
        else:
            print("Invalid login details: {0}, {1}".format(username, password))
            return HttpResponse("Invalid login details supplied.")

    else:
        return render(request, 'rango/login.html', {})


def search(request):
    result_list = []
    query_string = None

    if request.method == 'POST':
        query_string = request.POST['query']
        query = query_string.strip()
        if query:
            result_list = run_query(query)
    return render(request, 'rango/search.html', {'query': query_string,
                                                 'result_list': result_list})


def track_url(request, page_id):
    if page_id:
        page = Page.objects.get(id=page_id)
        page.views += 1
        page.save()
        return redirect(page.url)

    return redirect(reverse('index'))


@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('index'))


class MyRegistrationView(RegistrationView):
    def get_success_url(self, user):
        return '/rango/'
