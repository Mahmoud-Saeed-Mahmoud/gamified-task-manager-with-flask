# Gamified Task Manager

A motivating task management application that turns productivity into a game! Complete tasks, earn points, level up, and collect badges while staying organized.

## Features

- Task Management
  - Create, view, and complete tasks
  - Add descriptions and due dates
  - Track task completion status

- Gamification Elements
  - Earn points for completing tasks
  - Level up as you accumulate points
  - Maintain daily streaks
  - Unlock achievement badges
  - Track progress with a visual progress bar

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd gamified-task-manager
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

5. Open your browser and navigate to `http://localhost:5000`

## Usage

1. Register a new account or login if you already have one
2. Add tasks from your dashboard using the "Add Task" button
3. Complete tasks to earn points and increase your streak
4. Level up by earning points
5. Collect badges by reaching milestones

## Badge System

- **Beginner**: Earn your first 100 points
- **Intermediate**: Earn 500 points
- **Expert**: Earn 1000 points
- **Streak Master**: Maintain a 7-day streak
- **Streak Champion**: Maintain a 30-day streak

## Technologies Used

- Backend: Python Flask
- Database: SQLite with SQLAlchemy
- Frontend: HTML, CSS, Bootstrap 5
- Icons: Font Awesome
- Authentication: Flask-Login
