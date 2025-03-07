import os
import json
import qrcode
from io import BytesIO
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
import pdfkit
from .models import Item

def generate_receipt(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_ids = data.get('items', [])

            items = Item.objects.filter(id__in=item_ids)
            if not items:
                return JsonResponse({'error': 'No items found'}, status=400)

            total_amount = sum(item.price for item in items)

            context = {
                'items': items,
                'total_amount': total_amount,
                'created_at': timezone.now().strftime('%d.%m.%Y %H:%M')
            }

            html = render_to_string('receipt_template.html', context)
            pdf = pdfkit.from_string(html, False)

            # Сохранение PDF в папку media
            file_name = f'receipt_{timezone.now().strftime("%Y%m%d%H%M%S")}.pdf'
            file_path = os.path.join(settings.MEDIA_ROOT, file_name)
            with open(file_path, 'wb') as f:
                f.write(pdf)

            # Генерация QR-кода
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(f'{settings.MEDIA_URL}{file_name}')
            qr.make(fit=True)

            img = qr.make_image(fill='black', back_color='white')
            img_io = BytesIO()
            img.save(img_io, format='PNG')
            img_file = ContentFile(img_io.getvalue(), name='qr_code.png')

            qr_file_name = f'qr_code_{timezone.now().strftime("%Y%m%d%H%M%S")}.png'
            qr_file_path = os.path.join(settings.MEDIA_ROOT, qr_file_name)
            with open(qr_file_path, 'wb') as f:
                f.write(img_file.read())

            # Возвращаем URL на QR-код в ответе
            qr_url = request.build_absolute_uri(f'{settings.MEDIA_URL}{qr_file_name}')
            return JsonResponse({'qr_code_url': qr_url})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)
