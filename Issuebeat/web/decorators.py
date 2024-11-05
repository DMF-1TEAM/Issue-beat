from functools import wraps
from django.http import JsonResponse
import time

def with_loading_state(view_func):
    @wraps(view_func)
    async def wrapper(request, *args, **kwargs):
        try:
            start_time = time.time()
            response = await view_func(request, *args, **kwargs)
            execution_time = time.time() - start_time

            if isinstance(response, JsonResponse):
                data = response.content
                if hasattr(data, 'decode'):
                    data = data.decode('utf-8')

                return JsonResponse({
                    'data': data,
                    'meta': {
                        'loading': False,
                        'execution_time': execution_time
                    }
                }, status=response.status_code)

            return response
        except Exception as e:
            raise e

    return wrapper