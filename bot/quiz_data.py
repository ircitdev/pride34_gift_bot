"""Quiz questions and answers data."""
from bot.texts import TextManager


def get_quiz_questions():
    """Get quiz questions from TextManager."""
    questions = {}
    for i in range(1, 6):
        questions[i] = {
            "text": TextManager.get(f'quiz.question_{i}.text'),
            "options": TextManager.get_list(f'quiz.question_{i}.options')
        }
    return questions


# For backward compatibility
QUIZ_QUESTIONS = get_quiz_questions()


def get_predictions():
    """Get predictions from TextManager."""
    return {
        "fitness_enthusiast": TextManager.get('predictions.fitness_enthusiast'),
        "balanced_lifestyle": TextManager.get('predictions.balanced_lifestyle'),
        "sweet_lover": TextManager.get('predictions.sweet_lover'),
        "beginner": TextManager.get('predictions.beginner'),
        "default": TextManager.get('predictions.default')
    }


# For backward compatibility
PREDICTIONS = get_predictions()


def get_prediction(answers: list) -> str:
    """
    Generate prediction based on user answers.

    Args:
        answers: List of answer indices (0-3) for each question

    Returns:
        Prediction text
    """
    # Reload predictions to get latest values
    predictions = get_predictions()

    # Simple logic: categorize based on most common answer type
    if not answers or len(answers) < 5:
        return predictions["default"]

    # Count answer patterns
    active_count = sum(1 for a in answers if a == 0)
    moderate_count = sum(1 for a in answers if a == 1)
    enthusiast_count = sum(1 for a in answers if a == 2)

    if enthusiast_count >= 3 or active_count >= 3:
        return predictions["fitness_enthusiast"]
    elif moderate_count >= 3:
        return predictions["balanced_lifestyle"]
    else:
        return predictions["default"]
