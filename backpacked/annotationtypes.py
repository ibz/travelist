import os
import re
import subprocess
from tempfile import mkdtemp

from django import http
from django import forms
from django import template
from django.utils import html
from django.utils import simplejson

from backpacked import models
from backpacked import utils
from backpacked import views

import settings

def get_manager(content_type):
    return AnnotationManager.all[content_type]

def serialize(content):
    return simplejson.dumps(content)

def deserialize(content):
    if content is None:
        return {}
    if isinstance(content, dict):
        return content
    return simplejson.loads(content)

class CompositeContentWidget(forms.widgets.Widget):
    def render_one(self, label, widget, name, value, attrs=None, template=None):
        if not template:
            template = "%s"
        return template % ("<label for=\"%s\">%s:</label><br />%s" % (name, label, widget.render(name, value, attrs)))

    def render_set(self, widgets, name, value, attrs):
        strs = []
        for widget in widgets:
            name_ = "%s_%s" % (name, widget[0])
            value_ = value.get(widget[0])
            attrs_ = attrs.copy()
            attrs_['id'] = "id_%s" % name_
            template_ = len(widget) >= 4 and widget[3] or None
            strs.append(self.render_one(widget[1], widget[2], name_, value_, attrs_, template_))
        return "<br />".join(strs)

    def value_from_datadict(self, data, files, name):
        return dict([(field, data.get("%s_%s" % (name, field))) for field in self.subfields])

class AnnotationManager(object):
    all = {}

    class __metaclass__(type):
        def __init__(cls, name, bases, classdict):
            type.__init__(cls, name, bases, classdict)
            if hasattr(cls, 'content_type'):
                AnnotationManager.all[cls.content_type] = cls

    exclude_fields = []

    title_required = True

    trip_allowed = True
    point_allowed = True
    segment_allowed = True

    has_extended_content = False
    edit_content_as_file = False
    show_content_label = True

    user_levels = models.UserLevel.values

    is_photos = False

    can_attach_cost = False

    widget = None

    @classmethod
    def cost_content_types(_):
        return [c for c in models.ContentType.values
                if get_manager(c).can_attach_cost]

    def __init__(self, annotation):
        self.annotation = annotation

    @property
    def display_name(self):
        return self.annotation.title

    def render_short(self):
        raise NotImplementedError()

    def render(self, request):
        raise NotImplementedError()

    def clean_content(self, content):
        return content

    def after_save(self):
        pass

class ActivityAnnotationManager(AnnotationManager):
    content_type = models.ContentType.ACTIVITY

    widget = forms.widgets.Textarea

    can_attach_cost = True

    @property
    def display_name(self):
        display = "Activity: %s" % self.annotation.title
        if self.annotation.date:
            display += " (%s)" % utils.format_date_human(self.annotation.date)
        return display

    def render_short(self):
        t = template.loader.get_template("annotation_view_activity.html")
        c = template.Context({'annotation': self.annotation})

        return t.render(c)

    def clean_content(self, content):
        return re.sub("\r", "", content)

class UrlAnnotationManager(AnnotationManager):
    content_type = models.ContentType.URL

    widget = lambda _: forms.widgets.TextInput(attrs={'class': 'text'})

    def render_short(self):
        return "<a href=\"%s\">URL: %s</a>" % (html.escape(self.annotation.content),
                                               html.escape(self.annotation.title))

    def clean_content(self, content):
        return forms.fields.URLField().clean(content)

class ExternalPhotosAnnotationManager(UrlAnnotationManager):
    content_type = models.ContentType.EXTERNAL_PHOTOS

    is_photos = True

    def render_short(self):
        return "<a href=\"%s\">Photos: %s</a>" % (html.escape(self.annotation.content),
                                                  html.escape(self.annotation.title))

