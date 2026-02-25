from functools import reduce

# Отфильтровать пользователей по заданным критериям.
# Для каждого пользователя рассчитать общую сумму его расходов.
# Получить общую сумму расходов всех отфильтрованных пользователей.

users = [
   {"name": f"User_{i:03d}", "expenses": [50 + (i % 100), 75 + (i % 80), 100 + (i % 60), 125 + (i % 50)]}
   for i in range(100)
]

# Фильтрация: пользователи с общей суммой расходов > 300
user_totals = [{'name': u['name'], 'total': sum(u['expenses'])} for u in users]
filtered_users = list(filter(lambda u: u['total'] > 300, user_totals))
print(f"Пользователей с расходами > 300: {len(filtered_users)}\n")

# Сумма расходов для каждого
user_sums = [
    {'name': u['name'], 'total': reduce(lambda acc, x: acc + x, u['expenses'], 0)}
    for u in users
]
print(f"Пользователь, сумма расходов: \n{user_sums}\n")

# Общая сумма
total_expenses = reduce(lambda acc, u: acc + u['total'], user_sums, 0)
print(f"Общая сумма расходов: \n{total_expenses}\n")