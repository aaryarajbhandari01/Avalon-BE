from rest_framework import filters


class SizeFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        size = request.query_params.get("size")
        if size:
            size = size.upper()
            return queryset.filter(size__name=size)
        return queryset


class CategoryFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        category = request.query_params.get("category")
        if category:
            return queryset.filter(category__name=category)
        return queryset
