from django.urls import path
from transactions.views import DepositMoneyView, WithdrawMoneyView, TransactionReportView,LoanRequestView,LoanListView,PayLoanView, SendMoneyView
from core.views import MenuView

urlpatterns = [
    path("deposit/", DepositMoneyView.as_view(), name="deposit_money"),
    path("withdraw/", WithdrawMoneyView.as_view(), name="withdraw_money"),
    path("send-money/", SendMoneyView.as_view(), name="send_money"),
    path("report/", TransactionReportView.as_view(), name="transaction_report"),
    path("loan-request/", LoanRequestView.as_view(), name="loan_request"),
    path("loans/", LoanListView.as_view(), name="loan_list"),
    path("loans/<int:loan_id>/", PayLoanView.as_view(), name="pay"),
    path("menu/", MenuView.as_view(), name="menu"),
]