class Transportation:
    Means = utils.Enum([(0, "Unspecified"),
                        (1, "Airplane"),
                        (2, "Bike"),
                        (3, "Boat / Ferry"),
                        (4, "Bus"),
                        (5, "Car"),
                        (6, "Motorcycle"),
                        (7, "Train"),
                        (8, "Walk")])

    Class = utils.Enum([(0, "Unspecified"),
                        (1, "First class"),
                        (2, "Second class"),
                        (3, "Third class"),
                        (4, "First class sleeper"),
                        (5, "Second class sleeper"),
                        (6, "Third class sleeper"),
                        (7, "Economy"),
                        (8, "Business class")])

    ClassMapping = {Means.AIRPLANE: [Class.ECONOMY, Class.BUSINESS_CLASS],
                    Means.BOAT_X_FERRY: [Class.FIRST_CLASS, Class.SECOND_CLASS, Class.THIRD_CLASS,
                                         Class.FIRST_CLASS_SLEEPER, Class.SECOND_CLASS_SLEEPER, Class.THIRD_CLASS_SLEEPER],
                    Means.TRAIN: [Class.FIRST_CLASS, Class.SECOND_CLASS, Class.THIRD_CLASS,
                                  Class.FIRST_CLASS_SLEEPER, Class.SECOND_CLASS_SLEEPER, Class.THIRD_CLASS_SLEEPER]}

class TransportationWidget(CompositeContentWidget):
    subfields = ['means', 'class', 'comments']

    def render(self, name, value, attrs=None):
        value = deserialize(value)

        widgets = [('means', "Means", forms.widgets.Select(choices=Transportation.Means.choices)),
                   ('class', "Class", forms.widgets.Select(), "<span id=\"content_class\">%s</span>"),
                   ('comments', "Comments", forms.widgets.Textarea())]

        return self.render_set(widgets, name, value, attrs) \
            + "<script type=\"text/javascript\">init_annotation_edit_transportation(%s, %s, %s);</script>" \
            % (simplejson.dumps(dict(Transportation.Class.choices)),
               simplejson.dumps(Transportation.ClassMapping),
               value['class'])

class TransportationAnnotationManager(AnnotationManager):
    content_type = models.ContentType.TRANSPORTATION

    exclude_fields = ['title', 'date']

    title_required = False

    trip_allowed = False
    point_allowed = False

    show_content_label = False

    widget = TransportationWidget

    can_attach_cost = True

    @property
    def display_name(self):
        content = deserialize(self.annotation.content)
        return "Transportation: %s" % Transportation.Means.get_description(content['means'])

    def render_short(self):
        content = deserialize(self.annotation.content)
        for k, t in [('means', Transportation.Means), ('class', Transportation.Class)]:
            if content.has_key(k):
                content["%s_h" % k] = t.get_description(content[k])

        t = template.loader.get_template("annotation_view_transportation.html")
        c = template.Context({'annotation': self.annotation, 'content': content})

        return t.render(c)

    def clean_content(self, content):
        for k in ['means', 'class']:
            if content.has_key(k):
                try:
                    content[k] = int(content[k])
                except ValueError:
                    del content[k]
        content['comments'] = re.sub("\r", "", content['comments'])
        return serialize(content)

