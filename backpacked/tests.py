from datetime import date
from datetime import datetime
from datetime import timedelta
from unittest import TestCase

from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.models import User
from django.core import mail
from django.http import HttpRequest
from django.test.client import Client

from backpacked import views
from backpacked import forms
from backpacked import utils
from backpacked import models
from backpacked.models import Trip
from backpacked.models import UserProfile

def get_user(username):
    return User.objects.get(username=username)

def get_request(get=None, post=None, username=None):
    user = username and get_user(username) or AnonymousUser()

    request = HttpRequest()
    request.user = user
    request.GET = get or {}
    request.POST = post or {}

    return request

class TestLogin(TestCase):
    def test_login(self):
        c = Client()

        self.assertEquals(c.login(username="traveler", password="traveler"), True)
        self.assertEquals(c.login(username="admin", password="admin"), True)

class TestUtils(TestCase):
    def test_group_items(self):
        self.assertEquals(utils.group_items([1, 2, 3, 1, 3, 4], lambda a, b: a == b),
                          [[1, 1], [2], [3, 3], [4]])

    def test_find(self):
        self.assertEquals(utils.find([1, 2, 3, 4], lambda a: a == 2), 2)
        self.assertEquals(utils.find([1, 2, 3, 4], lambda a: a == 5), None)

class TestUrls(TestCase):
    def setUp(self):
        self.c = Client()

    def _test_url(self, url, status_code):
        resp = self.c.get(url)

        self.failUnless(resp)
        self.assertEquals(resp.status_code, status_code,
            "%s returned %s, %s was expected" %
            (url, resp.status_code, status_code))

    def test_urls_nologin(self):
        urls = [("/admin/", 200),
                ("/media/css/main.css", 200),
                ("/", 200),
                ("/account/register/", 200),
                ("/accounts/activate/XXX/", 404),
                ("/account/details/", 302),
                ("/trip/list/", 302),
                ("/trip/1/", 200),
                ("/trip/1/edit/", 302),
                ("/widget/segment_input/", 400)]

        for url, status_code in urls:
            self._test_url(url, status_code)

    def test_urls_login(self):
        urls = [("/", 200),
                ("/account/register/", 302),
                ("/accounts/activate/XXX/", 404),
                ("/account/details/", 200),
                ("/trip/list/", 200),
                ("/trip/1/", 200),
                ("/trip/1/edit/", 200),
                ("/widget/segment_input/", 400)]

        result = self.c.login(username="traveler", password="traveler")

        self.failUnless(result)

        for url, status_code in urls:
            self._test_url(url, status_code)

        self.c.logout()

class TestAccountRegistration(TestCase):
    def setUp(self):
        request = get_request(post={'username': "new_user",
                                    'email': "new_user@example.com",
                                    'password': "new_user_password"})
        views.account_register(request)
        user = User.objects.get(username="new_user")
        self.activation_key = user.userprofile.activation_key

    def tearDown(self):
        User.objects.get(username="new_user").delete()
        mail.outbox = []

    def test_account_register(self):
        user = User.objects.get(username="new_user")

        self.assertEquals(user.is_staff, False)
        self.assertEquals(user.is_superuser, False)
        self.assertEquals(user.is_active, False)
        self.assertEquals(user.userprofile.key_expires.date(),
                          (datetime.today() + timedelta(2)).date())
        self.assertEquals(len(mail.outbox), 1)
        activation_link = "/account/activate/%s/" % self.activation_key
        self.assert_(activation_link in mail.outbox[0].body)

    def test_account_activate(self):
        views.account_activate(get_request(), self.activation_key)

        user = User.objects.get(username="new_user")

        self.assertEquals(user.is_active, True)

class TestSegmentInput(TestCase):
    def test_value_from_datadict(self):
        widget = forms.SegmentInput()

        data = {'xxx_p1_place': "AAA",
                'xxx_p2_place': "BBB",
                'xxx_start_date': "CCC",
                'xxx_end_date': "DDD",
                'xxx_transportation_method': "EEE",
                "some_other_data": "XXX"}

        expected_result = {'p1_place': "AAA",
                           'p2_place': "BBB",
                           'start_date': "CCC",
                           'end_date': "DDD",
                           'transportation_method': "EEE"}

        result = widget.value_from_datadict(data, None, 'xxx')

        self.assertEquals(result, expected_result)

class TestPathInput(TestCase):
    def test_value_from_datadict(self):
        widget = forms.PathInput()
        segment_widget = forms.SegmentInput()

        data = {'xxx_0_p1_place': "AAA0",
                'xxx_0_p2_place': "BBB0",
                'xxx_0_start_date': "CCC0",
                'xxx_0_end_date': "DDD0",
                'xxx_0_transportation_method': "EEE0",
                'xxx_3_p1_place': "AAA3",
                'xxx_3_p2_place': "BBB3",
                'xxx_3_start_date': "CCC3",
                'xxx_3_end_date': "DDD3",
                'xxx_3_transportation_method': "EEE3",
                "some_other_data": "XXX"}

        expected_result = [{'xxx_0_p1_place': "AAA0",
                            'xxx_0_p2_place': "BBB0",
                            'xxx_0_start_date': "CCC0",
                            'xxx_0_end_date': "DDD0",
                            'xxx_0_transportation_method': "EEE0"},
                           {'xxx_3_p1_place': "AAA3",
                            'xxx_3_p2_place': "BBB3",
                            'xxx_3_start_date': "CCC3",
                            'xxx_3_end_date': "DDD3",
                            'xxx_3_transportation_method': "EEE3"}]
        expected_result[0] = segment_widget.value_from_datadict(expected_result[0], None, 'xxx_0')
        expected_result[1] = segment_widget.value_from_datadict(expected_result[1], None, 'xxx_3')

        result = widget.value_from_datadict(data, None, 'xxx')

        self.assertEquals(result, expected_result)


