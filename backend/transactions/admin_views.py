from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib import messages
from django.utils.html import format_html
from django.db.models import Count, Avg
from django.contrib.admin.views.decorators import staff_member_required

from .models import Review


@staff_member_required
def review_moderation_dashboard(request):
    """
    Панель модерации отзывов для администраторов
    """
    pending_reviews = Review.objects.filter(is_published=False).order_by('-created_at')
    recent_reviews = Review.objects.filter(is_published=True).order_by('-created_at')[:10]
    
    # Статистика
    total_reviews = Review.objects.count()
    pending_count = pending_reviews.count()
    published_count = Review.objects.filter(is_published=True).count()
    featured_count = Review.objects.filter(is_featured=True).count()
    avg_rating = Review.objects.filter(is_published=True).aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Распределение рейтингов
    rating_distribution = []
    for i in range(1, 6):
        count = Review.objects.filter(rating=i).count()
        percentage = (count / total_reviews * 100) if total_reviews > 0 else 0
        rating_distribution.append({
            'rating': i,
            'count': count,
            'percentage': round(percentage, 1),
            'stars': '★' * i + '☆' * (5 - i)
        })
    
    context = {
        'title': 'Модерация отзывов',
        'pending_reviews': pending_reviews,
        'recent_reviews': recent_reviews,
        'total_reviews': total_reviews,
        'pending_count': pending_count,
        'published_count': published_count,
        'featured_count': featured_count,
        'avg_rating': round(avg_rating, 1),
        'rating_distribution': rating_distribution,
    }
    
    return render(request, 'admin/review_moderation_dashboard.html', context)


@staff_member_required
def approve_review(request, review_id):
    """
    Быстрое одобрение отзыва
    """
    try:
        review = Review.objects.get(pk=review_id)
        review.is_published = True
        review.save()
        messages.success(request, f'Отзыв от {review.name} успешно опубликован')
    except Review.DoesNotExist:
        messages.error(request, 'Отзыв не найден')
    
    return redirect('admin:review_moderation_dashboard')


@staff_member_required
def reject_review(request, review_id):
    """
    Быстрое отклонение отзыва
    """
    try:
        review = Review.objects.get(pk=review_id)
        review.delete()
        messages.success(request, f'Отзыв от {review.name} удален')
    except Review.DoesNotExist:
        messages.error(request, 'Отзыв не найден')
    
    return redirect('admin:review_moderation_dashboard')


@staff_member_required
def mark_as_featured(request, review_id):
    """
    Отметить отзыв как избранный
    """
    try:
        review = Review.objects.get(pk=review_id)
        review.is_featured = True
        review.is_published = True
        review.is_verified = True
        review.save()
        messages.success(request, f'Отзыв от {review.name} добавлен в избранное')
    except Review.DoesNotExist:
        messages.error(request, 'Отзыв не найден')
    
    return redirect('admin:review_moderation_dashboard') 