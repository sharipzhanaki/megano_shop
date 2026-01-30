from .models import Basket, BasketItem
from catalog.models import Product


SESSION_KEY = "basket"

def get_session_basket(request):
    return request.session.setdefault(SESSION_KEY, {})


def get_or_create_user_basket(request):
    basket, _ = Basket.objects.get_or_create(user=request.user)
    return basket


def sync_session_basket_to_db(request) -> None:
    if not request.user.is_authenticated:
        return
    session_basket = get_session_basket(request)
    if not session_basket:
        return
    basket = get_or_create_user_basket(request)
    for product_id, count in session_basket.items():
        BasketItem.objects.update_or_create(
            basket=basket,
            product_id=int(product_id),
            defaults={"count": int(count)}
        )
    request.session[SESSION_KEY] = {}
    request.session.modified = True
