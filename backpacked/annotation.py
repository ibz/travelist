from django import http
from django import shortcuts
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from backpacked import annotationui
from backpacked import models
from backpacked import utils
from backpacked import views

def all(request, trip_id):
    trip = shortcuts.get_object_or_404(models.Trip, id=trip_id)
    annotations = list(models.Annotation.objects.filter(trip=trip).all())
    grouped_annotations = dict([(c, []) for c in models.ContentType.values])
    for annotation in annotations:
        grouped_annotations[annotation.content_type].append(annotation)
    annotation_groups = [(k, models.ContentType.get_description(k), v)
                         for k, v in grouped_annotations.items()]
    return views.render("annotation_list.html", request,
                        {'trip': trip, 'annotation_groups': annotation_groups})

@require_GET
def view(request, trip_id, id):
    annotation = shortcuts.get_object_or_404(models.Annotation, id=id)
    if not annotation.is_visible_to(request.user):
        raise http.Http404()
    return views.render("annotation_view.html", request, {'annotation': annotation})

def edit_GET(request, annotation):
    form = annotationui.AnnotationEditForm(instance=annotation)
    return views.render("annotation_edit.html", request, {'annotation': annotation, 'form': form})

def edit_POST(request, annotation):
    form = annotationui.AnnotationEditForm(request.POST, instance=annotation)
    if form.is_valid():
        form.save()
        return http.HttpResponseRedirect("/trip/%s/annotation/all/" % annotation.trip.id)
    else:
        return views.render("annotation_edit.html", request, {'annotation': annotation, 'form': form})

@login_required
@require_http_methods(["GET", "POST"])
def new(request, trip_id):
    content_type = int(request.GET.get('content_type', 0))
    assert content_type
    annotation = models.Annotation(trip_id=trip_id, content_type=content_type)
    if request.method == 'GET':
        return edit_GET(request, annotation)
    elif request.method == 'POST':
        return edit_POST(request, annotation)

@login_required
@require_http_methods(["GET", "POST"])
def edit(request, trip_id, id):
    annotation = shortcuts.get_object_or_404(models.Annotation, id=id, trip__user=request.user)
    if request.method == 'GET':
        return edit_GET(request, annotation)
    elif request.method == 'POST':
        return edit_POST(request, annotation)

@login_required
@require_GET
def delete(request, trip_id, id):
    annotation = shortcuts.get_object_or_404(models.Annotation, id=id, trip__user=request.user)
    annotation.delete()
    return http.HttpResponseRedirect("/trip/%s/annotation/all/" % trip_id)
