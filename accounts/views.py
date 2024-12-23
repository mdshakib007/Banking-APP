from django.shortcuts import render, redirect
from django.views.generic import FormView, View, TemplateView
from accounts.forms import RegistrationForm, UserUpdateForm
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from transactions.views import send_transaction_email

class UserRegistrationView(FormView):
    template_name = 'accounts/user_registration.html'
    form_class = RegistrationForm
    success_url = reverse_lazy('profile')
    
    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)


class UserLoginView(LoginView):
    template_name = 'accounts/user_login.html'
    
    def get_success_url(self):
        return reverse_lazy('profile')

@login_required
def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, "Successfully Logged Out!")
        return redirect('login')


class UserAccountUpdateView(LoginRequiredMixin, View):
    template_name = 'accounts/user_update_profile.html'

    def get(self, request):
        form = UserUpdateForm(instance=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile Information Updated Successfully!")
            return redirect('profile') 
        return render(request, self.template_name, {'form': form})
    


class UserChangePassword(LoginRequiredMixin, View):
    template_name = 'accounts/change_password.html'

    def get(self, request):
        form = PasswordChangeForm(user=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()  
            update_session_auth_hash(request, user) 
            messages.success(request, "Password changed successfully!")
            send_transaction_email(request.user, 0, "Security Alert", "accounts/change_password_email.html")
            return redirect('profile') 
        else:
            messages.error(request, "Please correct the error(s) below.")
        return render(request, self.template_name, {'form': form})



class UserProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/user_profile.html'

