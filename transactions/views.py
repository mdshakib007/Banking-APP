from datetime import datetime
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.http import HttpResponse
from django.views.generic import CreateView, ListView
from django.db.models import Sum
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template.loader import render_to_string
from transactions.constants import DEPOSIT, WITHDRAWAL,LOAN, LOAN_PAID, SEND_MONEY, RECEIVED_MONEY
from transactions.forms import DepositForm, WithdrawForm, LoanRequestForm, SendMoneyForm
from transactions.models import Transaction
from accounts.models import UserBankAccount


def send_transaction_email(user, amount, subject, template, to_user=None):
    if to_user is not None:
        message = render_to_string(template,{
            'user' : user,
            'to_user' : to_user,
            'amount' : amount
        })
    else:
        message = render_to_string(template,{
            'user' : user,
            'amount' : amount
        })

    send_email = EmailMultiAlternatives(subject, '', to=[user.email])
    send_email.attach_alternative(message, 'text/html')
    send_email.send()


class TransactionCreateMixin(LoginRequiredMixin, CreateView):
    template_name = 'transactions/transaction_form.html'
    model = Transaction
    title = ''
    success_url = reverse_lazy('transaction_report')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'account': self.request.user.account
        })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) 
        context.update({
            'title': self.title
        })

        return context


class DepositMoneyView(TransactionCreateMixin):
    form_class = DepositForm
    title = 'Deposit'

    def get_initial(self):
        initial = {'transaction_type': DEPOSIT}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.account
        account.balance += amount 
        account.save(update_fields=['balance'])

        messages.success(self.request, f'{"${:,.2f}".format(float(amount))} Was Successfully Deposited to Your Account!')

        send_transaction_email(self.request.user, amount, "Deposit Success!", "transactions/deposit_email.html")

        return super().form_valid(form)


class WithdrawMoneyView(TransactionCreateMixin):
    form_class = WithdrawForm
    title = 'Withdraw Money'

    def get_initial(self):
        initial = {'transaction_type': WITHDRAWAL}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        self.request.user.account.balance -= form.cleaned_data.get('amount')
        self.request.user.account.save(update_fields=['balance'])

        send_transaction_email(self.request.user, amount, "Withdraw Success!", "transactions/withdrawal_email.html")
        messages.success(self.request, f'Successfully withdrawn {"${:,.2f}".format(float(amount))} from your account!')
        return super().form_valid(form)

class LoanRequestView(TransactionCreateMixin):
    form_class = LoanRequestForm
    title = 'Request For Loan'

    def get_initial(self):
        initial = {'transaction_type': LOAN}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        messages.success(self.request, f'Loan request for {"${:,.2f}".format(float(amount))} is Panding!')
        send_transaction_email(self.request.user, amount, "Request For A Loan", "transactions/loan_request_email.html")
        return super().form_valid(form)
    
class TransactionReportView(LoginRequiredMixin, ListView):
    template_name = 'transactions/transaction_report.html'
    model = Transaction
    balance = 0
    
    def get_queryset(self):
        queryset = super().get_queryset().filter(
            account=self.request.user.account
        )
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')
        
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            queryset = queryset.filter(timestamp__date__gte=start_date, timestamp__date__lte=end_date)
            self.balance = Transaction.objects.filter(timestamp__date__gte=start_date, timestamp__date__lte=end_date).aggregate(Sum('amount'))['amount__sum']
        else:
            self.balance = self.request.user.account.balance
       
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'account': self.request.user.account
        })
        return context
    
        
class PayLoanView(LoginRequiredMixin, View):
    def get(self, request, loan_id):
        loan = get_object_or_404(Transaction, id=loan_id)
        
        if loan.loan_approve:
            user_account = loan.account
            if loan.amount < user_account.balance:
                user_account.balance -= loan.amount
                loan.balance_after_transaction = user_account.balance
                user_account.save()
                loan.loan_approved = True
                loan.transaction_type = LOAN_PAID
                loan.save()
                return redirect('loan_list')
            else:
                messages.error( self.request, f'You do not have sufficient balance to pay your loan!'
        )

        return redirect('deposit_money')


class LoanListView(LoginRequiredMixin,ListView):
    model = Transaction
    template_name = 'transactions/loan_request.html'
    context_object_name = 'loans'
    
    def get_queryset(self):
        user_account = self.request.user.account
        queryset = Transaction.objects.filter(account=user_account,transaction_type=3)
        
        return queryset



class SendMoneyView(TransactionCreateMixin):
    form_class = SendMoneyForm
    title = 'Send Money'

    def get_initial(self):
        initial = {'transaction_type': SEND_MONEY}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        to_account_no = form.cleaned_data.get('to_account')
        to_account = UserBankAccount.objects.get(account_no=to_account_no)

        self.request.user.account.balance -= amount
        to_account.balance += amount
        self.request.user.account.save(update_fields=['balance'])
        to_account.save(update_fields=['balance'])

        Transaction.objects.create(
            account=to_account,
            amount=amount,
            balance_after_transaction=to_account.balance,
            transaction_type=RECEIVED_MONEY, 
        )

        send_transaction_email(self.request.user, amount, "Send Money Successful!", "transactions/send_money_email.html", to_account)
        send_transaction_email(to_account.user, amount, "Received Money Successful!", "transactions/receieved_money_email.html", self.request.user)

        messages.success(self.request, f"Send Money to: ${amount} Successful!")
        return super().form_valid(form)