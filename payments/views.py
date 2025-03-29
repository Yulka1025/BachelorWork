import base64
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse


@csrf_exempt  # Щоб не перевіряв CSRF-токен, бо LiqPay не надсилає його
def liqpay_callback(request):
    if request.method == "POST":
        data = request.POST.get("data")
        signature = request.POST.get("signature")

        if not data:
            return HttpResponse("Missing data", status=400)

        # Розкодовуємо та виводимо
        try:
            decoded = base64.b64decode(data).decode("utf-8")
            payment_data = json.loads(decoded)
        except Exception as e:
            return HttpResponse(f"Error decoding: {e}", status=400)

        print("📩 Отримано callback від LiqPay:")
        print(json.dumps(payment_data, indent=4, ensure_ascii=False))

        # Тут можна зберегти в БД статус оплати, order_id, тощо

        return HttpResponse("OK")

    return HttpResponse("Only POST allowed", status=405)