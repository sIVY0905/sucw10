def current_room(request):
    from apps.rooms.models import Room
    room = None
    if request.user.is_authenticated:
        current_room_id = request.session.get('current_room_id')
        try:
            room = Room.objects.get(id=current_room_id, members=request.user)
        except (Room.DoesNotExist, TypeError):
            room = None
    return {'room': room}