from models import User, ScreenTime, Task, DigitalHabit, UserTaskStatus, UserDigitalHabitStatus, Achievement, UserAchievementStatus, Question, UserQuestionAnswer
from config import SessionLocal
from utils import hash_password

def seed_data():
    db = SessionLocal()
    print("Seeding database...")

    users = [
        User(username="john_doe", email="john@example.com", password=hash_password("password123"), onboarding=True),
        User(username="jane_doe", email="jane@example.com", password=hash_password("password123"), onboarding=False)
    ]
    
     # Criar algumas tarefas
    tasks = [
        Task(task="Complete the onboarding process"),
        Task(task="Log in at least once a day"),
    ]

    # Criar hábitos digitais fictícios
    digital_habits = [
        DigitalHabit(name="Social Media"),
        DigitalHabit(name="Gaming"),
    ]

    # Criar conquistas (achievements)
    achievements = [
        Achievement(name="First Login", description="Logged in for the first time", tag="starter", image=None),
        Achievement(name="Habit Tracker", description="Added a habit to track", tag="habit", image=None),
    ]

    # Inserir os dados na base de dados
    db.add_all(users + tasks + digital_habits + achievements)
    # db.add_all(tasks + digital_habits + achievements)
    db.commit()

    print("Seeding completed successfully!")

if __name__ == "__main__":
    seed_data()
