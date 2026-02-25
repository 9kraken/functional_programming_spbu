from functools import reduce

# Отфильтровать студентов определенного возраста и/или с определенным списком предметов.
# Вычислить средний балл для каждого студента и общий средний балл по всем студентам.
# Найти студента (или студентов) с самым высоким средним баллом.

students = [
   {"name": f"Student_{i:03d}", "age": 19 + (i % 8), "grades": [60 + (i % 40), 65 + (i % 35), 70 + (i % 30), 75 + (i % 25)]}
   for i in range(100)
]

# Фильтрация: студентов старше 20 лет
filtered_students = list(filter(lambda s: s['age'] > 20, students))
print(f"Студенты старше 20 лет: \n{filtered_students}\n")

# Преобразование: средний балл для каждого студента
averages = list(map(lambda s: {'name': s['name'], 'average': sum(s['grades']) / len(s['grades'])}, students))
print(f"Студент и его средний балл: \n{averages}\n")

# Агрегация: общий средний балл (среднее от всех оценок)
all_grades = reduce(lambda acc, s: acc + s['grades'], students, [])
total_average = sum(all_grades) / len(all_grades) if all_grades else 0
print(f"Общий средний балл: {total_average}\n")

# Студент с максимальным средним баллом
max_student_map = max(averages, key=lambda s: s['average'])
print(f"Студент с максимальным средним баллом (через max()): \n{max_student_map}\n")

max_student = reduce(lambda max_s, s: 
   max_s if max_s['average'] > s['average'] else s, averages
)
print(f"Студент с максимальным средним баллом (через reduce()): \n{max_student}\n")