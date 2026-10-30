def nexu(request):
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return {}
    # Perfil del postulante para el avatar, nombre y RUT del encabezado
    return {'postulante': getattr(user, 'postulante', None)}
