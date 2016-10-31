from django.shortcuts import render
from rango.models import Category, Page
from .forms import CategoryForm, PageForm

def index(request):
    """
    Consulta o banco de dados por uma lista de todas as categorias atualmente armazenadas
    Ordena as categorias pelo numero de likes de forma decrescente.
    Pega apenas as 5 categorias com mais likes, ou todas se existirem menos de 5 categorias.
    Poe a lista no dicionario context_dict que sera passado para o template engine.
    """
    category_list = Category.objects.order_by('-likes')[:5]
    pages_list = Page.objects.order_by('-views')[:5]

    context_dict = {'categories': category_list, 'pages': pages_list}
    return render(request, 'rango/index.html', context_dict)

def about(request):
    context = { 'name' : 'Leonnardo'}
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
