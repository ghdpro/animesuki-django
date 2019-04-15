from django.test import TestCase, RequestFactory
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType

from animesuki.core.models import Option
from animesuki.core.utils import user_add_permission
from animesuki.history.models import ChangeRequest
from ..models import Media


class HistoryModelTest(TestCase):
    """
    This class tests HistoryModel through the Media class. This couldn't be put in the History app because
    HistoryModel is an abstract model and writing simple tests for Abstract models is basically impossible.

    This TestCase attempts to only test base HistoryModel functionality as far as possible.
    """
    fixtures = ['option.json']

    def setUp(self):
        self.factory = RequestFactory()


    def test_historymodel_sanity_checks(self):
        # Set Up
        obj = Media(title='Test')
        request = self.factory.get('/')
        # AnonymousUser should raise ValidationError with code 'user-not-authenticated'
        request.user = AnonymousUser()
        obj.request = request
        with self.assertRaises(ValidationError) as cm:
            obj.sanity_checks
        self.assertEqual(cm.exception.code, 'user-not-authenticated')
        request.user = get_user_model().objects.create_user(username='test_user', email='test@example.com')  # reset
        # Inactive user should raise ValidationError with code 'user-not-active'
        request.user.is_active = False
        obj.request = request
        with self.assertRaises(ValidationError) as cm:
            obj.sanity_checks
        self.assertEqual(cm.exception.code, 'user-not-active')
        request.user.is_active = True  # reset
        # Banned user should raise ValidationError with code 'user-banned'
        request.user.is_banned = True
        obj.request = request
        with self.assertRaises(ValidationError) as cm:
            obj.sanity_checks
        self.assertEqual(cm.exception.code, 'user-banned')
        request.user.is_banned = False  # reset
        # Emergency Shutdown option should raise ValidationError with code 'emergency-shutdown' when enabled
        o = Option.objects.get(code='emergency-shutdown')
        o.value = 'true'
        o.save()
        obj.request = request
        with self.assertRaises(ValidationError) as cm:
            obj.sanity_checks
        self.assertEqual(cm.exception.code, 'emergency-shutdown')


    def test_historymodel_self_approve(self):
        # Set Up
        obj = Media(title='Test')
        request = self.factory.get('/')
        request.user = get_user_model().objects.create_user(username='test_user', email='test@example.com')
        obj.request = request
        obj._cr = obj.create_changerequest()
        # Sanity checks for next test
        self.assertEqual(obj._cr.request_type, ChangeRequest.Type.ADD)
        self.assertNotIn(obj._cr.request_type, Media.HISTORY_APPROVE_ACTIONS)
        # Should return False because user is less than a week old (and also action isn't in approved list)
        self.assertFalse(obj.self_approve)
        del obj.self_approve  # reset
        # Should return True as user now has proper permission
        request.user = user_add_permission(ChangeRequest, 'self_approve', request.user)
        obj.request = request
        self.assertTrue(obj.self_approve)
        del obj.self_approve  # reset
        # Should return False because user doesn't have permission (so falls back on user is less than 1 week old)
        obj._cr = obj.create_changerequest(request_type=ChangeRequest.Type.DELETE)
        self.assertFalse(obj.self_approve)
        del obj.self_approve  # reset
        # Should return True as user now has proper permission
        request.user = user_add_permission(ChangeRequest, 'self_delete', request.user)
        obj.request = request
        self.assertTrue(obj.self_approve)
        del obj.self_approve  # reset
        # Should return False because while user account is old enough, action isn't in approved list
        request.user = get_user_model()\
            .objects.create_user(username='another_user', date_joined=(timezone.now() - timezone.timedelta(days=14)))
        obj.request = request
        self.assertFalse(obj.self_approve)
        del obj.self_approve  # reset
        # Sanity checks for next test
        obj._cr = obj.create_changerequest(request_type=ChangeRequest.Type.MODIFY)
        self.assertIn(obj._cr.request_type, Media.HISTORY_APPROVE_ACTIONS)
        self.assertIsNotNone(obj._cr.data_changed)
        self.assertTrue(any(f in obj._cr.data_changed.keys() for f in Media.HISTORY_MODERATE_FIELDS))
        # Should return False because action in approved list, but one of the changed fields (like title) isn't
        obj._cr = obj.create_changerequest(request_type=ChangeRequest.Type.MODIFY)
        self.assertFalse(obj.self_approve)
        del obj.self_approve  # reset
        # Should return True because changed fields is now None (so it doesn't check fields)
        obj._cr.data_changed = None
        self.assertTrue(obj.self_approve)


    def test_historymodel_create_changerequest(self):
        # Set Up
        obj = Media(title='Test')
        request = self.factory.get('/')
        request.user = get_user_model().objects.create_user(username='test_user', email='test@example.com')
        # Create change request
        obj.request = request
        obj.comment = 'Test Comment'
        cr = obj.create_changerequest()
        # Returned object should be a ChangeRequest object
        self.assertIsInstance(cr, ChangeRequest)
        # Object should be None
        self.assertIsNone(cr.object)
        # Object type should be set to Media content type
        self.assertEqual(cr.object_type, ContentType.objects.get_for_model(obj))
        # Object id should be None
        self.assertIsNone(cr.object_id)
        # Object str should be equal to string representation of object
        self.assertEqual(cr.object_str, str(obj))
        # Related type should be None
        self.assertIsNone(cr.related_type)
        # Request type should be ADD
        self.assertEqual(cr.request_type, ChangeRequest.Type.ADD)
        # Data revert should be None
        self.assertIsNone(cr.data_revert)
        # Data changed should not be None
        self.assertIsNotNone(cr.data_changed)
        # Data changed should at least have item 'title' with value 'Test'
        self.assertEqual(cr.data_changed['title'], 'Test')
        # Comment should be set to 'Test Comment'
        self.assertEqual(cr.comment, 'Test Comment')
        # User should be set to request.user
        self.assertEqual(cr.user, request.user)
        # Mod should be None
        self.assertIsNone(cr.mod)


    def test_historymodel_create_changerequest_anonymous(self):
        # Set Up
        obj = Media(title='Test')
        request = self.factory.get('/')
        request.user = AnonymousUser()
        # create_changerequest() calls changerequest.set_user() which assumes user is AnimeSukiUser instance
        # As that is not the case here, it should raise ValueError
        obj.request = request
        self.assertRaises(ValueError, obj.create_changerequest)
