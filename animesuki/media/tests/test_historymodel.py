from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from animesuki.history.models import ChangeRequest
from ..models import Media


class HistoryModelTest(TestCase):
    """
    This class tests HistoryModel through the Media class. This couldn't be put in the History app because
    HistoryModel is an abstract model and writing simple tests for Abstract models is basically impossible.

    This TestCase attempts to only test base HistoryModel functionality as far as possible.
    """

    def setUp(self):
        self.factory = RequestFactory()

    def test_historymodel_create_changerequest(self):
        # Set Up
        obj = Media(title='Test')
        request = self.factory.get('/')
        request.user = get_user_model().objects.create_user(username='test_user')
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
        # Object str should be empty
        self.assertEqual(cr.object_str, '')
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
