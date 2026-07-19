from django.urls import path

from .views import (
    PersonListView, PersonDetailView, PersonCreateView, PersonUpdateView, PersonDeleteView,
    person_create_ajax, person_update_ajax,
    TeamListView, TeamDetailView, TeamCreateView, TeamUpdateView, TeamDeleteView,
    team_create_ajax, team_update_ajax,
    BranchAccessListView, BranchAccessCreateView, BranchAccessUpdateView, BranchAccessDeleteView,
    RoleListView, RoleDetailView, RoleCreateView, RoleUpdateView, RoleDeleteView,
    role_create_ajax, role_update_ajax,
    EmployeeRoleListView, EmployeeRoleCreateView, EmployeeRoleUpdateView, EmployeeRoleDeleteView,
    EmployeePerformanceListView, EmployeePerformanceCreateView, EmployeePerformanceUpdateView, EmployeePerformanceDeleteView,
    PermissionListView, PermissionDeleteView,
    permission_create_ajax, permission_update_ajax,
    employeerole_bulk_create,
)

urlpatterns = [
    # Person URLs
    path('persons/', PersonListView.as_view(), name='person-list'),
    path('persons/<str:slug>/', PersonDetailView.as_view(), name='person-detail'),
    path('persons/create/', PersonCreateView.as_view(), name='person-create'),
    path('persons/<str:slug>/update/', PersonUpdateView.as_view(), name='person-update'),
    path('persons/<str:slug>/delete/', PersonDeleteView.as_view(), name='person-delete'),
    path('persons/ajax/create/', person_create_ajax, name='person-create-ajax'),
    path('persons/ajax/<int:pk>/update/', person_update_ajax, name='person-update-ajax'),

    # Team URLs
    path('teams/', TeamListView.as_view(), name='team-list'),
    path('teams/<str:slug>/', TeamDetailView.as_view(), name='team-detail'),
    path('teams/create/', TeamCreateView.as_view(), name='team-create'),
    path('teams/<str:slug>/update/', TeamUpdateView.as_view(), name='team-update'),
    path('teams/<str:slug>/delete/', TeamDeleteView.as_view(), name='team-delete'),
    path('teams/ajax/create/', team_create_ajax, name='team-create-ajax'),
    path('teams/ajax/<int:pk>/update/', team_update_ajax, name='team-update-ajax'),

    # BranchAccess URLs
    path('branch-accesses/', BranchAccessListView.as_view(), name='branchaccess-list'),
    path('branch-accesses/create/', BranchAccessCreateView.as_view(), name='branchaccess-create'),
    path('branch-accesses/<int:pk>/update/', BranchAccessUpdateView.as_view(), name='branchaccess-update'),
    path('branch-accesses/<int:pk>/delete/', BranchAccessDeleteView.as_view(), name='branchaccess-delete'),

    # Role URLs
    path('roles/', RoleListView.as_view(), name='role-list'),
    path('roles/<str:slug>/', RoleDetailView.as_view(), name='role-detail'),
    path('roles/create/', RoleCreateView.as_view(), name='role-create'),
    path('roles/<str:slug>/update/', RoleUpdateView.as_view(), name='role-update'),
    path('roles/<str:slug>/delete/', RoleDeleteView.as_view(), name='role-delete'),
    path('roles/ajax/create/', role_create_ajax, name='role-create-ajax'),
    path('roles/ajax/<int:pk>/update/', role_update_ajax, name='role-update-ajax'),

    # EmployeeRole URLs
    path('employee-roles/', EmployeeRoleListView.as_view(), name='employeerole-list'),
    path('employee-roles/create/', EmployeeRoleCreateView.as_view(), name='employeerole-create'),
    path('employee-roles/<int:pk>/update/', EmployeeRoleUpdateView.as_view(), name='employeerole-update'),
    path('employee-roles/<int:pk>/delete/', EmployeeRoleDeleteView.as_view(), name='employeerole-delete'),
    path('employee-roles/bulk-create/', employeerole_bulk_create, name='employeerole-bulk-create'),

    # EmployeePerformance URLs
    path('employee-performances/', EmployeePerformanceListView.as_view(), name='employeeperformance-list'),
    path('employee-performances/create/', EmployeePerformanceCreateView.as_view(), name='employeeperformance-create'),
    path('employee-performances/<int:pk>/update/', EmployeePerformanceUpdateView.as_view(), name='employeeperformance-update'),
    path('employee-performances/<int:pk>/delete/', EmployeePerformanceDeleteView.as_view(), name='employeeperformance-delete'),

    # Permission URLs
    path('permissions/', PermissionListView.as_view(), name='permission-list'),
    path('permissions/<int:pk>/delete/', PermissionDeleteView.as_view(), name='permission-delete'),
    path('permissions/ajax/create/', permission_create_ajax, name='permission-create-ajax'),
    path('permissions/ajax/<int:pk>/update/', permission_update_ajax, name='permission-update-ajax'),
]
