import importlib
import os
from typing import List, Type

import strawberry
from django.apps import apps
from django.db import connection
from strawberry.extensions import Extension
from strawberry.tools import merge_types
from strawberry.types.base import TypeDefinition
from strawberry_django.optimizer import DjangoOptimizerExtension


class SQLPrintingExtension(Extension):
    def on_request_end(self):
        for query in connection.queries:
            print(f"Query: {query['sql']}")
            print(f"Time: {query['time']}")
            print("---")


def find_graphql_modules() -> tuple[List[Type], List[Type]]:
    """Find all Query and Mutation classes from installed apps"""
    queries = []
    mutations = []

    for app_config in apps.get_app_configs():
        app_path = app_config.path
        queries_path = os.path.join(app_path, 'graphql', 'queries.py')
        mutations_path = os.path.join(app_path, 'graphql', 'mutations.py')

        # Import queries module if it exists
        if os.path.exists(queries_path):
            queries_module = importlib.import_module(f"{app_config.name}.graphql.queries")
            if hasattr(queries_module, "Query"):
                queries.append(getattr(queries_module, "Query"))

        # Import mutations module if it exists
        if os.path.exists(mutations_path):
            mutations_module = importlib.import_module(f"{app_config.name}.graphql.mutations")
            if hasattr(mutations_module, "Mutation"):
                mutations.append(getattr(mutations_module, "Mutation"))

    return queries, mutations


def combine_types(base_class_name: str, types: List[Type]) -> Type:
    """Combine multiple strawberry types into one"""
    if not types:
        return None

    # Create a new type with combined fields
    combined_fields = {}
    for type_ in types:
        type_def: TypeDefinition = type_._type_definition
        for field in type_def.fields:
            combined_fields[field.python_name] = field

    return strawberry.type(
        type(
            base_class_name,
            (),
            combined_fields
        )
    )


# Find and combine all queries and mutations
all_queries, all_mutations = find_graphql_modules()

Query = merge_types(
    "Query",
    tuple(all_queries)
)
Mutation = merge_types(
    "Mutation",
    tuple(all_mutations)
)

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[
        DjangoOptimizerExtension,
        SQLPrintingExtension,
    ]
)
