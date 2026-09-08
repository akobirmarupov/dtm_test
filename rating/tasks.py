import logging

from celery import shared_task

logger = logging.getLogger('rating.tasks')


@shared_task(ignore_result=True)
def rebuild_leaderboards_task():
    from rating.services import rebuild_all_leaderboards

    return rebuild_all_leaderboards()


@shared_task(ignore_result=True)
def close_leagues_task():
    """O'tgan haftaning ligalarini yakunlaydi: kim ko'tarildi, kim tushdi."""
    from rating.leagues import close_previous_week

    return close_previous_week()
