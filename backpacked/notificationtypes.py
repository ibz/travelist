from datetime import datetime

from backpacked import models
from backpacked import utils

def get_manager(type):
    return NotificationManager.all[type]

Action = utils.Enum({'OK': (1, "OK", True),
                     'ACCEPT': (2, "Accept", True),
                     'REJECT': (3, "Reject", False)})

class NotificationManager(object):
    all = {}

    class __metaclass__(type):
        def __init__(cls, name, bases, classdict):
            type.__init__(cls, name, bases, classdict)
            if hasattr(cls, 'type'):
                NotificationManager.all[cls.type] = cls

    available_actions = [Action.OK]

    def __init__(self, notification):
        self.notification = notification

    @property
    def available_actions_choices(self):
        return [(a, Action.get_description(a), Action.get_extra(a))
                for a in self.available_actions]

    def render(self):
        raise NotImplementedError()

    def action(self, action_id):
        assert action_id in self.available_actions

class FriendRequestNotificationManager(NotificationManager):
    type = models.NotificationType.FRIEND_REQUEST

    available_actions = [Action.ACCEPT, Action.REJECT]

    def render(self):
        user_id = int(self.notification.content)
        user = models.User.objects.get(id=user_id)
        return "The user <a href=\"/people/%(user)s/\">%(user)s</a> wants to add you as a friend." % {'user': user.username}

    def action(self, action_id):
        action_id = int(action_id)
        super(FriendRequestNotificationManager, self).action(action_id)

        other_user = models.User.objects.get(id=int(self.notification.content))
        relationship = self.notification.user.get_relationship(other_user)

        if action_id == Action.ACCEPT:
            relationship.status = models.RelationshipStatus.CONFIRMED
            relationship.date_confirmed = datetime.now()
            relationship.save()
        elif action_id == Action.REJECT:
            relationship.delete()

        self.notification.delete()
