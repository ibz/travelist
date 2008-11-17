from django import http
from django import shortcuts
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from backpacked import forms
from backpacked import models
from backpacked import utils
from backpacked import views

@require_GET
def view(request, trip_id, entity, entity_id, id):
    annotation = shortcuts.get_object_or_404(models.Annotation, id=id)
    if annotation.is_visible_to(request.user):
        raise http.Http404()
    return views.render("annotation_view.html", request, {'annotation': annotation})

def edit_GET(request, trip_id, entity, entity_id, id=None):
    if id:
        annotation = shortcuts.get_object_or_404(models.Annotation, id=id)
        form = forms.AnnotationEditForm(instance=annotation)
    else:
        annotation = models.Annotation(trip_id=trip_id, entity=entity, entity_id=entity_id)
        form = forms.AnnotationNewForm(instance=annotation)
    return views.render("annotation_edit.html", request, {'trip_id': trip_id, 'annotation': annotation, 'form': form})

def edit_POST(request, trip_id, entity, entity_id, id=None):
    if id:
        annotation = shortcuts.get_object_or_404(models.Annotation, id=id)
        form = forms.AnnotationEditForm(request.POST, instance=annotation)
    else:
        annotation = models.Annotation(trip_id=trip_id, entity=entity, entity_id=entity_id)
        form = forms.AnnotationNewForm(request.POST, instance=annotation)
    if form.is_valid():
        annotation = form.save()
        return http.HttpResponseRedirect("/trip/%s/" % trip_id)
    else:
        return views.render("annotation_edit.html", request, {'trip_id': trip_id, 'annotation': annotation, 'form': form})

@login_required
@require_http_methods(["GET", "POST"])
def edit(request, trip_id, entity, entity_id, id=None):
    if request.method == 'GET':
        return edit_GET(request, trip_id, entity, entity_id, id=None)
    elif request.method == 'POST':
        return edit_POST(request, trip_id, entity, entity_id, id=None)

@login_required
@require_GET
def delete(request, trip_id, entity, entity_id, id):
    annotation = shortcuts.get_object_or_404(models.Annotation, id=id, trip__user=request.user)
    annotation.delete()
    return http.HttpResponseRedirect("/trip/%s/%s/%s/annotation/list/"
                                     % (trip_id, entity, entity_id))

@login_required
@require_GET
def widget_content_input(request):
    content_type = int(request.GET['content_type'])
    content_type_selector = request.GET['content_type_selector']
    name = request.GET['name']
    input = forms.ContentInput(content_type, content_type_selector)
    return http.HttpResponse(input.render(name, None))
