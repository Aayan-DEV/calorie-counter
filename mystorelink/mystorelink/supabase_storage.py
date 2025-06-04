import os
import uuid
from io import BytesIO
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from django.conf import settings
from .supabase_client import get_supabase_admin_client
from supabase import Client

class SupabaseStorage(Storage):
    """
    Custom Django storage backend for Supabase Storage
    """
    
    def __init__(self, bucket_name=None):
        self.bucket_name = bucket_name or getattr(settings, 'SUPABASE_STORAGE_BUCKET', 'photos')
        self.supabase: Client = get_supabase_admin_client()
        
    def _save(self, name, content):
        """
        Save file to Supabase Storage
        """
        # Generate unique filename
        file_extension = os.path.splitext(name)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        try:
            # Read file content
            if hasattr(content, 'read'):
                file_content = content.read()
            else:
                file_content = content
                
            # Upload to Supabase Storage
            response = self.supabase.storage.from_(self.bucket_name).upload(
                path=unique_filename,
                file=file_content,
                file_options={"content-type": "image/jpeg"}
            )
            
            if response:
                return unique_filename
            else:
                raise Exception("Failed to upload to Supabase")
                
        except Exception as e:
            raise Exception(f"Error uploading to Supabase: {str(e)}")
    
    def delete(self, name):
        """
        Delete file from Supabase Storage
        """
        try:
            self.supabase.storage.from_(self.bucket_name).remove([name])
        except Exception as e:
            print(f"Error deleting file from Supabase: {str(e)}")
    
    def exists(self, name):
        """
        Check if file exists in Supabase Storage
        """
        try:
            response = self.supabase.storage.from_(self.bucket_name).list()
            return any(file['name'] == name for file in response)
        except:
            return False
    
    def url(self, name):
        """
        Get public URL for the file
        """
        try:
            response = self.supabase.storage.from_(self.bucket_name).get_public_url(name)
            return response
        except Exception as e:
            print(f"Error getting public URL: {str(e)}")
            return None
    
    def size(self, name):
        """
        Get file size
        """
        return 0
    
    def deconstruct(self):
        """
        Required for Django migrations serialization
        """
        return (
            'mystorelink.supabase_storage.SupabaseStorage',
            [],
            {'bucket_name': self.bucket_name}
        )