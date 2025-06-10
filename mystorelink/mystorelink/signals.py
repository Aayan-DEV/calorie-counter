import stripe
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.conf import settings
from .models import UserProfile
from credits.models import UserCredit
from trackgrams.models import UserProfile as TrackgramsProfile

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY

@receiver(post_save, sender=User)
def create_universal_user_profile(sender, instance, created, **kwargs):
    """Create universal UserProfile and app-specific profiles when a new user is created"""
    if created:
        try:
            # Create universal profile
            profile, profile_created = UserProfile.objects.get_or_create(
                user=instance
            )
            
            # Create Stripe customer
            if not profile.stripe_customer_id:
                try:
                    # Check if customer already exists by email
                    existing_customers = stripe.Customer.list(email=instance.email, limit=1)
                    
                    if existing_customers.data:
                        customer = existing_customers.data[0]
                        logger.info(f"Found existing Stripe customer for {instance.email}: {customer.id}")
                    else:
                        customer = stripe.Customer.create(
                            email=instance.email,
                            name=f"{instance.first_name} {instance.last_name}".strip() or instance.username,
                            metadata={'user_id': str(instance.id)}
                        )
                        logger.info(f"Created new Stripe customer for {instance.email}: {customer.id}")
                    
                    profile.stripe_customer_id = customer.id
                    profile.save()
                    
                except stripe.error.StripeError as e:
                    logger.error(f"Failed to create Stripe customer for user {instance.id}: {str(e)}")
            
            # Create app-specific profiles
            # Credits profile
            UserCredit.objects.get_or_create(
                user=instance,
                defaults={'total_credits': 20, 'free_credits_given': True}
            )
            
            # Trackgrams profile
            TrackgramsProfile.objects.get_or_create(
                user=instance,
                defaults={'daily_calorie_goal': 2000}
            )
            
        except Exception as e:
            logger.error(f"Error in universal user creation signal for user {instance.id}: {str(e)}")