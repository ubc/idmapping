from django.conf.urls import url

from idm.views import SingleMappingView

urlpatterns = [
    url(r'^map', SingleMappingView.as_view()),
]
