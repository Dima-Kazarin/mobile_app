from background_task import background
from .models import Purchase, Reminder, User, Product
from django.utils.timezone import now
from datetime import timedelta

def fetch_user_purchases(user_id):
    return Purchase.objects.filter(user_id=user_id)


def filter_old_purchases(user_id, days_threshold):
    user = User.objects.get(id=user_id)
    cutoff_date = now() - timedelta(days=days_threshold)
    return Purchase.objects.filter(user=user, purchase_date__lte=cutoff_date)


def create_reminder(user_id, product_id):
    user = User.objects.get(id=user_id)
    product = Product.objects.get(id=product_id)
    reminder, created = Reminder.objects.get_or_create(
        user=user,
        product=product,
        defaults={'created_at': now()}
    )
    if created:
        print(f"Нагадування про продукт {product_id} успішно додана.")
    else:
        print(f"Нагадування про продукт {product_id} вже iснує.")


def process_user_reminders(user_id):
    old_purchases = filter_old_purchases(user_id, 7)
    for purchase in old_purchases:
        create_reminder(user_id, purchase.product.id)


def process_all_users_reminders():
    users = User.objects.all()
    for user in users:
        process_user_reminders(user.id)

@background(schedule=60 * 60 * 24)
def daily_reminder_task():
    process_all_users_reminders()