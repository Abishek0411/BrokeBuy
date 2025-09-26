import random
import hashlib
import time
from typing import Dict, Tuple

class SecurityChallenge:
    """Simple security challenge system as an alternative to ReCAPTCHA"""
    
    # Simple math problems for challenge
    MATH_PROBLEMS = [
        ("What is 2 + 3?", "5"),
        ("What is 10 - 4?", "6"),
        ("What is 3 * 2?", "6"),
        ("What is 8 / 2?", "4"),
        ("What is 5 + 7?", "12"),
        ("What is 15 - 8?", "7"),
        ("What is 4 * 3?", "12"),
        ("What is 20 / 4?", "5"),
        ("What is 6 + 9?", "15"),
        ("What is 18 - 5?", "13")
    ]
    
    # Simple word problems
    WORD_PROBLEMS = [
        ("What color is the sky?", "blue"),
        ("How many days in a week?", "7"),
        ("What is the first letter of the alphabet?", "a"),
        ("What comes after Monday?", "tuesday"),
        ("How many wheels does a car have?", "4")
    ]
    
    @staticmethod
    def generate_challenge() -> Tuple[str, str]:
        """Generate a random challenge and return (question, answer_hash)"""
        
        # Randomly choose between math and word problems
        if random.choice([True, False]):
            question, answer = random.choice(SecurityChallenge.MATH_PROBLEMS)
        else:
            question, answer = random.choice(SecurityChallenge.WORD_PROBLEMS)
        
        # Create a hash of the answer for verification
        answer_hash = hashlib.sha256(answer.lower().strip().encode()).hexdigest()
        
        return question, answer_hash
    
    @staticmethod
    def verify_challenge(user_answer: str, answer_hash: str) -> bool:
        """Verify if the user's answer matches the expected answer"""
        
        if not user_answer or not answer_hash:
            return False
        
        # Hash the user's answer and compare
        user_hash = hashlib.sha256(user_answer.lower().strip().encode()).hexdigest()
        return user_hash == answer_hash
    
    @staticmethod
    def generate_session_token() -> str:
        """Generate a unique session token for the challenge"""
        timestamp = str(int(time.time()))
        random_str = str(random.randint(1000, 9999))
        return hashlib.sha256(f"{timestamp}{random_str}".encode()).hexdigest()[:16]
