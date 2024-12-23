from django.contrib import admin
from accounts.models import UserAddress, UserBankAccount

admin.site.register(UserBankAccount)
admin.site.register(UserAddress)