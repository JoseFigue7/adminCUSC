from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from audit.models import AuditLog, AuditAction
from audit.utils import is_audit_enabled, should_audit_model

User = get_user_model()


class AuditLogModelTestCase(TestCase):
    """Tests para el modelo AuditLog"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_audit_log_creation(self):
        """Test crear un registro de auditoría"""
        content_type = ContentType.objects.get_for_model(User)
        
        audit_log = AuditLog.objects.create(
            user=self.user,
            username=self.user.username,
            action=AuditAction.CREATE,
            content_type=content_type,
            object_id=str(self.user.pk),
            model_name='users.User',
            data_snapshot={'username': 'testuser'}
        )
        
        self.assertEqual(audit_log.user, self.user)
        self.assertEqual(audit_log.action, AuditAction.CREATE)
        self.assertEqual(audit_log.model_name, 'users.User')
        self.assertIsNotNone(audit_log.id)
        self.assertIsNotNone(audit_log.timestamp)
    
    def test_audit_log_str(self):
        """Test la representación string del AuditLog"""
        content_type = ContentType.objects.get_for_model(User)
        
        audit_log = AuditLog.objects.create(
            user=self.user,
            username=self.user.username,
            action=AuditAction.UPDATE,
            content_type=content_type,
            object_id=str(self.user.pk),
            model_name='users.User'
        )
        
        str_repr = str(audit_log)
        self.assertIn('testuser', str_repr)
        self.assertIn('UPDATE', str_repr)
        self.assertIn('users.User', str_repr)
    
    def test_audit_log_formatted_changes(self):
        """Test el método get_formatted_changes"""
        content_type = ContentType.objects.get_for_model(User)
        
        audit_log = AuditLog.objects.create(
            user=self.user,
            action=AuditAction.UPDATE,
            content_type=content_type,
            object_id=str(self.user.pk),
            model_name='users.User',
            changes={
                'username': {'old': 'olduser', 'new': 'newuser'},
                'email': {'old': 'old@example.com', 'new': 'new@example.com'}
            }
        )
        
        formatted = audit_log.get_formatted_changes()
        self.assertEqual(formatted['username']['anterior'], 'olduser')
        self.assertEqual(formatted['username']['nuevo'], 'newuser')
        self.assertEqual(formatted['email']['anterior'], 'old@example.com')
        self.assertEqual(formatted['email']['nuevo'], 'new@example.com')
