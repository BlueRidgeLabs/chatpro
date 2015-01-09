from __future__ import absolute_import, unicode_literals

from chatpro.test import ChatProTest


class UserPatchTest(ChatProTest):
    def test_is_admin_for(self):
        self.assertTrue(self.admin.is_admin_for(self.unicef))
        self.assertFalse(self.admin.is_admin_for(self.nyaruka))
        self.assertFalse(self.user1.is_admin_for(self.unicef))
