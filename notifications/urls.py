# notifications/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # عرض الإشعارات
    path('api/notifications/<int:user_id>/', views.get_user_notifications, name='get-user-notifications'),
    path('api/notifications/<int:user_id>/unread/', views.get_unread_notifications, name='get-unread-notifications'),
    
    # تحديث الحالة
    path('api/notifications/<int:notification_id>/read/', views.mark_notification_as_read, name='mark-notification-read'),
    path('api/notifications/<int:notification_id>/delivered/', views.mark_notification_as_delivered, name='mark-notification-delivered'),
    path('api/notifications/mark-all-read/', views.mark_all_notifications_read, name='mark-all-read'),
    
    # تفاعل المستخدم
    path('api/notifications/<int:notification_id>/action/', views.update_notification_action, name='notification-action'),
    
    # إلغاء وإعادة محاولة
    path('api/notifications/<int:notification_id>/cancel/', views.cancel_notification, name='cancel-notification'),
    path('api/notifications/<int:notification_id>/retry/', views.retry_failed_notification, name='retry-notification'),
    
    # حذف
    path('api/notifications/<int:notification_id>/delete/', views.delete_notification, name='delete-notification'),
    path('api/notifications/<int:user_id>/delete-read/', views.delete_all_read_notifications, name='delete-read-notifications'),
]