from functools import reduce

# Отфильтровать заказы только для определенного клиента с заданным идентификатором клиента.
# Подсчитать общую сумму всех заказов для данного клиента.
# Найти среднюю стоимость заказов для данного клиента.

orders = [
    {"order_id": i, "customer_id": 101 + (i % 10), "amount": 50.0 + (i * 1.5)}
    for i in range(1, 101)
]

# Фильтрация: заказы для customer_id 101
filtered_orders = list(filter(lambda o: o['customer_id'] == 101, orders))
print(f"Заказы для клиента с id 101: \n{filtered_orders}\n")

# Сумма заказов
total_amount = reduce(lambda acc, o: acc + o['amount'], filtered_orders, 0)
print(f"Сумма заказов этого клиента: \n{total_amount}\n")

# Средняя стоимость (используем len для количества)
count = len(filtered_orders)
average_amount = total_amount / count if count > 0 else 0
print(f"Средняя стоимость заказов этого клиента: {average_amount}")