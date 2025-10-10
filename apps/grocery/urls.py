from django.urls import path

from . import views

app_name = "grocery"

urlpatterns = [
    # Template URLs
    path("templates/", views.template_list, name="template_list"),
    path("templates/<uuid:pk>/", views.template_detail, name="template_detail"),
    path("templates/create/", views.template_create, name="template_create"),
    path("templates/<uuid:pk>/edit/", views.template_edit, name="template_edit"),
    path("templates/<uuid:pk>/delete/", views.template_delete, name="template_delete"),
    # Trip Grocery List URLs
    path("trip/<uuid:trip_pk>/lists/", views.trip_grocery_lists, name="trip_grocery_lists"),
    path(
        "trip/<uuid:trip_pk>/create-from-template/<uuid:template_pk>/",
        views.list_create_from_template,
        name="list_create_from_template",
    ),
    path("trip/<uuid:trip_pk>/create-blank/", views.list_create_blank, name="list_create_blank"),
    # Grocery List URLs
    path("list/<uuid:pk>/", views.list_detail, name="list_detail"),
    path("list/<uuid:pk>/edit/", views.list_edit, name="list_edit"),
    path("list/<uuid:pk>/delete/", views.list_delete, name="list_delete"),
    path("list/<uuid:pk>/print/", views.list_print, name="list_print"),
    path("list/<uuid:pk>/save-as-template/", views.save_as_template, name="save_as_template"),
    # Item URLs
    path("list/<uuid:list_pk>/add-item/", views.add_item, name="add_item"),
    path("list/<uuid:list_pk>/bulk-add/", views.bulk_add_items, name="bulk_add_items"),
    path("list/<uuid:list_pk>/rename-category/", views.rename_category, name="rename_category"),
    path("item/<uuid:pk>/edit/", views.edit_item, name="edit_item"),
    path("item/<uuid:pk>/delete/", views.delete_item, name="delete_item"),
    path("item/<uuid:pk>/toggle/", views.toggle_purchased, name="toggle_purchased"),
]
