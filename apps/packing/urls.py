"""
URL configuration for packing app.
"""

from django.urls import path

from . import views

app_name = "packing"

urlpatterns = [
    # Template management
    path("templates/", views.TemplateListView.as_view(), name="template_list"),
    path("templates/<uuid:pk>/", views.TemplateDetailView.as_view(), name="template_detail"),
    path("templates/create/", views.TemplateCreateView.as_view(), name="template_create"),
    path("templates/<uuid:pk>/edit/", views.TemplateUpdateView.as_view(), name="template_edit"),
    path("templates/<uuid:pk>/delete/", views.TemplateDeleteView.as_view(), name="template_delete"),
    # Trip packing lists (one per trip)
    path(
        "trip/<uuid:trip_pk>/create/", views.create_or_get_packing_list, name="create_packing_list"
    ),
    path("list/<uuid:pk>/", views.PackingListDetailView.as_view(), name="list_detail"),
    path("list/<uuid:pk>/print/", views.print_packing_list, name="print_list"),
    path("list/<uuid:pk>/save-as-template/", views.save_as_template, name="save_as_template"),
    # Packing items
    path("list/<uuid:list_pk>/add-item/", views.add_packing_item, name="add_item"),
    path("list/<uuid:list_pk>/bulk-add/", views.bulk_add_items, name="bulk_add_items"),
    path("list/<uuid:list_pk>/rename-category/", views.rename_category, name="rename_category"),
    path("item/<uuid:pk>/toggle/", views.toggle_packed, name="toggle_packed"),
    path("item/<uuid:pk>/edit/", views.edit_packing_item, name="edit_item"),
    path("item/<uuid:pk>/delete/", views.delete_packing_item, name="delete_item"),
    # Outfit calculator
    path("list/<uuid:list_pk>/add-outfit/", views.add_outfit, name="add_outfit"),
]
