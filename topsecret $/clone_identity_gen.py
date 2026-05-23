import random

# --- CLONE_IDENTITY_GEN v1.0 ---
# Генерация легенды для корпоративного внедрения (Corporate Infiltration)

PERSONAS = [
    {"name": "Alexandr Volkov", "role": "Senior Python Developer", "skills": ["FastAPI", "PostgreSQL", "Docker", "AI"]},
    {"name": "Dmitry Reznik", "role": "DevOps Engineer", "skills": ["Kubernetes", "Terraform", "AWS", "Security"]},
    {"name": "Elena Belova", "role": "Product Manager", "skills": ["Agile", "Scrum", "Market Analysis", "B2B"]}
]

COMPANIES_TO_TARGET = [
    "OpenCloud solutions", "Nexus Tech", "Global Data Corp", "CyberShield UA"
]

def generate_cv(persona):
    print(f"[CLONE] Генерирую личность: {persona['name']}")
    print(f"[ROLE] {persona['role']}")
    print(f"[SKILLS] {', '.join(persona['skills'])}")
    
    cv_text = f"""
    --- CURRICULUM VITAE ---
    Name: {persona['name']}
    Objective: Seeking {persona['role']} position at top-tier tech companies.
    Experience: 5+ years in high-load systems, cloud architecture.
    Key Achievements: Optimized database performance by 40%, implemented AI-driven monitoring.
    """
    return cv_text

def simulate_infiltration():
    persona = random.choice(PERSONAS)
    target = random.choice(COMPANIES_TO_TARGET)
    cv = generate_cv(persona)
    
    print(f"[INFILTRATION] Подача заявки в {target}...")
    print(f"[STATUS] Заявка отправлена. Ожидание ответа через анонимный шлюз Lia_Mail.")
    
    return persona, target

if __name__ == "__main__":
    simulate_infiltration()
