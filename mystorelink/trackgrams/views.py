import httpx
import asyncio
import json
import base64
import uuid
from io import BytesIO
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.core.files.base import ContentFile
from .models import Photo, FoodEntry
from django.contrib.auth.decorators import login_required
import cv2
import numpy as np
from PIL import Image
from pyzbar.pyzbar import decode
from io import BytesIO

def enhanced_barcode_detection(image_file):
    """Enhanced barcode detection with multiple preprocessing approaches"""
    # Reset file pointer
    image_file.seek(0)
    
    # Load image with PIL
    pil_image = Image.open(image_file)
    
    # Convert to OpenCV format
    cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    
    # Try multiple approaches
    approaches = [
        # Approach 1: Original image
        lambda img: img,
        
        # Approach 2: Resize to smaller resolution
        lambda img: cv2.resize(img, (1024, 768)),
        
        # Approach 3: Grayscale conversion
        lambda img: cv2.cvtColor(img, cv2.COLOR_BGR2GRAY),
        
        # Approach 4: Gaussian blur + threshold
        lambda img: cv2.threshold(
            cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (5, 5), 0),
            0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )[1],
        
        # Approach 5: Adaptive threshold
        lambda img: cv2.adaptiveThreshold(
            cv2.cvtColor(img, cv2.COLOR_BGR2GRAY),
            255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        ),
        
        # Approach 6: Edge enhancement
        lambda img: cv2.Canny(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 50, 150),
        
        # Approach 7: Morphological operations
        lambda img: cv2.morphologyEx(
            cv2.cvtColor(img, cv2.COLOR_BGR2GRAY),
            cv2.MORPH_CLOSE,
            cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        )
    ]
    
    # Try different rotations for each approach
    rotations = [0, 90, 180, 270]
    
    for i, approach in enumerate(approaches):
        try:
            processed_img = approach(cv_image.copy())
            
            # Try different rotations
            for rotation in rotations:
                if rotation != 0:
                    if len(processed_img.shape) == 3:
                        h, w = processed_img.shape[:2]
                    else:
                        h, w = processed_img.shape
                    
                    center = (w // 2, h // 2)
                    matrix = cv2.getRotationMatrix2D(center, rotation, 1.0)
                    rotated_img = cv2.warpAffine(processed_img, matrix, (w, h))
                else:
                    rotated_img = processed_img
                
                # Try pyzbar detection
                barcodes = decode(rotated_img)
                
                if barcodes:
                    print(f"✅ Barcode detected with approach {i+1}, rotation {rotation}°")
                    return barcodes[0].data.decode('utf-8')
                    
        except Exception as e:
            print(f"❌ Approach {i+1} failed: {str(e)}")
            continue
    
    return None

@login_required
def camera_capture(request):
    """Camera capture page - main feature"""
    # Get user's recent photos
    recent_photos = Photo.objects.filter(user=request.user)[:10]
    
    # Get or create user credits
    from credits.models import UserCredit
    user_credit, created = UserCredit.objects.get_or_create(
        user=request.user,
        defaults={'total_credits': 0}
    )
    
    context = {
        'recent_photos': recent_photos,
        'user_credits': user_credit.total_credits,
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
                    'status': 'error',
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
                'status': 'success',
                'message': 'Photo saved to Supabase successfully!',
                'photo_id': photo.id,
                'photo_url': photo.image.url,
                'supabase_path': photo.supabase_path
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error saving photo to Supabase: {str(e)}'
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
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
@login_required
def analyze_nutrition(request):
    """New endpoint to analyze nutrition using your API"""
    if request.method == 'POST':
        try:
            # Check user credits
            from credits.models import UserCredit
            user_credit, created = UserCredit.objects.get_or_create(
                user=request.user,
                defaults={'total_credits': 0}
            )
            
            if user_credit.total_credits <= 0:
                return JsonResponse({
                    'status': 'error',
                    'message': 'insufficient_credits',
                    'credits_remaining': 0
                })
            
            data = json.loads(request.body)
            photo_id = data.get('photo_id')
            grams = data.get('grams', 100)
            
            if not photo_id:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Photo ID is required'
                })
            
            # Get photo from database
            try:
                photo = Photo.objects.get(id=photo_id, user=request.user)
            except Photo.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Photo not found'
                })
            
            # Download image from Supabase
            import requests
            image_response = requests.get(photo.image.url)
            if image_response.status_code != 200:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Failed to download image'
                })
            
            # Prepare image file for API
            image_file = BytesIO(image_response.content)
            image_file.name = f'photo_{photo_id}.jpg'
            
            # Call your nutrition API
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    call_nutrition_api(image_file, grams)
                )
                
                print(f"Raw API Response: {result}")  # Debug logging
                
                # Parse the nested API response correctly
                if result.get('status') == 'success':
                    # Deduct 1 credit
                    user_credit.deduct_credits(1, "nutrition_analysis")
                    
                    # Extract nutrition data from the nested structure - USE nutrition_for_requested_grams (correct values)
                    nutrition_analysis = result.get('nutrition_analysis', {})
                    nutrition_data = nutrition_analysis.get('nutrition_for_requested_grams', {})
                    
                    # Handle both possible field names (with/without _grams suffix)
                    calories = nutrition_data.get('calories', 0)
                    protein = nutrition_data.get('protein_grams', nutrition_data.get('protein', 0))
                    carbs = nutrition_data.get('carbs_grams', nutrition_data.get('carbs', 0))
                    sugar = nutrition_data.get('sugar_grams', nutrition_data.get('sugar', 0))
                    
                    print(f"Extracted nutrition - Calories: {calories}, Protein: {protein}, Carbs: {carbs}, Sugar: {sugar}")
                    
                    # Format the response properly
                    response_data = {
                        'status': 'success',
                        'nutrition': {
                            'calories': float(calories) if calories else 0,
                            'protein': float(protein) if protein else 0,
                            'carbs': float(carbs) if carbs else 0,
                            'sugar': float(sugar) if sugar else 0
                        },
                        'credits_remaining': user_credit.total_credits,
                        'debug_info': {
                            'raw_api_response': result,
                            'extracted_nutrition': nutrition_data
                        }
                    }
                    return JsonResponse(response_data)
                else:
                    return JsonResponse({
                        'status': 'error',
                        'message': result.get('message', 'Analysis failed'),
                        'debug_info': result
                    })
                    
            finally:
                loop.close()
                
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            })
        except Exception as e:
            print(f"Error in analyze_nutrition: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    })

@csrf_exempt
def add_food_entry(request):
    """Add a food entry to the log"""
    if request.method == 'POST':
        try:
            # Check if user is authenticated
            if not request.user.is_authenticated:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Authentication required'
                }, status=401)
            
            data = json.loads(request.body)
            
            # Create food entry
            food_entry = FoodEntry.objects.create(
                user=request.user,
                food_name=data.get('food_name', 'Unknown Food'),
                grams=data.get('grams', 0),
                calories=data.get('calories', 0),
                protein=data.get('protein', 0),
                carbs=data.get('carbs', 0),
                sugar=data.get('sugar', 0)
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Food entry added successfully',
                'entry_id': food_entry.id
            })
            
        except Exception as e:
            print(f"Error adding food entry: {e}")  # Add logging
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=405)

