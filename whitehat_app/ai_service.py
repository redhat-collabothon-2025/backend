import os
import requests
import random
from typing import Optional


class GraniteAIService:

    def __init__(self):
        # Read from environment variables, with fallback to default
        self.api_url = os.getenv(
            'AI_API_URL',
            "https://granite-3b-white-hat-project.apps.cluster-xdhbp.xdhbp.sandbox1403.opentlc.com/v1/chat/completions"
        )
        
        self.api_token = os.getenv('AI_API_TOKEN', None)
        self.model = os.getenv('AI_MODEL_NAME', "granite-3b")
        self.timeout = int(os.getenv('AI_TIMEOUT', 60))
        
        # Prepare headers with authentication if token is provided
        self.headers = {
            'Content-Type': 'application/json'
        }
        if self.api_token:
            self.headers['Authorization'] = f'Bearer {self.api_token}'

    def generate_linkedin_message(self, user_name: str, sender_name: str, sender_company: str) -> Optional[str]:

        prompt = f"""You are a professional recruiter at {sender_company}.
Write a short, professional LinkedIn message (2-3 sentences) to {user_name} about a job opportunity.
Be specific and make it sound genuine. Don't use quotes.
Keep it under 100 words."""

        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
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
                headers=self.headers,
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
                headers=self.headers,
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
                headers=self.headers,
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

    def analyze_log_risk(self, log_data: dict) -> dict:
        """Analyze a log entry to determine its risk level and generate incident details."""

        action_type = log_data.get('action_type', '')
        resource_type = log_data.get('resource_type', '')
        resource_accessed = log_data.get('resource_accessed', '')
        request_status = log_data.get('request_status', '')
        employee_id = log_data.get('employee_id', '')

        prompt = f"""You are a cybersecurity analyst. Analyze this employee activity log and determine if it represents a security risk.

Activity Details:
- Action: {action_type}
- Resource Type: {resource_type}
- Resource Accessed: {resource_accessed}
- Status: {request_status}
- Employee ID: {employee_id}

Determine:
1. Risk Level: LOW, MEDIUM, or CRITICAL
2. Should this create a security incident? (yes/no)
3. Brief incident description (one sentence, under 50 words)

Respond ONLY in this exact format:
Risk: [LOW/MEDIUM/CRITICAL]
Incident: [yes/no]
Description: [one sentence description]

High-risk activities include: confidential file access, sensitive data exports, bulk downloads, failed authentication attempts, suspicious access patterns.
Medium-risk activities include: unusual file downloads, access to restricted resources, multiple failed attempts.
Low-risk activities include: normal logins, standard file access, routine operations."""

        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are a cybersecurity analyst evaluating security logs"},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 200,
                    "temperature": 0.3
                },
                timeout=self.timeout
            )
            response.raise_for_status()

            content = response.json()["choices"][0]["message"]["content"].strip()

            # Parse the response
            result = {
                'risk_level': 'LOW',
                'create_incident': False,
                'description': ''
            }

            lines = content.split('\n')
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()

                    if key == 'risk':
                        result['risk_level'] = value.upper()
                    elif key == 'incident':
                        result['create_incident'] = value.lower() == 'yes'
                    elif key == 'description':
                        result['description'] = value

            return result

        except Exception as e:
            print(f"AI risk analysis failed: {str(e)}")
            # Fallback to rule-based analysis
            return self._fallback_risk_analysis(log_data)

    def _fallback_risk_analysis(self, log_data: dict) -> dict:
        """Fallback rule-based risk analysis if AI fails."""
        action_type = log_data.get('action_type', '').lower()
        request_status = log_data.get('request_status', '').lower()
        resource_type = log_data.get('resource_type', '').lower()
        resource_accessed = log_data.get('resource_accessed', '').lower()

        risk_level = 'LOW'
        create_incident = False
        description = f"Standard activity: {log_data.get('action_type', 'unknown action')}"

        # Define sensitive data indicators
        sensitive_indicators = ['confidential', 'sensitive', 'secret', 'classified', 'private']
        risky_actions = ['export', 'download', 'bulk', 'mass', 'transfer', 'share']

        # Check if dealing with sensitive data
        is_sensitive = any(indicator in action_type or indicator in resource_accessed or indicator in resource_type
                          for indicator in sensitive_indicators)

        # Check if action is risky
        is_risky_action = any(action in action_type for action in risky_actions)

        # Define truly routine actions that should NOT create any incidents
        no_incident_actions = ['login', 'logout', 'navigate', 'access_dashboard',
                              'search', 'browse', 'update_profile']
        is_no_incident = any(routine in action_type for routine in no_incident_actions)

        # CRITICAL: Sensitive data + risky action combination
        if is_sensitive and is_risky_action:
            risk_level = 'CRITICAL'
            create_incident = True
            description = f"Critical security event: {action_type} on sensitive resource detected for employee {log_data.get('employee_id', 'unknown')}"

        # CRITICAL: Multiple authentication failures or unauthorized access
        elif 'unauthorized' in action_type or 'breach' in action_type:
            risk_level = 'CRITICAL'
            create_incident = True
            description = f"Critical security event: {action_type} detected for employee {log_data.get('employee_id', 'unknown')}"

        # MEDIUM: Risky actions on non-sensitive data OR access to restricted resources
        elif is_risky_action or 'restricted' in action_type or 'restricted' in resource_accessed:
            # Exception: Normal single file downloads/views are LOW risk but still trackable
            if action_type in ['download_file', 'view_file', 'access_file', 'open_file', 'read_file'] and 'bulk' not in action_type and 'mass' not in action_type:
                risk_level = 'LOW'
                create_incident = True
                description = f"Low risk activity: {action_type} by employee {log_data.get('employee_id', 'unknown')}"
            else:
                risk_level = 'MEDIUM'
                create_incident = True
                description = f"Suspicious activity: {action_type} detected for employee {log_data.get('employee_id', 'unknown')}"

        # MEDIUM: Failed access to restricted resources
        elif request_status == 'failed' and ('restricted' in resource_accessed or 'confidential' in resource_accessed):
            risk_level = 'MEDIUM'
            create_incident = True
            description = f"Failed access to restricted resource: {action_type} by employee {log_data.get('employee_id', 'unknown')}"

        # LOW: Failed login or other failed operations
        elif request_status == 'failed':
            risk_level = 'LOW'
            create_incident = True
            description = f"Failed operation: {action_type} by employee {log_data.get('employee_id', 'unknown')}"

        # LOW: Document/file operations that should be tracked
        elif any(op in action_type for op in ['view_document', 'edit_document', 'create_document',
                                                'view_report', 'access_file', 'read', 'open']):
            risk_level = 'LOW'
            create_incident = True
            description = f"Low risk activity: {action_type} by employee {log_data.get('employee_id', 'unknown')}"

        # NO INCIDENT: Truly routine operations
        elif is_no_incident:
            risk_level = 'LOW'
            create_incident = False
            description = f"Standard activity: {log_data.get('action_type', 'unknown action')}"

        # LOW: Everything else that's successful (default trackable behavior)
        elif request_status == 'success':
            risk_level = 'LOW'
            create_incident = True
            description = f"Low risk activity: {action_type} by employee {log_data.get('employee_id', 'unknown')}"

        return {
            'risk_level': risk_level,
            'create_incident': create_incident,
            'description': description
        }


# Singleton instance
ai_service = GraniteAIService()
