from django.shortcuts import render

def home(request):
    """Main site homepage with links to all SaaS apps"""
    apps = [
        {
            'name': 'Track Grams',
            'description': 'Calorie tracking and nutrition management',
            'url': '/trackgrams/',
            'icon': '🍎',
            'color': 'bg-green-500'
        },
        # Add more SaaS apps here in the future
    ]
    return render(request, 'home.html', {'apps': apps})