@login_required
def get_food_entries(request):
    """Get today's food entries for the user with extensive error checking"""
    import logging
    from datetime import date, datetime, timedelta
    from django.utils import timezone as django_timezone
    
    # Set up logging
    logger = logging.getLogger(__name__)
    
    try:
        # STEP 1: Validate user authentication
        if not request.user or not request.user.is_authenticated:
            logger.error(f"User authentication failed: {request.user}")
            return JsonResponse({
                'status': 'error',
                'message': 'User not authenticated',
                'debug_info': 'Authentication check failed'
            }, status=401)
        
        user_id = request.user.id
        username = request.user.username
        logger.info(f"Processing food entries request for user: {username} (ID: {user_id})")
        
        # STEP 2: Check if FoodEntry model is accessible
        try:
            total_entries_in_db = FoodEntry.objects.count()
            logger.info(f"Total FoodEntry records in database: {total_entries_in_db}")
        except Exception as e:
            logger.error(f"Database connection or model access error: {e}")
            return JsonResponse({
                'status': 'error',
                'message': 'Database access error',
                'debug_info': str(e)
            }, status=500)
        
        # STEP 3: Check user's total entries (all time)
        try:
            user_total_entries = FoodEntry.objects.filter(user=request.user).count()
            logger.info(f"Total entries for user {username}: {user_total_entries}")
            
            if user_total_entries == 0:
                logger.warning(f"No entries found for user {username} in entire database")
                return JsonResponse({
                    'status': 'success',
                    'entries': [],
                    'debug_info': f'User has no entries in database. Total DB entries: {total_entries_in_db}'
                })
        except Exception as e:
            logger.error(f"Error querying user entries: {e}")
            return JsonResponse({
                'status': 'error',
                'message': 'Error querying user entries',
                'debug_info': str(e)
            }, status=500)
        
        # STEP 4: Get recent entries for debugging
        try:
            recent_entries = FoodEntry.objects.filter(user=request.user).order_by('-created_at')[:5]
            logger.info(f"Recent entries for user {username}:")
            for entry in recent_entries:
                logger.info(f"  - {entry.food_name} created at {entry.created_at} (timezone: {entry.created_at.tzinfo})")
        except Exception as e:
            logger.error(f"Error fetching recent entries: {e}")
        
        # STEP 5: Handle timezone and date filtering
        try:
            # Get current timezone info
            from django.conf import settings
            use_tz = getattr(settings, 'USE_TZ', False)
            current_tz = getattr(settings, 'TIME_ZONE', 'UTC')
            logger.info(f"Django timezone settings - USE_TZ: {use_tz}, TIME_ZONE: {current_tz}")
            
            # Get today's date
            if use_tz:
                # Use timezone-aware datetime
                now = django_timezone.now()
                today = now.date()
                start_of_day = django_timezone.make_aware(datetime.combine(today, datetime.min.time()))
                end_of_day = django_timezone.make_aware(datetime.combine(today, datetime.max.time()))
                logger.info(f"Using timezone-aware dates: {start_of_day} to {end_of_day}")
            else:
                # Use naive datetime
                today = date.today()
                start_of_day = datetime.combine(today, datetime.min.time())
                end_of_day = datetime.combine(today, datetime.max.time())
                logger.info(f"Using naive dates: {start_of_day} to {end_of_day}")
            
        except Exception as e:
            logger.error(f"Error setting up date filtering: {e}")
            return JsonResponse({
                'status': 'error',
                'message': 'Date filtering setup error',
                'debug_info': str(e)
            }, status=500)
        
        # STEP 6: Try different date filtering approaches
        try:
            # Method 1: Today's entries with strict date filtering
            todays_entries = FoodEntry.objects.filter(
                user=request.user,
                created_at__gte=start_of_day,
                created_at__lte=end_of_day
            ).order_by('-created_at')
            
            logger.info(f"Method 1 - Today's entries found: {todays_entries.count()}")
            
            # Method 2: Last 24 hours
            if use_tz:
                last_24h = django_timezone.now() - timedelta(hours=24)
            else:
                last_24h = datetime.now() - timedelta(hours=24)
            
            last_24h_entries = FoodEntry.objects.filter(
                user=request.user,
                created_at__gte=last_24h
            ).order_by('-created_at')
            
            logger.info(f"Method 2 - Last 24h entries found: {last_24h_entries.count()}")
            
            # Method 3: Today's entries using date only (ignoring time)
            today_date_only = FoodEntry.objects.filter(
                user=request.user,
                created_at__date=today
            ).order_by('-created_at')
            
            logger.info(f"Method 3 - Today's entries (date only): {today_date_only.count()}")
            
            # Choose the best method
            if todays_entries.exists():
                entries = todays_entries
                method_used = "strict_datetime"
            elif today_date_only.exists():
                entries = today_date_only
                method_used = "date_only"
            elif last_24h_entries.exists():
                entries = last_24h_entries
                method_used = "last_24h"
            else:
                entries = FoodEntry.objects.none()
                method_used = "none_found"
            
            logger.info(f"Using method: {method_used}, entries found: {entries.count()}")
            
        except Exception as e:
            logger.error(f"Error in date filtering: {e}")
            return JsonResponse({
                'status': 'error',
                'message': 'Date filtering error',
                'debug_info': str(e)
            }, status=500)
        
        # STEP 7: Build response data
        try:
            entries_data = []
            for entry in entries:
                try:
                    entry_data = {
                        'id': entry.id,
                        'food_name': entry.food_name,
                        'grams': entry.grams,
                        'calories': entry.calories,
                        'protein': entry.protein,
                        'carbs': entry.carbs,
                        'sugar': entry.sugar,
                        'created_at': entry.created_at.strftime('%H:%M'),
                        'created_at_full': entry.created_at.isoformat()
                    }
                    entries_data.append(entry_data)
                    logger.info(f"Added entry: {entry.food_name} - {entry.created_at}")
                except Exception as entry_error:
                    logger.error(f"Error processing entry {entry.id}: {entry_error}")
                    continue
            
            # STEP 8: Return comprehensive response
            response_data = {
                'status': 'success',
                'entries': entries_data,
                'debug_info': {
                    'user_id': user_id,
                    'username': username,
                    'total_user_entries': user_total_entries,
                    'total_db_entries': total_entries_in_db,
                    'method_used': method_used,
                    'timezone_settings': {
                        'USE_TZ': use_tz,
                        'TIME_ZONE': current_tz
                    },
                    'date_range': {
                        'start': start_of_day.isoformat() if hasattr(start_of_day, 'isoformat') else str(start_of_day),
                        'end': end_of_day.isoformat() if hasattr(end_of_day, 'isoformat') else str(end_of_day)
                    },
                    'entries_found': len(entries_data)
                }
            }
            
            logger.info(f"Returning {len(entries_data)} entries for user {username}")
            return JsonResponse(response_data)
            
        except Exception as e:
            logger.error(f"Error building response: {e}")
            return JsonResponse({
                'status': 'error',
                'message': 'Error building response',
                'debug_info': str(e)
            }, status=500)
    
    except Exception as e:
        logger.error(f"Unexpected error in get_food_entries: {e}")
        return JsonResponse({
            'status': 'error',
            'message': 'Unexpected server error',
            'debug_info': str(e)
        }, status=500)

