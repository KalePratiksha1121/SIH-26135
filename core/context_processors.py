from .views import AVATARS


def role_context(request):
    role = None
    avatar = None
    if request.user.is_authenticated:
        username = request.user.username
        if username.startswith('gov_'):
            role, avatar = 'Government Admin', AVATARS['gov_admin']
        elif username.startswith('employer'):
            role, avatar = 'Employer', AVATARS['employer1']
        elif username.startswith('trainee'):
            role, avatar = 'Trainee', AVATARS['trainee_demo']
        elif username.startswith('provider'):
            role, avatar = 'Training Provider', AVATARS['provider1']
        else:
            role, avatar = 'Staff', AVATARS['gov_admin']
    return {'current_role': role, 'current_avatar': avatar}
