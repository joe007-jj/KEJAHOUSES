from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from .forms import CustomUserCreationForm, ProductForm, ReviewForm, ProductImageFormSet, ProductVideoFormSet, UserForm, ProfileForm
from .models import Product, Review, Profile
from django.http import HttpResponseForbidden
import logging

logger = logging.getLogger(__name__)

@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            return redirect('product_list')
    else:
        form = ReviewForm()
    return render(request, 'add_review.html', {'form': form, 'product': product})

def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, owner=request.user)
    if request.user.groups.filter(name='HouseOwner').exists() and product.owner == request.user:
        product.delete()
        return redirect('product_list')
    else:
        return HttpResponseForbidden("You cannot delete this product.")

@login_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if product.owner != request.user:
        return redirect('product_list')

    if request.method == 'POST':
        product_form = ProductForm(request.POST, instance=product)
        image_formset = ProductImageFormSet(request.POST, request.FILES, instance=product)
        video_formset = ProductVideoFormSet(request.POST, request.FILES, instance=product)
        if product_form.is_valid() and image_formset.is_valid() and video_formset.is_valid():
            product_form.save()
            image_formset.save()
            video_formset.save()
            return redirect('product_list')
    else:
        product_form = ProductForm(instance=product)
        image_formset = ProductImageFormSet(instance=product)
        video_formset = ProductVideoFormSet(instance=product)

    return render(request, 'edit_product.html', {'product_form': product_form, 'image_formset': image_formset, 'video_formset': video_formset})

def home(request):
    category = request.GET.get('category')
    if category:
        products = Product.objects.filter(category=category)
    else:
        products = Product.objects.all()

    return render(request, 'home.html', {'products': products})


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            role = form.cleaned_data.get('role')
            group_name = 'HouseOwner' if role == 'house_owner' else 'Tenant'
            group = Group.objects.get(name=group_name)
            user.groups.add(group)
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        return redirect('product_list')


@login_required
def list_product(request):
    is_house_owner = request.user.groups.filter(name='HouseOwner').exists()
    logger.debug(f"User: {request.user.username}, Is House Owner: {is_house_owner}")

    if not is_house_owner:
        return redirect('product_list')

    if request.method == 'POST':
        product_form = ProductForm(request.POST)
        image_formset = ProductImageFormSet(request.POST, request.FILES, instance=Product())
        video_formset = ProductVideoFormSet(request.POST, request.FILES, instance=Product())
        if product_form.is_valid() and image_formset.is_valid() and video_formset.is_valid():
            product = product_form.save(commit=False)
            product.owner = request.user
            product.save()
            image_formset.instance = product
            image_formset.save()
            video_formset.instance = product
            video_formset.save()
            return redirect('product_list')
    else:
        product_form = ProductForm()
        image_formset = ProductImageFormSet(instance=Product())
        video_formset = ProductVideoFormSet(instance=Product())

    return render(request, 'list_product.html', {'product_form': product_form, 'image_formset': image_formset, 'video_formset': video_formset})


@login_required
def product_list(request):
    category = request.GET.get('category', None)
    if category in dict(Product.CATEGORY_CHOICES).keys():
        products = Product.objects.filter(category=category)
    else:
        products = Product.objects.all()
    is_house_owner = request.user.groups.filter(name='HouseOwner').exists()
    logger.debug(f"User: {request.user.username}, Is House Owner: {is_house_owner}")
    return render(request, 'product_list.html', {'products': products, 'is_house_owner': is_house_owner})

def profile(request):
    user = request.user

    if not hasattr(user, 'profile'):
        profile = Profile(user=user)
        profile.save()

    products = Product.objects.filter(owner=user)

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('profile')
    else:
        user_form = UserForm(instance=user)
        profile_form = ProfileForm(instance=user.profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'products': products
    }

    return render(request, 'profile.html', context)