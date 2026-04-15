from panel_admin.models import Notification


class NotificationService:
    @staticmethod
    def create_notification(user, title, message, notification_type='system', link=None):
        """Create notification for user"""
        return Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            link=link
        )
    
    @staticmethod
    def mark_as_read(notification):
        """Mark notification as read"""
        notification.is_read = True
        notification.save()
        return notification
    
    @staticmethod
    def mark_all_as_read(user):
        """Mark all user notifications as read"""
        Notification.objects.filter(user=user, is_read=False).update(is_read=True)
        return True
    
    @staticmethod
    def get_unread_count(user):
        """Get unread notification count"""
        return Notification.objects.filter(user=user, is_read=False).count()
    
    @staticmethod
    def get_recent_notifications(user, limit=10):
        """Get recent notifications for user"""
        return Notification.objects.filter(user=user).order_by('-created_at')[:limit]
    
    @staticmethod
    def delete_old_notifications(days=30):
        """Delete notifications older than specified days"""
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days)
        Notification.objects.filter(created_at__lt=cutoff_date).delete()
        return True
