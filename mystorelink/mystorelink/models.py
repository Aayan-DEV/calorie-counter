from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def get_or_create_stripe_customer(self):
        """Get or create Stripe customer for this user"""
        import stripe
        from django.conf import settings
        
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        if self.stripe_customer_id:
            try:
                return stripe.Customer.retrieve(self.stripe_customer_id)
            except stripe.error.StripeError:
                # Customer doesn't exist, create new one
                pass
        
        # Create new customer
        customer = stripe.Customer.create(
            email=self.user.email,
            name=f"{self.user.first_name} {self.user.last_name}".strip() or self.user.username,
            metadata={'user_id': str(self.user.id)}
        )
        
        self.stripe_customer_id = customer.id
        self.save()
        
        return customer