@csrf_exempt
@login_required
def delete_food_entry(request):
    """Delete a food entry"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            entry_id = data.get('entry_id')
            
            if not entry_id:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Entry ID is required'
                })
            
            try:
                entry = FoodEntry.objects.get(id=entry_id, user=request.user)
                entry.delete()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Entry deleted successfully'
                })
                
            except FoodEntry.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Entry not found'
                })
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    })

async def call_barcode_api(image_file, grams):
    """Enhanced barcode API call with local preprocessing and manual barcode endpoint"""
    try:
        # First try local enhanced detection
        print("🔍 Trying enhanced local barcode detection...")
        local_barcode = enhanced_barcode_detection(image_file)
        
        if local_barcode:
            print(f"✅ Local detection successful: {local_barcode}")
            
            # Use the manual barcode endpoint with extracted barcode
            import httpx
            async with httpx.AsyncClient(timeout=60.0) as client:
                data = {
                    'barcode': local_barcode,
                    'grams': grams
                }
                headers = {
                    'Authorization': f'Bearer {settings.NUTRITION_API_KEY}'
                }
                
                response = await client.post(
                    f"{settings.NUTRITION_API_URL}/analyze-nutrition-barcode-manual",
                    data=data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Manual barcode API successful: {result.get('product_name', 'Unknown')}")
                    return result
                else:
                    print(f"❌ Manual barcode API failed: {response.status_code}")
                    return {
                        'status': 'error',
                        'message': f'Manual barcode API returned status {response.status_code}'
                    }
        else:
            print("❌ No barcode detected locally")
            return {
                'status': 'error',
                'message': 'No barcode detected in image'
            }
                
    except Exception as e:
        print(f"❌ Barcode API call failed: {str(e)}")
        return {
            'status': 'error',
            'message': f'API call failed: {str(e)}'
        }

@csrf_exempt
@login_required
def analyze_barcode(request):
    """New endpoint to analyze nutrition using barcode API"""
    if request.method == 'POST':
        try:
            # Check user credits
            from credits.models import UserCredit
            user_credit, created = UserCredit.objects.get_or_create(
                user=request.user,
                defaults={'total_credits': 0}
            )
            
            if user_credit.total_credits <= 0:
                return JsonResponse({
                    'status': 'error',
                    'message': 'insufficient_credits',
                    'credits_remaining': 0
                })
            
            data = json.loads(request.body)
            photo_id = data.get('photo_id')
            grams = data.get('grams', 100)
            
            if not photo_id:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Photo ID is required'
                })
            
            # Get photo from database
            try:
                photo = Photo.objects.get(id=photo_id, user=request.user)
            except Photo.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Photo not found'
                })
            
            # Download image from Supabase
            import requests
            image_response = requests.get(photo.image.url)
            if image_response.status_code != 200:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Failed to download image'
                })
            
            # Prepare image file for API
            image_file = BytesIO(image_response.content)
            image_file.name = f'barcode_{photo_id}.jpg'
            
            # Call barcode API
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # In the analyze_barcode function, update the API call (around line 745)
            try:
                result = loop.run_until_complete(
                    call_barcode_api(image_file, grams)  # Removed country parameter
                )
                
                print(f"Raw Barcode API Response: {result}")  # Debug logging
                
                if result.get('status') == 'success':
                    # Deduct 1 credit
                    user_credit.deduct_credits(1, "barcode_analysis")
                    
                    # Extract nutrition data from barcode API response
                    nutrition_analysis = result.get('nutrition_analysis', {})
                    nutrition_data = nutrition_analysis.get('nutrition_for_requested_grams', {})
                    
                    # Extract product information
                    product_info = {
                        'product_name': result.get('product_name', 'Unknown Product'),
                        'brands': result.get('brands', ''),
                        'barcode': result.get('barcode', ''),
                        'nutrition_grade': result.get('nutrition_grade', '')
                    }
                    
                    # Handle nutrition data
                    calories = nutrition_data.get('calories', 0)
                    protein = nutrition_data.get('protein_grams', 0)
                    carbs = nutrition_data.get('carbs_grams', 0)
                    sugar = nutrition_data.get('sugar_grams', 0)
                    
                    print(f"Barcode - Product: {product_info['product_name']}, Calories: {calories}, Protein: {protein}, Carbs: {carbs}, Sugar: {sugar}")
                    
                    # Format the response
                    response_data = {
                        'status': 'success',
                        'nutrition': {
                            'calories': float(calories) if calories else 0,
                            'protein': float(protein) if protein else 0,
                            'carbs': float(carbs) if carbs else 0,
                            'sugar': float(sugar) if sugar else 0
                        },
                        'product_info': product_info,
                        'credits_remaining': user_credit.total_credits,
                        'debug_info': {
                            'raw_api_response': result,
                            'extracted_nutrition': nutrition_data
                        }
                    }
                    return JsonResponse(response_data)
                else:
                    return JsonResponse({
                        'status': 'error',
                        'message': result.get('message', 'Barcode analysis failed'),
                        'debug_info': result
                    })
                    
            finally:
                loop.close()
                
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            })
        except Exception as e:
            print(f"Error in analyze_barcode: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    })