from django import http
from django import shortcuts
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from backpacked import annotationtypes
from backpacked import annotationui
from backpacked import models
from backpacked import utils
from backpacked import views

@require_GET
def view(request, trip_id, id):
    annotation = shortcuts.get_object_or_404(models.Annotation, id=id)
    if not annotation.is_visible_to(request.user):
        raise http.Http404()
    return annotation.manager.render(request)

def new_GET(request, annotation):
    form = annotationui.EditForm(annotation=annotation)
    return views.render("annotation_edit.html", request, {'annotation': annotation, 'form': form})

def new_POST(request, annotation):
    form = annotationui.EditForm(request.POST, request.FILES, annotation=annotation)
    if form.is_valid():
        form.save()
        return http.HttpResponseRedirect("/trips/%s/" % annotation.trip.id)
    else:
        return views.render("annotation_edit.html", request, {'annotation': annotation, 'form': form})

@login_required
@require_http_methods(["GET", "POST"])
def new(request, trip_id):
    content_type = int(request.GET.get('content_type', 0))
    assert content_type
    point_id = int(request.GET.get('point_id', 0)) or None
    segment = bool(int(request.GET.get('segment', 0)))

    if request.user.userprofile.level not in annotationtypes.get_manager(content_type).user_levels:
        return http.HttpResponseForbidden()

    point = models.Point.objects.get(id=point_id) if point_id else None
    annotation = models.Annotation(trip_id=trip_id, content_type=content_type, point=point, segment=segment)

    if request.method == 'GET':
        return new_GET(request, annotation)
    elif request.method == 'POST':
        return new_POST(request, annotation)

def edit_GET(request, annotation):
    form = annotationui.EditForm(annotation=annotation)
    return views.render("annotation_edit.html", request, {'annotation': annotation, 'form': form})

def edit_POST(request, annotation):
    form = annotationui.EditForm(request.POST, request.FILES, annotation=annotation)
    if form.is_valid():
        form.save()
        return http.HttpResponseRedirect("/trips/%s/" % annotation.trip.id)
    else:
        return views.render("annotation_edit.html", request, {'annotation': annotation, 'form': form})

@login_required
@require_http_methods(["GET", "POST"])
def edit(request, trip_id, id):
    annotation = shortcuts.get_object_or_404(models.Annotation, id=id, trip__user=request.user)
    if request.user.userprofile.level not in annotation.manager.user_levels:
        return http.HttpResponseForbidden()
    if request.method == 'GET':
        return edit_GET(request, annotation)
    elif request.method == 'POST':
        return edit_POST(request, annotation)

@login_required
@require_POST
def delete(request, trip_id, id):
    annotation = shortcuts.get_object_or_404(models.Annotation, id=id, trip__user=request.user)
    annotation.delete()
    return http.HttpResponse()
