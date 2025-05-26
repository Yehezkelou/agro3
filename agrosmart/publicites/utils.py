import os
from django.utils.text import slugify
from django.utils import timezone
from PIL import Image
from io import BytesIO
from django.core.files import File

def generate_unique_slug(model, title):
    slug = slugify(title)
    unique_slug = slug
    num = 1
    while model.objects.filter(slug=unique_slug).exists():
        unique_slug = f"{slug}-{num}"
        num += 1
    return unique_slug

def compress_image(image, quality=70):
    img = Image.open(image)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    img_io = BytesIO()
    img.save(img_io, format='JPEG', quality=quality, optimize=True)
    new_image = File(img_io, name=image.name)
    return new_image

def handle_uploaded_image(image, ad_id):
    # Créer le répertoire s'il n'existe pas
    upload_dir = f"publicites/images/{ad_id}/"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Générer un nom de fichier unique
    filename = f"{timezone.now().timestamp()}-{image.name}"
    filepath = os.path.join(upload_dir, filename)
    
    # Compresser et sauvegarder l'image
    compressed_image = compress_image(image)
    with open(filepath, 'wb') as f:
        for chunk in compressed_image.chunks():
            f.write(chunk)
    
    return filepath