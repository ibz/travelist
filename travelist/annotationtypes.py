import os
import re
import subprocess
from tempfile import mkdtemp

from django import http
from django import forms
from django.utils import html
from django.utils import simplejson

from travelist import models
from travelist import utils
from travelist import views

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

    has_extended_content = False
    edit_content_as_file = False
    content_label = None

    user_levels = models.UserLevel.values

    can_attach_cost = False
    can_delete = True

    widget = None

    @property
    def can_edit(self):
        return self.widget is not None

    @classmethod
    def cost_content_types(_):
        return [c for c in models.ContentType.values
                if get_manager(c).can_attach_cost]

    def __init__(self, annotation):
        self.annotation = annotation

    @property
    def display_name(self):
        return self.annotation.title

    @property
    def edit_link_url(self):
        return "/trips/%s/annotations/%s/edit/" % (self.annotation.trip_id, self.annotation.id)

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
        return self.annotation.title

    def render_short(self):
        return "<h5>%s</h5><p>%s</p>" % (self.display_name,
                                         self.annotation.content.replace("\n", "<br />"))

    def clean_content(self, content):
        return content.replace("\r", "")

class UrlAnnotationManager(AnnotationManager):
    content_type = models.ContentType.URL

    widget = lambda _: forms.widgets.TextInput(attrs={'class': 'text'})

    def render_short(self):
        return "<a href=\"%s\">%s</a>" % (html.escape(self.annotation.content),
                                          html.escape(self.annotation.title))

    def clean_content(self, content):
        return forms.fields.URLField().clean(content)

class ExternalPhotosAnnotationManager(UrlAnnotationManager):
    content_type = models.ContentType.EXTERNAL_PHOTOS

    content_label = "Link to your photo album"

    @property
    def display_name(self):
        return "Photos: %s" % self.annotation.name

    def render_short(self):
        return "Photos: <a href=\"%s\">%s</a>" % \
            (html.escape(self.annotation.content),
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

class TransportationAnnotationManager(AnnotationManager):
    content_type = models.ContentType.TRANSPORTATION

    exclude_fields = ['title', 'visibility']
    widget = lambda _: forms.widgets.Select(choices=Transportation.Means.choices)
    can_attach_cost = True
    can_delete = False

    @property
    def display_name(self):
        return Transportation.Means.get_description(int(self.annotation.content))

    @property
    def edit_link_url(self):
        return "#"

    @property
    def edit_link_click(self):
        return "javascript:transportation_edit(this, %s);" % self.annotation.id

    def render_short(self):
        return "Transportation: <span data-id=\"%s\">%s</span>" % (int(self.annotation.content), self.display_name)

class GPSAnnotationManager(AnnotationManager):
    content_type = models.ContentType.GPS

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

class AccommodationInput(forms.widgets.Widget):
    def __init__(self, attrs=None, choices=[]):
        super(AccommodationInput, self).__init__(attrs)
        self.choices = choices

    def render(self, name, value, attrs=None):
        final_attrs = self.build_attrs(attrs)
        return forms.widgets.Select(final_attrs, self.choices).render(name, value) + \
            "<br />Can't find what you're looking for? <a href=\"javascript:accommodation_add();\">Add it!</a>"

class AccommodationAnnotationManager(AnnotationManager):
    content_type = models.ContentType.ACCOMMODATION

    exclude_fields = ['title']
    can_attach_cost = True

    def widget(self):
        choices = [(a.id, a.name) for a in self.annotation.point.place.accommodation_set.all()]
        return AccommodationInput(choices=choices)

    @property
    def accommodation(self):
        return models.Accommodation.objects.get(id=int(self.annotation.content))

    @property
    def display_name(self):
        return self.accommodation.name

    def render_short(self):
        return "<a href=\"%s\">%s</a>" % (self.accommodation.get_absolute_url(),
                                          html.escape(self.accommodation.name))

    def clean_content(self, content):
        try:
            return int(content)
        except ValueError:
            accommodation = models.Accommodation(name=content,
                                                 place=self.annotation.point.place)
            accommodation.save()
            return accommodation.id

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
    content_label = ""
    widget = CostWidget

    def render_short(self):
        content = deserialize(self.annotation.content)
        parent = models.Annotation.objects.get(id=content['parent']) if content.get('parent') else None

        str = "%s %s" % (content['value'], content['currency'])
        if parent:
            str += "<br /><span>%s</span>" % parent.manager.display_name
        if content.get('comments'):
            str += "<br /><span>%s</span>" % content['comments']

        return str

    def clean_content(self, content):
        if not content.get('value') or not content.get('currency'):
            raise forms.util.ValidationError("Value and currency are mandatory.")
        try:
            content['value'] = float(content['value'])
        except ValueError:
            raise forms.util.ValidationError("The value is invalid.")
        content['comments'] = content['comments'].replace("\r", "")
        return serialize(content)

class NoteAnnotationManager(AnnotationManager):
    content_type = models.ContentType.NOTE

    widget = forms.widgets.Textarea

    @property
    def display_name(self):
        return self.annotation.title

    def render_short(self):
        return "<h5>%s</h5><p>%s</p>" % (self.display_name,
                                         self.annotation.content.replace("\n", "<br />"))

    def clean_content(self, content):
        return content.replace("\r", "")

class TweetAnnotationManager(AnnotationManager):
    content_type = models.ContentType.TWEET

    widget = None

    @property
    def display_name(self):
        return self.annotation.content

    def render_short(self):
        return "<h5>%s</h5><p>%s</p>" % (utils.format_date_human(self.annotation.date),
                                         html.urlize(self.annotation.content))

    def clean_content(self, content):
        return content.replace("\r", "").replace("\n", " ")

class FlickrPhotoAnnotationManager(AnnotationManager):
    content_type = models.ContentType.FLICKR_PHOTO

    widget = None

    def render_short(self):
        content = simplejson.loads(self.annotation.content)
        return "<h5>%(title)s</h5><p><a href=\"%(url)s\"><img src=\"%(src)s\" title=\"%(title)s\" /></p></a>" \
            % {'src': content['thumbnail'], 'title': self.annotation.title, 'url': self.annotation.url}

    def render(self, request):
        content = simplejson.loads(self.annotation.content)
        trip = self.annotation.trip
        all_flickr_photos = list(trip.get_annotations_visible_to(request.user).filter(content_type=models.ContentType.FLICKR_PHOTO))
        count = len(all_flickr_photos)
        for current in range(count):
            if all_flickr_photos[current] == self.annotation:
                break
        prev = all_flickr_photos[current - 1]
        next = all_flickr_photos[(current + 1) % count]
        current += 1 # make it 1-based
        return views.render("annotation_view_flickr_photo.html", request,
                            {'trip': trip, 'annotation': self.annotation, 'photo': content,
                             'current': current, 'count': count,
                             'prev': prev, 'next': next})
