import json
import logging
import stripe
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db import models
from .models import UserCredit, Payment, CreditTransaction
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils import timezone
from decimal import Decimal

logger = logging.getLogger(__name__)

# Configure Stripe
if hasattr(settings, 'STRIPE_SECRET_KEY') and settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY
    STRIPE_CONFIGURED = True
else:
    STRIPE_CONFIGURED = False
    logger.warning("Stripe not configured - missing STRIPE_SECRET_KEY")

@login_required
def pricing_view(request):
    """Display pricing page for one-time credit purchases"""
    
    # Get user credit info
    user_credit, created = UserCredit.objects.get_or_create(user=request.user)
    
    # Calculate paid credits from purchase transactions
    from .models import CreditTransaction
    paid_credits_added = CreditTransaction.objects.filter(
        user=request.user,
        transaction_type='credit',
        source='purchase'
    ).aggregate(total=models.Sum('amount'))['total'] or 0
    
    # Calculate used credits (all debit transactions)
    used_credits = CreditTransaction.objects.filter(
        user=request.user,
        transaction_type='debit'
    ).aggregate(total=models.Sum('amount'))['total'] or 0
    used_credits = abs(used_credits)  # Make positive
    
    # Calculate remaining paid credits
    # If user has more than 20 credits total, assume the excess are paid credits
    # If user has 20 or fewer, they might be free credits
    total_credits = user_credit.total_credits
    free_credits_given = user_credit.free_credits_given
    
    if paid_credits_added > 0:
        # User has bought credits, calculate remaining paid credits
        remaining_paid_credits = max(0, total_credits - (20 if free_credits_given else 0))
        credits_type = 'paid' if remaining_paid_credits > 0 else 'free'
        display_credits = remaining_paid_credits if remaining_paid_credits > 0 else total_credits
    else:
        # User only has free credits
        credits_type = 'free'
        display_credits = total_credits
    
    context = {
        'stripe_configured': STRIPE_CONFIGURED,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY if STRIPE_CONFIGURED else '',
        'user_credits': display_credits,
        'credits_type': credits_type,
        'total_credits': total_credits,
    }
    return render(request, 'credits/pricing.html', context)

@login_required
@require_POST
def create_payment_intent(request):
    """Create a Stripe payment intent for one-time credit purchase"""
    if not STRIPE_CONFIGURED:
        logger.error("Payment attempt with unconfigured Stripe")
        return JsonResponse({'error': 'Payment system not configured'}, status=500)
    
    try:
        data = json.loads(request.body)
        credits = int(data.get('credits', 0))
        
        if credits < 10:
            return JsonResponse({
                'error': 'Minimum purchase amount is $0.50 (10 credits)'
            }, status=400)
        
        # Calculate amount (5 cents per credit)
        amount = credits * 5  # Amount in cents
        
        logger.info(f"Creating payment intent for user {request.user.id}: {credits} credits, ${amount/100}")
        
        # Create payment intent
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='usd',
            metadata={
                'user_id': request.user.id,
                'credits': credits,
                'type': 'onetime'
            }
        )
        
        # Create payment record
        payment = Payment.objects.create(
            user=request.user,
            payment_type='one_time',
            amount=Decimal(amount) / 100,
            credits_purchased=credits,
            stripe_payment_intent_id=intent.id,
            status='pending'
        )
        
        logger.info(f"Created payment intent {intent.id} for user {request.user.id}")
        
        return JsonResponse({
            'client_secret': intent.client_secret,
            'payment_type': 'payment_intent',
            'amount': amount
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except ValueError as e:
        return JsonResponse({'error': f'Invalid data: {str(e)}'}, status=400)
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        return JsonResponse({'error': f'Payment processing error: {str(e)}'}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error in create_payment_intent: {str(e)}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

@login_required
def payment_success(request):
    """Handle successful payment redirect"""
    credits = request.GET.get('credits', 0)
    amount = request.GET.get('amount', 0)
    payment_type = request.GET.get('type', 'onetime')
    
    context = {
        'credits': credits,
        'amount': amount,
        'payment_type': payment_type
    }

    return render(request, 'credits/payment_success.html', context)
@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhooks"""
    if not STRIPE_CONFIGURED:
        return HttpResponse(status=400)
    
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)
    
    try:
        if endpoint_secret:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        else:
            event = json.loads(payload)
            
        logger.info(f"Received webhook: {event['type']}")
        
        # Handle payment intent succeeded
        if event['type'] == 'payment_intent.succeeded':
            handle_successful_payment(event['data']['object'])
        elif event['type'] == 'payment_intent.payment_failed':
            handle_failed_payment(event['data']['object'])
            
        return HttpResponse(status=200)
        
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        return HttpResponse(status=400)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return HttpResponse(status=500)

def handle_successful_payment(payment_intent):
    """Handle successful one-time payment"""
    try:
        payment_intent_id = payment_intent.get('id')
        metadata = payment_intent.get('metadata', {})
        user_id = metadata.get('user_id')
        credits = int(metadata.get('credits', 0))
        
        logger.info(f"Processing successful payment for user {user_id}: {credits} credits")
        
        # Update payment record
        try:
            payment = Payment.objects.get(stripe_payment_intent_id=payment_intent_id)
            payment.status = 'completed'
            payment.save()
        except Payment.DoesNotExist:
            logger.error(f"Payment record not found for intent {payment_intent_id}")
            return
        
        # Add credits to user account
        from django.contrib.auth.models import User
        user = User.objects.get(id=user_id)
        user_credit, created = UserCredit.objects.get_or_create(user=user)
        user_credit.add_credits(credits, source="purchase")
        
        logger.info(f"Added {credits} credits to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error handling successful payment: {str(e)}")

def handle_failed_payment(payment_intent):
    """Handle failed payment"""
    try:
        payment_intent_id = payment_intent.get('id')
        
        # Update payment record
        try:
            payment = Payment.objects.get(stripe_payment_intent_id=payment_intent_id)
            payment.status = 'failed'
            payment.save()
            logger.info(f"Updated payment {payment_intent_id} status to failed")
        except Payment.DoesNotExist:
            logger.error(f"Payment record not found for intent {payment_intent_id}")
            
    except Exception as e:
        logger.error(f"Error handling failed payment: {str(e)}")