class GPSAnnotationManager(AnnotationManager):
    content_type = models.ContentType.GPS

    title_required = False

    user_levels = [models.UserLevel.PRO]

    has_extended_content = True
    edit_content_as_file = True

    widget = forms.widgets.FileInput

    @property
    def display_name(self):
        display = "GPS"
        if self.annotation.title:
            display += ": %s" % self.annotation.title
        return html.escape(display)

    def render_short(self):
        return "<a href=\"%s\">%s</a>" % (html.escape(self.annotation.url), self.display_name)

    def get_cache_filename(self):
        if self.annotation.id:
            return os.path.join(settings.GPS_ANNOTATION_CACHE_PATH, "%s.kmz" % self.annotation.id)
        else:
            return None

    def ensure_cache_file(self):
        cachefilename = self.get_cache_filename()
        assert cachefilename

        if os.path.exists(cachefilename):
            return

        tempdir = mkdtemp()
        gpxfilename = os.path.join(tempdir, "doc.gpx")
        kmlfilename = os.path.join(tempdir, "doc.kml")
        kmzfilename = os.path.join(tempdir, "doc.kmz")
        try:
            gpxfile = file(gpxfilename, "w")
            try:
                gpxfile.write(self.annotation.extended_content.content)
            finally:
                gpxfile.close()
            subprocess.check_call(["gpsbabel", "-i", "gpx", "-o", "kml", gpxfilename, kmlfilename])
            subprocess.check_call(["zip", "-q", "-j", kmzfilename, kmlfilename])
            os.rename(kmzfilename, cachefilename)
        finally:
            for f in [gpxfilename, kmlfilename, kmzfilename]:
                if os.path.exists(f):
                    os.unlink(f)
            os.rmdir(tempdir)

    def render(self, request):
        self.ensure_cache_file()

        f = open(self.get_cache_filename(), "rb")
        try:
            content = f.read()
        finally:
            f.close()

        response = http.HttpResponse(content, content_type="application/vnd.google-earth.kmz")
        response["Content-Length"] = len(content)
        response['Content-Disposition'] = "attachment; filename=%s.kmz" % self.annotation.id

        return response

    def clean_content(self, content):
        return content and content.read() or None

    def after_save(self):
        cachefilename = self.get_cache_filename()
        if os.path.exists(cachefilename):
            os.unlink(cachefilename)

AccomodationType = utils.Enum([(0, ""),
                               (1, "* Hotel"),
                               (2, "** Hotel"),
                               (3, "*** Hotel"),
                               (4, "**** Hotel"),
                               (5, "***** Hotel"),
                               (6, "Hostel"),
                               (7, "Bungalow")])

AccomodationRoomType = utils.Enum([(0, ""),
                                   (1, "Single room"),
                                   (2, "Double room"),
                                   (3, "Dorm"),
                                   (4, "Suite")])

AccomodationRating = utils.Enum([(-2, "Very poor"),
                                 (-1, "Poor"),
                                 (0, "Average"),
                                 (1, "Good"),
                                 (2, "Very good")])

class AccomodationInput(CompositeContentWidget):
    subfields = ['name', 'type', 'room_type', 'URL', 'email', 'address', 'phone_number', 'rating', 'comments']

    def render_basic(self, name, value, attrs=None):
        basic = [('name', "Name", forms.widgets.TextInput(attrs={'class': 'text'})),
                 ('type', "Type", forms.widgets.Select(choices=AccomodationType.choices)),
                 ('room_type', "Room type", forms.widgets.Select(choices=AccomodationRoomType.choices))]
        return self.render_set(basic, name, value, attrs) + "<br />" \
            "<a href=\"javascript:accomodation_toggle_contact();\">toggle contact details</a>" \
            " | " \
            "<a href=\"javascript:accomodation_toggle_rating();\">toggle rating</a>"

    def render_contact(self, name, value, attrs=None):
        contact = [('URL', "URL", forms.widgets.TextInput(attrs={'class': 'text'})),
                   ('address', "Address", forms.widgets.TextInput(attrs={'class': 'text'})),
                   ('email', "Email", forms.widgets.TextInput(attrs={'class': 'text'})),
                   ('phone_number', "Phone number", forms.widgets.TextInput(attrs={'class': 'text'}))]
        return "<div id=\"accomodation-contact\" style=\"display: none;\">%s</div>" \
            % self.render_set(contact, name, value, attrs)

    def render_rating_stars(self, value):
        checked = lambda r: value and r == value and "checked=\"checked\"" or ""
        return "".join(["<input name=\"content_rating\" type=\"radio\" class=\"star\" value=\"%s\" title=\"%s\" %s />" \
                            % (r, AccomodationRating.get_description(r), checked(r))
                        for r in sorted(AccomodationRating.values)])

    def render_rating(self, name, value, attrs=None):
        rating = [('comments', "Comments", forms.widgets.Textarea())]
        return "<div id=\"accomodation-rating\" style=\"display: none;\">" \
            "<label for=\"content_rating\">Rating:</label><br />%s<br />%s" \
            "</div>" % (self.render_rating_stars(value.get('rating')),
                        self.render_set(rating, name, value, attrs))

    def render(self, name, value, attrs=None):
        value = deserialize(value)
        render_funcs = [self.render_basic, self.render_contact, self.render_rating]
        return "".join([render_func(name, value, attrs) for render_func in render_funcs])

