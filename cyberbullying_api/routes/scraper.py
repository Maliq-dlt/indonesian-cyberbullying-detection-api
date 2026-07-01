"""Scraper endpoints — TikTok & X/Twitter social media scraping."""

from fastapi import APIRouter, HTTPException, Depends, Security
import asyncio
import logging

from models import ScrapeTikTokRequest, ScrapeXRequest, ScrapeResponse
from routes.deps import rate_limit_cloud_llm_and_batch, get_current_user

logger = logging.getLogger("bullyguard")


def run_async_in_new_loop(coro_func, *args):
    """Helper to run an async function in a new thread."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro_func(*args))
    finally:
        loop.close()


router = APIRouter(prefix="/api", tags=["admin"], dependencies=[Security(get_current_user, scopes=["admin"])])


@router.post("/scrape/tiktok", response_model=ScrapeResponse, dependencies=[Depends(rate_limit_cloud_llm_and_batch)])
async def api_scrape_tiktok(req: ScrapeTikTokRequest):
    max_comments = req.max_comments if req.max_comments is not None else 20

    celery_active = False
    try:
        from tasks import celery_app
        inspect = celery_app.control.inspect(timeout=0.5)
        if inspect and inspect.active():
            celery_active = True
    except Exception as e:
        logger.warning("Failed to check Celery worker status (scrape_tiktok)", extra={"error": str(e)})

    if celery_active:
        try:
            from tasks import scrape_tiktok_task
            task = scrape_tiktok_task.delay(req.url, max_comments)
            res = task.get(timeout=60.0)
            if not res["success"]:
                raise HTTPException(status_code=502, detail="Gagal mengikis data dari TikTok via Celery worker.")
            return ScrapeResponse(success=True, count=len(res["comments"]), data=res["comments"])
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error scraping TikTok via Celery", extra={"error": str(e)})
            raise HTTPException(status_code=500, detail="Gagal mengikis data TikTok via antrean Celery.")

    try:
        from scraper.tiktok import scrape_tiktok_comments
        comments, success = await asyncio.to_thread(run_async_in_new_loop, scrape_tiktok_comments, req.url, max_comments)
        if not success:
            raise HTTPException(status_code=502, detail="Gagal mengikis data dari TikTok secara lokal.")
        return ScrapeResponse(success=success, count=len(comments), data=comments)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error scraping TikTok locally", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Gagal mengikis data komentar TikTok secara lokal.")


@router.post("/scrape/x", response_model=ScrapeResponse, dependencies=[Depends(rate_limit_cloud_llm_and_batch)])
async def api_scrape_x(req: ScrapeXRequest):
    max_tweets = req.max_tweets if req.max_tweets is not None else 20

    celery_active = False
    try:
        from tasks import celery_app
        inspect = celery_app.control.inspect(timeout=0.5)
        if inspect and inspect.active():
            celery_active = True
    except Exception as e:
        logger.warning("Failed to check Celery worker status (scrape_x)", extra={"error": str(e)})

    if celery_active:
        try:
            from tasks import scrape_x_task
            task = scrape_x_task.delay(req.url, max_tweets)
            res = task.get(timeout=60.0)
            if not res["success"]:
                raise HTTPException(status_code=502, detail="Gagal mengikis data dari X via Celery worker.")
            return ScrapeResponse(success=True, count=len(res["tweets"]), data=res["tweets"])
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error scraping X via Celery", extra={"error": str(e)})
            raise HTTPException(status_code=500, detail="Gagal mengikis data X via antrean Celery.")

    try:
        from scraper.twitter import scrape_x_tweets
        tweets, success = await asyncio.to_thread(run_async_in_new_loop, scrape_x_tweets, req.url, max_tweets)
        if not success:
            raise HTTPException(status_code=502, detail="Gagal mengikis data dari X secara lokal.")
        return ScrapeResponse(success=success, count=len(tweets), data=tweets)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error scraping X locally", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Gagal mengikis data replies X/Twitter secara lokal.")
