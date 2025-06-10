from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal

class UserCredit(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='credit_account')
    total_credits = models.IntegerField(default=0)
    free_credits_given = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.total_credits} credits"
    
    def add_credits(self, amount, source="manual"):
        """Add credits to user account"""
        self.total_credits += amount
        self.save()
        
        # Log the transaction
        CreditTransaction.objects.create(
            user=self.user,
            amount=amount,
            transaction_type='credit',
            source=source,
            balance_after=self.total_credits
        )
    
    def deduct_credits(self, amount, purpose="usage"):
        """Deduct credits from user account"""
        if self.total_credits >= amount:
            self.total_credits -= amount
            self.save()
            
            # Log the transaction
            CreditTransaction.objects.create(
                user=self.user,
                amount=-amount,
                transaction_type='debit',
                source=purpose,
                balance_after=self.total_credits
            )
            return True
        return False

class CreditTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('credit', 'Credit Added'),
        ('debit', 'Credit Deducted'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='credit_transactions')
    amount = models.IntegerField()  # Positive for credits, negative for debits
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    source = models.CharField(max_length=100)  # 'signup', 'purchase', 'usage', etc.
    balance_after = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.amount} credits ({self.source})"

class Payment(models.Model):
    PAYMENT_TYPES = [
        ('one_time', 'One-time Purchase'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    payment_type = models.CharField(max_length=15, choices=PAYMENT_TYPES, default='one_time')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    credits_purchased = models.IntegerField()
    stripe_payment_intent_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - ${self.amount} ({self.status})"