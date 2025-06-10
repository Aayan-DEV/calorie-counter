from django.shortcuts import render
from django.http import HttpResponse
from credits.models import UserCredit, CreditTransaction
from django.db import models

def home_view(request):
    context = {}
    
    # Only get user credit if user is authenticated
    if request.user.is_authenticated:
        user_credit, created = UserCredit.objects.get_or_create(user=request.user)
        
        # Calculate paid credits from purchase transactions
        paid_credits_added = CreditTransaction.objects.filter(
            user=request.user,
            transaction_type='credit',
            source='purchase'
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        total_credits = user_credit.total_credits
        free_credits_given = user_credit.free_credits_given
        
        if paid_credits_added > 0:
            # User has bought credits, show remaining paid credits if any
            remaining_paid_credits = max(0, total_credits - (20 if free_credits_given else 0))
            credits_type = 'paid' if remaining_paid_credits > 0 else 'free'
            display_credits = remaining_paid_credits if remaining_paid_credits > 0 else total_credits
        else:
            # User only has free credits
            credits_type = 'free'
            display_credits = total_credits
            
        context['user_credits'] = display_credits
        context['credits_type'] = credits_type
    
    return render(request, 'home.html', context)


def robots_txt(request):
    lines = [
        "User-Agent: *",
        "Allow: /",
        "Sitemap: https://mystorel.ink/sitemap.xml",  # Replace with your domain
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")