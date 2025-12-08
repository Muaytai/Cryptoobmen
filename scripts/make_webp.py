import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from PIL import Image
except:
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'Pillow', '-q'])
    from PIL import Image

base = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'public', 'images')

files = [
    'checkbox.png', 'chess_mirror.png', 'chess.png', 'chess1.png', 'chess2.png',
    'crypt-ico.png', 'doska.png', 'logo_light.png', 'logo.png', 'themes.png',
    'Инста.png', 'Телеграм.png',
    'profile/edit-2.png', 'profile/image-2-1.png', 'profile/image-2-2.png',
    'profile/image-2.png', 'profile/QR_code_light.png', 'profile/QR_code.png',
    'profile/rectangle-12960.png'
]

empty_photo = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'public', 'empty_photo.png')

count = 0
for f in files:
    png = os.path.join(base, f)
    if os.path.exists(png):
        try:
            img = Image.open(png)
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGBA')
            webp = png.replace('.png', '.webp').replace('.PNG', '.webp')
            img.save(webp, 'WEBP', quality=85)
            count += 1
            print(f"✓ {os.path.basename(f)}")
        except Exception as e:
            print(f"✗ {f}: {e}")

if os.path.exists(empty_photo):
    try:
        img = Image.open(empty_photo)
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGBA')
        webp = empty_photo.replace('.png', '.webp')
        img.save(webp, 'WEBP', quality=85)
        count += 1
        print(f"✓ empty_photo.png")
    except Exception as e:
        print(f"✗ empty_photo.png: {e}")

print(f"\n✅ Создано {count} WebP файлов")