class TestPathField(TestCase):
    def test_clean(self):
        field = forms.PathField()

        data = [{'p1_place': "1",
                 'p2_place': "2",
                 'start_date': "2007-01-01",
                 'end_date': "2007-01-03",
                 'transportation_method': "1"},
                {'p1_place': "2",
                 'p2_place': "3",
                 'start_date': "2007-01-05",
                 'end_date': "2007-01-07",
                 'transportation_method': "2"}]

        expected_segments = [{'p1_place': 1,
                              'p2_place': 2,
                              'start_date': datetime(2007, 1, 1, 0, 0),
                              'end_date': datetime(2007, 1, 3, 0, 0),
                              'transportation_method': 1},
                             {'p1_place': 2,
                              'p2_place': 3,
                              'start_date': datetime(2007, 1, 5, 0, 0),
                              'end_date': datetime(2007, 1, 7, 0, 0),
                              'transportation_method': 2}]
        expected_places = [1, 2, 3]

        segments, places = field.clean(data)

        self.assertEquals(segments, expected_segments)
        self.assertEquals(places, expected_places)

class TestTripEditForm(TestCase):
    def _get_trip_data(self, name, start_date, end_date, visibility):
        return {'name': name,
                'start_date': start_date,
                'end_date': end_date,
                'visibility': visibility}

    def _get_segment_data(self, i,
                          p1_place, p2_place,
                          start_date, end_date,
                          transportation_method):
        return {"path_%s_p1_place" % i: p1_place,
                "path_%s_p2_place" % i: p2_place,
                "path_%s_start_date" % i: start_date,
                "path_%s_end_date" % i: end_date,
                "path_%s_transportation_method" % i: transportation_method}

    def _create_trip(self, *args):
        trip = Trip(user=get_user("traveler"))
        self._edit_trip(trip, *args)
        return trip.id

    def _edit_trip(self, trip, name, start_date, end_date, segments=[], visibility=models.PUBLIC):
        data = self._get_trip_data(name, start_date, end_date, visibility)
        for segment in segments:
            data.update(self._get_segment_data(*segment))
        form = forms.TripEditForm(data, instance=trip)
        form.save()

        return trip.id

    def _assert_segment_data_equals(self, segment,
                                    p1_place, p2_place,
                                    start_date, end_date,
                                    transportation_method):

        self.assertEquals(segment.p1.place_id, p1_place)
        self.assertEquals(segment.p2.place_id, p2_place)
        self.assertEquals(segment.start_date, start_date)
        self.assertEquals(segment.end_date, end_date)
        self.assertEquals(segment.transportation_method, transportation_method)

    def test_create_trip(self):
        trip_id = self._create_trip("Some test trip", "2007-01-01", "2007-02-01")

        trip = Trip.objects.get(id=trip_id)

        self.failUnless(trip.id)
        self.assertEquals(trip.name, "Some test trip")
        self.assertEquals(trip.start_date, date(2007, 1, 1))
        self.assertEquals(trip.end_date, date(2007, 2, 1))

    def test_create_trip_with_segments(self):
        trip_id = self._create_trip("Some test trip", "2007-02-01", "2007-02-10",
                                    [(0, 1, 2, "2007-02-01", "2007-02-05", 1),
                                     (1, 2, 3, "2007-02-05", "2007-02-10", 2)])

        trip = Trip.objects.get(id=trip_id)

        self.failUnless(trip.id)
        self.assertEquals(trip.name, "Some test trip")
        self.assertEquals(trip.start_date, date(2007, 2, 1))
        self.assertEquals(trip.end_date, date(2007, 2, 10))

        segments = list(trip.segment_set.all())
        points = list(trip.point_set.all())

        segments.sort()
        self._assert_segment_data_equals(segments[0],
                                         *(1, 2, datetime(2007, 2, 1), datetime(2007, 2, 5), 1))
        self._assert_segment_data_equals(segments[1],
                                         *(2, 3, datetime(2007, 2, 5), datetime(2007, 2, 10), 2))

        self.assertEquals(sorted([p.place_id for p in points]), [1, 2, 3])

    def test_edit_trip(self):
        trip_id = self._create_trip("Some test trip", "2007-02-01", "2007-02-10",
                                    [(0, 1, 2, "2007-02-01", "2007-02-05", 1),
                                     (1, 2, 3, "2007-02-05", "2007-02-10", 2)])

        trip = Trip.objects.get(id=trip_id)

        # change name and dates

        self._edit_trip(trip, "New name", "2007-03-01", "2007-03-10",
                        [(0, 1, 2, "2007-03-01", "2007-03-05", 2),
                         (1, 2, 3, "2007-03-05", "2007-03-10", 1)])

        trip = Trip.objects.get(id=trip_id)

        self.failUnless(trip.id)
        self.assertEquals(trip.name, "New name")
        self.assertEquals(trip.start_date, date(2007, 3, 1))
        self.assertEquals(trip.end_date, date(2007, 3, 10))

        segments = list(trip.segment_set.all())
        points = list(trip.point_set.all())

        segments.sort()
        self.assertEquals(len(segments), 2)
        self._assert_segment_data_equals(segments[0],
                                         *(1, 2, datetime(2007, 3, 1), datetime(2007, 3, 5), 2))
        self._assert_segment_data_equals(segments[1],
                                         *(2, 3, datetime(2007, 3, 5), datetime(2007, 3, 10), 1))

        self.assertEquals(sorted([p.place_id for p in points]), [1, 2, 3])

        # add segment

        self._edit_trip(trip, "New name", "2007-03-01", "2007-03-10",
                        [(0, 1, 2, "2007-03-01", "2007-03-05", 2),
                         (1, 2, 3, "2007-03-05", "2007-03-07", 1),
                         (3, 3, 0, "2007-03-07", "2007-03-10", 1)])

        segments = list(trip.segment_set.all())
        points = list(trip.point_set.all())

        segments.sort()
        self.assertEquals(len(segments), 3)
        self._assert_segment_data_equals(segments[0],
                                         *(1, 2, datetime(2007, 3, 1), datetime(2007, 3, 5), 2))
        self._assert_segment_data_equals(segments[1],
                                         *(2, 3, datetime(2007, 3, 5), datetime(2007, 3, 7), 1))
        self._assert_segment_data_equals(segments[2],
                                         *(3, 0, datetime(2007, 3, 7), datetime(2007, 3, 10), 1))

        self.assertEquals(sorted([p.place_id for p in points]), [0, 1, 2, 3])

        # edit / delete segment

        self._edit_trip(trip, "New name", "2007-03-01", "2007-03-10",
                        [(0, 1, 2, "2007-03-01", "2007-03-05", 2),
                         (4, 2, 1, "2007-03-05", "2007-03-10", 1)])

        segments = list(trip.segment_set.all())
        points = list(trip.point_set.all())

        segments.sort()
        self.assertEquals(len(segments), 2)
        self._assert_segment_data_equals(segments[0], *(1, 2, datetime(2007, 3, 1), datetime(2007, 3, 5), 2))
        self._assert_segment_data_equals(segments[1], *(2, 1, datetime(2007, 3, 5), datetime(2007, 3, 10), 1))

        self.assertEquals(sorted([p.place_id for p in points]), [1, 2])

        # add multiple segments between same points

        self._edit_trip(trip, "New name", "2007-03-01", "2007-03-10",
                        [(0, 1, 2, "2007-03-01", "2007-03-05", 2),
                         (4, 2, 1, "2007-03-05", "2007-03-06", 1),
                         (5, 1, 2, "2007-03-06", "2007-03-08", 2),
                         (1, 2, 1, "2007-03-09", "2007-03-10", 1)])

        segments = list(trip.segment_set.all())
        points = list(trip.point_set.all())

        segments.sort()
        self.assertEquals(len(segments), 4)
        self._assert_segment_data_equals(segments[0], *(1, 2, datetime(2007, 3, 1), datetime(2007, 3, 5), 2))
        self._assert_segment_data_equals(segments[1], *(2, 1, datetime(2007, 3, 5), datetime(2007, 3, 6), 1))
        self._assert_segment_data_equals(segments[2], *(1, 2, datetime(2007, 3, 6), datetime(2007, 3, 8), 2))
        self._assert_segment_data_equals(segments[3], *(2, 1, datetime(2007, 3, 9), datetime(2007, 3, 10), 1))

        self.assertEquals(sorted([p.place_id for p in points]), [1, 2])

        # deleting one of the doubled segments

        self._edit_trip(trip, "New name", "2007-03-01", "2007-03-10",
                        [(0, 1, 2, "2007-03-01", "2007-03-05", 2),
                         (4, 2, 1, "2007-03-05", "2007-03-06", 1),
                         (5, 1, 2, "2007-03-06", "2007-03-08", 2)])

        segments = list(trip.segment_set.all())
        points = list(trip.point_set.all())

        segments.sort()
        self.assertEquals(len(segments), 3)
        self._assert_segment_data_equals(segments[0], *(1, 2, datetime(2007, 3, 1), datetime(2007, 3, 5), 2))
        self._assert_segment_data_equals(segments[1], *(2, 1, datetime(2007, 3, 5), datetime(2007, 3, 6), 1))
        self._assert_segment_data_equals(segments[2], *(1, 2, datetime(2007, 3, 6), datetime(2007, 3, 8), 2))

        self.assertEquals(sorted([p.place_id for p in points]), [1, 2])
