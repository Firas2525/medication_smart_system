from accounts.models import UserRelationship


def get_relationship_type_for_user(user_type):
    if user_type == 'doctor':
        return 'doctor_patient'
    if user_type == 'nurse':
        return 'nurse_patient'
    return None


def can_access_patient(current_user, patient_id):
    if not current_user or not getattr(current_user, 'is_authenticated', False):
        return False

    if current_user.user_type == 'patient':
        return current_user.id == patient_id

    if current_user.user_type in ['doctor', 'nurse']:
        relationship_type = get_relationship_type_for_user(current_user.user_type)
        return UserRelationship.objects.filter(
            doctor=current_user,
            patient_id=patient_id,
            relationship_type=relationship_type,
            status='active'
        ).exists()

    return getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
