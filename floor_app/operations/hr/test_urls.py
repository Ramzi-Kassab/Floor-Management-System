from django.urls import include, path

from floor_app.operations.hr.tests import planning_stub_urls, sales_stub_urls

urlpatterns = [
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include(('floor_app.operations.hr.urls', 'hr'), namespace='hr')),
    path('', include(('core.urls', 'core'), namespace='core')),
    path('inventory/', include(('floor_app.operations.inventory.urls', 'inventory'), namespace='inventory')),
    path('production/', include(('floor_app.operations.production.urls', 'production'), namespace='production')),
    path('evaluation/', include(('floor_app.operations.evaluation.urls', 'evaluation'), namespace='evaluation')),
    path('sales/', include((sales_stub_urls, 'sales'), namespace='sales')),
    path('planning/', include((planning_stub_urls, 'planning'), namespace='planning')),
    path('qrcodes/', include(('floor_app.operations.qrcodes.urls', 'qrcodes'), namespace='qrcodes')),
    path('purchasing/', include(('floor_app.operations.purchasing.urls', 'purchasing'), namespace='purchasing')),
    path('knowledge/', include(('floor_app.operations.knowledge.urls', 'knowledge'), namespace='knowledge')),
    path('maintenance/', include(('floor_app.operations.maintenance.urls', 'maintenance'), namespace='maintenance')),
    path('quality/', include(('floor_app.operations.quality.urls', 'quality'), namespace='quality')),
]
