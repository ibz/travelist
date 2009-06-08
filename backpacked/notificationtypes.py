from datetime import datetime

from django.core import mail
from django.template import loader, Context

from backpacked import models
from backpacked import utils

import settings

def get_manager(type):
    return NotificationManager.all[type]

Action = utils.Enum({'OK': (1, "OK", "positive"),
                     'ACCEPT': (2, "Accept", "positive"),
                     'REJECT': (3, "Reject", "negative")})

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
    def type_name(self):
        return models.NotificationType.get_name(self.type)

    @property
    def available_actions_choices(self):
        return [{'id': a,
                 'name': Action.get_name(a),
                 'description': Action.get_description(a),
                 'class': Action.get_extra(a)[0]}
                for a in self.available_actions]

    def send_email(self):
        raise NotImplementedError()

    def render(self):
        raise NotImplementedError()

    def action(self, action_id, data):
        assert action_id in self.available_actions

class FriendRequestNotificationManager(NotificationManager):
    type = models.NotificationType.FRIEND_REQUEST

    available_actions = [Action.ACCEPT, Action.REJECT]

    def send_email(self):
        email_subject = "Friend request"
        email_body = (
"""Hello, %(user)s.
%(requesting_user)s wants to add you as a friend on backpacked.it.
You can accept his request by following this link: http://backpacked.it/notifications/
""" % (
                {'user': self.notification.user.username,
                 'requesting_user': models.User.objects.get(id=int(self.notification.content)).username}))
        mail.send_mail(email_subject,
                       email_body,
                       settings.SERVER_EMAIL,
                       [self.notification.user.email])

    def render(self):
        user_id = int(self.notification.content)
        user = models.User.objects.get(id=user_id)
        return "<a href=\"/people/%(user)s/\">%(user)s</a> wants to add you as a friend." % {'user': user.username}

    def action(self, action_id, data):
        super(FriendRequestNotificationManager, self).action(action_id, data)

        other_user = models.User.objects.get(id=int(self.notification.content))
        relationship = self.notification.user.get_relationship(other_user)

        if action_id == Action.ACCEPT:
            relationship.status = models.RelationshipStatus.CONFIRMED
            relationship.date_confirmed = datetime.now()
            relationship.save()
        elif action_id == Action.REJECT:
            relationship.delete()

        self.notification.delete()

class TripShareRequestNotificationManager(NotificationManager):
    type = models.NotificationType.TRIP_LINK_REQUEST

    available_actions = [Action.ACCEPT, Action.REJECT]

    def send_email(self):
        email_subject = "Trip share request"
        email_body = (
"""Hello, %(user)s.
%(requesting_user)s wants to add you to one of his trips on backpacked.it.
You can accept his request by following this link: http://backpacked.it/notifications/
""" % (
                {'user': self.notification.user.username,
                 'requesting_user': models.TripLink.objects.get(id=int(self.notification.content)).lhs.user.username}))
        mail.send_mail(email_subject,
                       email_body,
                       settings.SERVER_EMAIL,
                       [self.notification.user.email])

    def render(self):
        trip = models.TripLink.objects.get(id=int(self.notification.content)).lhs
        linkable_trips = models.Trip.objects.filter(user=self.notification.user)
        linkable_places = sorted(set(p.place for p in trip.point_set.all()))
        context = Context({'id': self.notification.id, 'trip': trip, 'linkable_trips': linkable_trips, 'linkable_places': linkable_places})
        return loader.get_template("_notification_trip_link_request.html").render(context)

    def action(self, action_id, data):
        super(TripShareRequestNotificationManager, self).action(action_id, data)

        link = models.TripLink.objects.get(id=int(self.notification.content))
        rhs_user = self.notification.user

        if action_id == Action.ACCEPT:
            link.status = models.RelationshipStatus.CONFIRMED
            link.date_confirmed = datetime.now()
            if data['copy_status'] == 'copy':
                link.rhs = link.lhs.copy(user=rhs_user)
            else:
                link.rhs = models.Trip.objects.get(id=int(data['link_to_trip']), user=rhs_user)
            if data['link_type'] != 'whole':
                link.start_place = models.Place.objects.get(id=int(data['start_place']))
                link.end_place = models.Place.objects.get(id=int(data['end_place']))
            link.save()
        elif action_id == Action.REJECT:
            link.delete()

        self.notification.delete()
