from django.conf.urls import url

from idm.views import SingleMappingView, AttributeView

urlpatterns = [
    url(r'^map', SingleMappingView.as_view()),
    url(r'^attribute', AttributeView.as_view()),
]
