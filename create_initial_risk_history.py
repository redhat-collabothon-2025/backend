# Run this script to create initial risk history for all users
# Usage: python manage.py shell < create_initial_risk_history.py

from whitehat_app.models import User, RiskHistory
from django.utils import timezone

users = User.objects.all()
for user in users:
    # Only create if user doesn't have any risk history
    if not RiskHistory.objects.filter(user=user).exists():
        RiskHistory.objects.create(
            user=user,
            risk_score=user.risk_score,
            reason='Initial risk score baseline'
        )
        print(f'Created risk history for {user.email}')

print(f'Done! Created risk history for {users.count()} users')
