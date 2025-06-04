import httpx
import asyncio
import json
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from .models import Photo
from django.contrib.auth.decorators import login_required

@login_required
def camera_capture(request):
    """Camera capture page - main feature"""
    # Get user's recent photos
    recent_photos = Photo.objects.filter(user=request.user)[:10]
    
    context = {
        'recent_photos': recent_photos,
    }
    return render(request, 'trackgrams/track.html', context)

@csrf_exempt
@login_required
def save_photo(request):
    """API endpoint to save captured photos to Supabase"""
    if request.method == 'POST':
        try:
            # Handle both file upload and base64 data
            if request.FILES.get('photo'):
                # File upload
                photo_file = request.FILES['photo']
                
            elif request.POST.get('photo_data'):
                # Base64 data from camera
                photo_data = request.POST.get('photo_data')
                
                # Remove data URL prefix if present
                if photo_data.startswith('data:image'):
                    photo_data = photo_data.split(',')[1]
                
                # Decode base64
                image_data = base64.b64decode(photo_data)
                photo_file = ContentFile(image_data, name=f'camera_photo_{uuid.uuid4()}.jpg')
            
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'No photo data provided'
                }, status=400)
            
            # Create photo instance - this will automatically upload to Supabase
            photo = Photo.objects.create(
                user=request.user,
                image=photo_file
            )
            
            # Store the Supabase path
            photo.supabase_path = photo.image.name
            photo.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Photo saved to Supabase successfully!',
                'photo_id': photo.id,
                'photo_url': photo.image.url,
                'supabase_path': photo.supabase_path
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error saving photo to Supabase: {str(e)}'
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=405)


async def call_nutrition_api(image_file, grams):
    """Call your nutrition API with image file and grams"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            files = {'image': image_file}
            data = {
                'grams': grams
            }
            headers = {
                'Authorization': f'Bearer {settings.NUTRITION_API_KEY}'
            }
            
            response = await client.post(
                f"{settings.NUTRITION_API_URL}/analyze-nutrition",
                files=files,
                data=data,
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'status': 'error',
                    'message': f'API returned status {response.status_code}'
                }
                
    except Exception as e:
        return {
            'status': 'error',
            'message': f'API call failed: {str(e)}'
        }

@csrf_exempt
def save_photo(request):
    if request.method == 'POST':
        try:
            # Handle file upload
            if 'photo' in request.FILES:
                photo_file = request.FILES['photo']
            elif 'image' in request.POST:
                # Handle base64 data
                import base64
                from io import BytesIO
                from django.core.files.base import ContentFile
                
                image_data = request.POST['image']
                format, imgstr = image_data.split(';base64,')
                ext = format.split('/')[-1]
                photo_file = ContentFile(
                    base64.b64decode(imgstr),
                    name=f'photo.{ext}'
                )
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'No image provided'
                })
            
            # Save photo to database
            photo = Photo.objects.create(
                user=request.user if request.user.is_authenticated else None,
                image=photo_file
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Photo saved successfully',
                'photo_id': photo.id,
                'photo_url': photo.image.url
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

@csrf_exempt
def analyze_nutrition(request):
    """New endpoint to analyze nutrition using your API"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            photo_id = data.get('photo_id')
            grams = data.get('grams', 100)
            
            if not photo_id:
                return JsonResponse({
                    'success': False,
                    'message': 'Photo ID is required'
                })
            
            # Get photo from database
            try:
                photo = Photo.objects.get(id=photo_id)
            except Photo.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Photo not found'
                })
            
            # Download image from Supabase
            import requests
            image_response = requests.get(photo.image.url)
            if image_response.status_code != 200:
                return JsonResponse({
                    'success': False,
                    'message': 'Failed to download image'
                })
            
            # Prepare image file for API
            from io import BytesIO
            image_file = BytesIO(image_response.content)
            image_file.name = f'photo_{photo_id}.jpg'
            
            # Call your nutrition API
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    call_nutrition_api(image_file, grams)
                )
                return JsonResponse(result)
            finally:
                loop.close()
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

def camera_capture(request):
    """Render the camera capture page"""
    recent_photos = Photo.objects.all().order_by('-created_at')[:10]
    return render(request, 'trackgrams/track.html', {
        'recent_photos': recent_photos
    })