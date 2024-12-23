from django import forms
from transactions.models import Transaction
from core.models import Bank
from accounts.models import UserBankAccount

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            'amount',
            'transaction_type'
        ]

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account')
        super().__init__(*args, **kwargs)
        self.fields['transaction_type'].disabled = True 
        self.fields['transaction_type'].widget = forms.HiddenInput() 

    def save(self, commit=True):
        self.instance.account = self.account
        self.instance.balance_after_transaction = self.account.balance
        return super().save()


class DepositForm(TransactionForm):
    def clean_amount(self): 
        min_deposit_amount = 100
        amount = self.cleaned_data.get('amount') 
        if amount < min_deposit_amount:
            raise forms.ValidationError(f'You need to deposit at least ${min_deposit_amount}')
        return amount


class WithdrawForm(TransactionForm):
    def clean_amount(self):
        account = self.account
        min_withdraw_amount = 100
        max_withdraw_amount = 100000
        balance = account.balance
        bank = Bank.objects.get(id=1)
        amount = self.cleaned_data.get('amount')

        if bank.is_bankrupt:
            raise forms.ValidationError(
                f"This Bank is Bankrupt! So You Cannot Withdraw Any Money!"
            )
        
        if amount < min_withdraw_amount:
            raise forms.ValidationError(
                f'You can withdraw at least ${min_withdraw_amount}'
            )

        if amount > max_withdraw_amount:
            raise forms.ValidationError(
                f'You can withdraw at most ${max_withdraw_amount}'
            )

        if amount > balance: 
            raise forms.ValidationError(
                f'You have only ${balance} in your account.'
            )

        return amount



class LoanRequestForm(TransactionForm):
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        current_loan_count = Transaction.objects.filter( account=self.account, transaction_type=3,loan_approve=False).count()
        if current_loan_count >= 1:
            raise forms.ValidationError("You already have a pending request for a loan!")

        return amount


class SendMoneyForm(TransactionForm):
    class Meta:
        model = Transaction
        fields = [
            'to_account',
            'amount',
            'transaction_type'
        ]
    
    def clean_to_account(self):
        to_account_no = self.cleaned_data["to_account"]
        try:
            to_account = UserBankAccount.objects.get(account_no=to_account_no)
        except UserBankAccount.DoesNotExist:
            raise forms.ValidationError('The account number is invalid!')

        return to_account_no
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount') 
        account = self.account
        balance = account.balance

        if amount > balance:
            raise forms.ValidationError('You do not have sufficient money to send!')

        return amount