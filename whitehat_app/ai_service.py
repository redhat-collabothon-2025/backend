import requests
import random
from typing import Optional


class GraniteAIService:

    def __init__(self):
        self.api_url = "http://granite-7b-lab-white-hat.apps.cluster-xdhbp.xdhbp.sandbox1403.opentlc.com/v1/chat/completions"
        self.model = "granite-7b-lab"
        self.timeout = 60

    def generate_linkedin_message(self, user_name: str, sender_name: str, sender_company: str) -> Optional[str]:

        prompt = f"""You are a professional recruiter at {sender_company}.
Write a short, professional LinkedIn message (2-3 sentences) to {user_name} about a job opportunity.
Be specific and make it sound genuine. Don't use quotes.
Keep it under 100 words."""

        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are a professional recruiter writing LinkedIn messages"},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 150,
                    "temperature": 0.8
                },
                timeout=self.timeout
            )
            response.raise_for_status()

            message = response.json()["choices"][0]["message"]["content"].strip()
            # Clean up quotes if present
            message = message.strip('"').strip("'")
            return message

        except Exception as e:
            print(f"AI generation failed: {str(e)}")
            # Fallback to template
            return self._get_fallback_linkedin_message(user_name, sender_company)

    def generate_profile_view_message(self, user_name: str, viewer_name: str, viewer_company: str, user_field: str) -> Optional[str]:
        """Generate a message from someone who viewed the profile."""

        prompt = f"""You are {viewer_name} from {viewer_company}.
Write a short professional message (1-2 sentences) to {user_name} explaining why you're interested in their {user_field} experience.
Sound genuine and professional. Don't use quotes.
Keep it under 80 words."""

        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are a professional writing a LinkedIn connection message"},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 120,
                    "temperature": 0.7
                },
                timeout=self.timeout
            )
            response.raise_for_status()

            message = response.json()["choices"][0]["message"]["content"].strip()
            message = message.strip('"').strip("'")
            return message

        except Exception as e:
            print(f"AI generation failed: {str(e)}")
            return self._get_fallback_profile_message(user_name, user_field, viewer_company)

    def generate_recruiter_profile(self) -> dict:
        """Generate a complete recruiter profile (name, title, company)."""

        prompt = """Generate a realistic recruiter profile for a LinkedIn message.
Return in this exact format (one line each):
Name: [Full name]
Title: [Job title]
Company: [Company name]

Make it realistic and professional. Use real-sounding names and companies."""

        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are generating realistic professional profiles"},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 100,
                    "temperature": 0.9
                },
                timeout=self.timeout
            )
            response.raise_for_status()

            content = response.json()["choices"][0]["message"]["content"].strip()

            # Parse the response
            lines = content.split('\n')
            profile = {}
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    profile[key] = value

            return {
                'name': profile.get('name', 'Sarah Thompson'),
                'title': profile.get('title', 'Senior Recruiter'),
                'company': profile.get('company', 'Tech Solutions Inc')
            }

        except Exception as e:
            print(f"AI generation failed: {str(e)}")
            return self._get_fallback_recruiter_profile()

    def generate_profile_viewer(self) -> dict:
        """Generate a complete profile viewer (name, title, company)."""

        prompt = """Generate a realistic LinkedIn profile for someone viewing a profile.
Return in this exact format (one line each):
Name: [Full name]
Title: [Job title]
Company: [Company name]

Make it realistic and professional."""

        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are generating realistic professional profiles"},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 100,
                    "temperature": 0.9
                },
                timeout=self.timeout
            )
            response.raise_for_status()

            content = response.json()["choices"][0]["message"]["content"].strip()

            # Parse the response
            lines = content.split('\n')
            profile = {}
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    profile[key] = value

            return {
                'name': profile.get('name', 'James Mitchell'),
                'title': profile.get('title', 'Technical Recruiter'),
                'company': profile.get('company', 'Global Innovations Corp')
            }

        except Exception as e:
            print(f"AI generation failed: {str(e)}")
            return self._get_fallback_profile_viewer()

    def _get_fallback_linkedin_message(self, user_name: str, company: str) -> str:
        """Fallback messages if AI fails."""
        templates = [
            f"Hi {user_name}, I came across your profile and was impressed by your background. We have an exciting opportunity at {company} that aligns with your expertise. Would you be open to a quick conversation?",
            f"Hello {user_name}, your experience caught my attention. We're looking for talented professionals at {company}. I'd love to discuss how your skills could be a great fit for our team.",
            f"Hi {user_name}, I'm reaching out regarding a senior position at {company}. Your background seems like an excellent match. Are you open to exploring new opportunities?"
        ]
        return random.choice(templates)

    def _get_fallback_profile_message(self, user_name: str, field: str, company: str) -> str:
        """Fallback profile view messages."""
        templates = [
            f"Hi {user_name}, I came across your profile and was impressed by your experience in {field}. I'd love to connect and discuss potential opportunities at {company}.",
            f"Hello {user_name}, your {field} background is impressive. I'm interested in learning more about your experience and exploring potential collaboration.",
            f"Hi {user_name}, I noticed your expertise in {field}. Would be great to connect and discuss how we might work together."
        ]
        return random.choice(templates)

    def _get_fallback_recruiter_profile(self) -> dict:
        """Fallback recruiter profiles if AI fails."""
        profiles = [
            {'name': 'Yulia Rudenko', 'title': 'Senior Talent Acquisition Specialist', 'company': 'SKELAR'},
            {'name': 'James Mitchell', 'title': 'HR Director', 'company': 'Tech Solutions Inc'},
            {'name': 'Rachel Stevens', 'title': 'Technical Recruiter', 'company': 'Google'},
            {'name': 'Sarah Thompson', 'title': 'Senior Recruiter', 'company': 'Microsoft'},
            {'name': 'Michael Chen', 'title': 'Talent Acquisition Manager', 'company': 'Amazon'},
            {'name': 'Alex Kumar', 'title': 'Hiring Manager', 'company': 'Meta'}
        ]
        return random.choice(profiles)

    def _get_fallback_profile_viewer(self) -> dict:
        """Fallback profile viewer profiles if AI fails."""
        profiles = [
            {'name': 'James Mitchell', 'title': 'Senior Recruiter', 'company': 'Tech Solutions Inc'},
            {'name': 'Rachel Stevens', 'title': 'Talent Acquisition Manager', 'company': 'Global Innovations Corp'},
            {'name': 'Alex Kumar', 'title': 'HR Director', 'company': 'Future Systems Ltd'},
            {'name': 'Thomas Wilson', 'title': 'Technical Recruiter', 'company': 'Digital Ventures Group'},
            {'name': 'Lisa Brown', 'title': 'Hiring Manager', 'company': 'Cloud Technologies'}
        ]
        return random.choice(profiles)


# Singleton instance
ai_service = GraniteAIService()
