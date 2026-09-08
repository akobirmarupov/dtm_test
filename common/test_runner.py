"""Testlar uchun kesh izolyatsiyasi.

Kesh ham, DRF throttling hisobi ham Redis'da turadi va ular test bazasi
bilan birga tozalanmaydi. Natijada testlar bir-birining va ishchi muhitning
ma'lumotiga urilib ketardi: qayta ishga tushirilgan test o'sha `user_id`
ostidagi eski throttle hisobini topib **429** olardi va tasodifiy yiqilardi.

Yechim ikki qismdan iborat:

1. `settings.CACHES['default']['KEY_PREFIX'] = 'test'` — test kalitlari
   ishchi kalitlardan ajratiladi;
2. shu prefiksdagi kalitlar har bir ishga tushishda tozalanadi.

`cache.clear()` ATAYIN ishlatilmaydi: django-redis uni `FLUSHDB` ga
o'giradi va butun Redis bazasini — ishchi keshni ham — o'chirib yuboradi.
`delete_pattern('*')` esa kalit prefiksini hisobga oladi.
"""

import logging

from django.core.cache import cache
from django.test.runner import DiscoverRunner

logger = logging.getLogger(__name__)


class IsolatedCacheTestRunner(DiscoverRunner):
    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        self._flush_test_cache()

    def teardown_test_environment(self, **kwargs):
        self._flush_test_cache()
        super().teardown_test_environment(**kwargs)

    @staticmethod
    def _flush_test_cache():
        try:
            cache.delete_pattern('*')
        except AttributeError:
            # `delete_pattern` — django-redis kengaytmasi. Boshqa backendda
            # (LocMemCache) kesh baribir jarayon bilan birga o'ladi.
            cache.clear()
        except Exception:
            logger.warning('Test keshini tozalab bo\'lmadi.', exc_info=True)