class AccomodationAnnotationManager(AnnotationManager):
    content_type = models.ContentType.ACCOMODATION

    exclude_fields = ['title']

    title_required = False

    trip_allowed = False
    point_allowed = True
    segment_allowed = False

    show_content_label = False

    widget = AccomodationInput

    can_attach_cost = True

    @property
    def display_name(self):
        display = "Accomodation"
        if self.annotation.date:
            display += " (%s)" % utils.format_date_human(self.annotation.date)
        return display

    def render_short(self):
        content = deserialize(self.annotation.content)
        for k, t in [('type', AccomodationType), ('room_type', AccomodationRoomType), ('rating', AccomodationRating)]:
            if content.has_key(k):
                content["%s_h" % k] = t.get_description(content[k])

        t = template.loader.get_template("annotation_view_accomodation.html")
        c = template.Context({'annotation': self.annotation, 'content': content})

        return t.render(c)

    def clean_content(self, content):
        if not content.get('name'):
            raise forms.util.ValidationError("The name is mandatory.")
        if content.get('URL'):
            content['URL'] = forms.fields.URLField().clean(content['URL'])
        for k in ['type', 'room_type', 'rating']:
            if content.has_key(k):
                try:
                    content[k] = int(content[k])
                except ValueError:
                    del content[k]
        content['comments'] = re.sub("\r", "", content['comments'])
        return serialize(content)

class CostWidget(CompositeContentWidget):
    subfields = ['value', 'currency', 'parent', 'comments']

    def render(self, name, value, attrs=None):
        value = deserialize(value)

        annotations = self.annotation.point.annotation_set
        annotations = annotations.filter(content_type__in=AnnotationManager.cost_content_types(),
                                         segment=self.annotation.segment)
        annotation_choices = [("", "")]
        annotation_choices.extend([(a.id, a.manager.display_name) for a in annotations])

        widgets = [('value', "Value", forms.widgets.TextInput(attrs={'class': 'text'})),
                   ('currency', "Currency", forms.widgets.TextInput(attrs={'class': 'text'})),
                   ('parent', "Attach to", forms.widgets.Select(choices=annotation_choices)),
                   ('comments', "Comments", forms.widgets.Textarea())]
        return self.render_set(widgets, name, value, attrs)

class CostAnnotationManager(AnnotationManager):
    content_type = models.ContentType.COST

    exclude_fields = ['title']

    title_required = False

    show_content_label = False

    widget = CostWidget

    def render_short(self):
        content = deserialize(self.annotation.content)
        parent = content.get('parent') and models.Annotation.objects.get(id=content['parent']) or None

        t = template.loader.get_template("annotation_view_cost.html")
        c = template.Context({'annotation': self.annotation, 'content': content,
                              'parent': parent})

        return t.render(c)

    def clean_content(self, content):
        if not content.get('value') or not content.get('currency'):
            raise forms.util.ValidationError("Value and currency are mandatory.")
        try:
            content['value'] = float(content['value'])
        except ValueError:
            raise forms.util.ValidationError("The value is invalid.")
        content['comments'] = re.sub("\r", "", content['comments'])
        return serialize(content)

class NoteAnnotationManager(AnnotationManager):
    content_type = models.ContentType.NOTE

    widget = forms.widgets.Textarea

    @property
    def display_name(self):
        display = "Note: %s" % self.annotation.title
        if self.annotation.date:
            display += " (%s)" % utils.format_date_human(self.annotation.date)
        return display

    def render_short(self):
        t = template.loader.get_template("annotation_view_note.html")
        c = template.Context({'annotation': self.annotation})

        return t.render(c)

    def clean_content(self, content):
        return re.sub("\r", "", content)
