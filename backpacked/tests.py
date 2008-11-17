from datetime import date
from datetime import datetime
from datetime import timedelta

from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.models import User
from django.core import mail
from django.http import HttpRequest
from django.test import TestCase
from django.test.client import Client

from backpacked import views
from backpacked import account
from backpacked import forms
from backpacked import utils
from backpacked import models
from backpacked.models import Place
from backpacked.models import Trip
from backpacked.models import UserProfile

def get_user(username):
    return User.objects.get(username=username)

def get_request(method, data=None, username=None):
    request = HttpRequest()
    request.method = method
    if method == 'GET':
        request.GET = data
    elif method == 'POST':
        request.POST = data
    request.user = username and get_user(username) or AnonymousUser()

    return request

class TestLogin(TestCase):
    fixtures = ['test_data']

    def test_login(self):
        c = Client()

        self.assertEquals(c.login(username="traveler", password="traveler"), True)
        self.assertEquals(c.login(username="admin", password="admin"), True)

class TestUtils(TestCase):
    def test_find(self):
        self.assertEquals(utils.find([1, 2, 3, 4], lambda a: a == 2), 2)
        self.assertEquals(utils.find([1, 2, 3, 4], lambda a: a == 5), None)

class TestUrls(TestCase):
    fixtures = ['test_data']

    def setUp(self):
        self.c = Client()

    def _test_url(self, url, status_code):
        resp = self.c.get(url)

        self.failUnless(resp)
        self.assertEquals(resp.status_code, status_code,
            "%s returned %s, %s was expected" %
            (url, resp.status_code, status_code))

    def test_urls_nologin(self):
        urls = [("/media/css/main.css", 200),
                ("/", 200),
                ("/account/register/", 200),
                ("/accounts/activate/XXX/", 404),
                ("/account/details/", 302),
                ("/trip/all/", 302),
                ("/trip/1/", 200),
                ("/trip/1/edit/", 302)]

        for url, status_code in urls:
            self._test_url(url, status_code)

    def test_urls_login(self):
        urls = [("/", 302),
                ("/account/register/", 302),
                ("/accounts/activate/XXX/", 404),
                ("/account/details/", 200),
                ("/trip/all/", 200),
                ("/trip/1/", 200)]

        result = self.c.login(username="traveler", password="traveler")

        self.failUnless(result)

        for url, status_code in urls:
            self._test_url(url, status_code)

        self.c.logout()

class TestAccountRegistration(TestCase):
    def setUp(self):
        request = get_request('POST', {'username': "new_user",
                                       'email': "new_user@example.com",
                                       'password': "new_user_password",
                                       'alpha_code': "i want the alpha!"})
        account.register(request)
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
        account.activate(get_request('GET'), self.activation_key)

        user = User.objects.get(username="new_user")

        self.assertEquals(user.is_active, True)
