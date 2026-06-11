import json
import re

import google.generativeai as genai
from flask import current_app


class GeminiService:
    MODEL_NAME = "gemini-1.5-flash"

    def __init__(self):
        api_key = current_app.config.get("GEMINI_API_KEY", "")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(self.MODEL_NAME)
            self.enabled = True
        else:
            self.model = None
            self.enabled = False

    def _generate(self, prompt):
        if not self.enabled:
            return None
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception:
            current_app.logger.exception("Gemini API call failed")
            return None

    def _parse_json_response(self, text):
        if not text:
            return None
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    return None
        return None

    def analyze_job(self, title, description, requirements=""):
        prompt = f"""Analyze this job posting and return ONLY valid JSON with these keys:
- analysis: string (2-3 paragraph summary of the role, responsibilities, and ideal candidate)
- skills: array of required skill strings (max 15)
- experience_level: one of "Entry", "Mid", "Senior", "Lead", "Executive"

Job Title: {title}
Description: {description}
Requirements: {requirements or "Not specified"}

Return JSON only, no markdown."""

        result = self._generate(prompt)
        data = self._parse_json_response(result)

        if data:
            skills = data.get("skills", [])
            if isinstance(skills, list):
                skills_str = ", ".join(str(s) for s in skills)
            else:
                skills_str = str(skills)
            return {
                "analysis": data.get("analysis", ""),
                "skills": skills_str,
                "experience_level": data.get("experience_level", "Mid"),
            }

        return self._fallback_job_analysis(title, description, requirements)

    def _fallback_job_analysis(self, title, description, requirements):
        text = f"{description} {requirements}".lower()
        skill_keywords = [
            "python", "javascript", "java", "react", "flask", "django",
            "sql", "mysql", "aws", "docker", "kubernetes", "machine learning",
            "data analysis", "communication", "leadership", "project management",
            "html", "css", "node", "typescript", "git", "agile",
        ]
        found = [kw.title() for kw in skill_keywords if kw in text]
        level = "Mid"
        if any(w in text for w in ["senior", "lead", "principal", "5+ years", "7+ years"]):
            level = "Senior"
        elif any(w in text for w in ["entry", "junior", "graduate", "0-2 years", "intern"]):
            level = "Entry"

        return {
            "analysis": f"Role: {title}. This position requires candidates with relevant experience and skills matching the job description.",
            "skills": ", ".join(found[:10]) if found else "Communication, Problem Solving",
            "experience_level": level,
        }

    def parse_resume(self, raw_text):
        prompt = f"""Parse this resume text and return ONLY valid JSON with these keys:
- name: string
- email: string
- phone: string
- skills: array of skill strings (max 20)
- experience: string (brief work history summary)
- education: string (education summary)
- summary: string (professional summary, 2-3 sentences)

Resume text:
{raw_text[:8000]}

Return JSON only, no markdown."""

        result = self._generate(prompt)
        data = self._parse_json_response(result)

        if data:
            skills = data.get("skills", [])
            if isinstance(skills, list):
                skills_str = ", ".join(str(s) for s in skills)
            else:
                skills_str = str(skills)
            return {
                "parsed_name": data.get("name", ""),
                "parsed_email": data.get("email", ""),
                "parsed_phone": data.get("phone", ""),
                "parsed_skills": skills_str,
                "parsed_experience": data.get("experience", ""),
                "parsed_education": data.get("education", ""),
                "parsed_summary": data.get("summary", ""),
                "ai_summary": data.get("summary", ""),
            }

        return self._fallback_resume_parse(raw_text)

    def _fallback_resume_parse(self, raw_text):
        email_match = re.search(
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", raw_text
        )
        phone_match = re.search(
            r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", raw_text
        )
        lines = [ln.strip() for ln in raw_text.split("\n") if ln.strip()]
        name = lines[0][:80] if lines else "Unknown"

        skill_keywords = [
            "python", "javascript", "java", "react", "flask", "django",
            "sql", "mysql", "aws", "docker", "machine learning", "html", "css",
            "node", "typescript", "git", "excel", "communication",
        ]
        text_lower = raw_text.lower()
        found = [kw.title() for kw in skill_keywords if kw in text_lower]

        return {
            "parsed_name": name,
            "parsed_email": email_match.group() if email_match else "",
            "parsed_phone": phone_match.group() if phone_match else "",
            "parsed_skills": ", ".join(found[:15]),
            "parsed_experience": raw_text[:500],
            "parsed_education": "",
            "parsed_summary": lines[1][:300] if len(lines) > 1 else "",
            "ai_summary": "Resume parsed using rule-based extraction.",
        }

    def match_candidate_to_job(self, job, resume):
        prompt = f"""Score how well this candidate matches the job. Return ONLY valid JSON:
- score: float 0-100
- analysis: string (2-3 sentences explaining the match)
- strengths: array of 3-5 strength strings
- gaps: array of 2-4 gap/missing skill strings

Job Title: {job.title}
Job Description: {job.description}
Required Skills: {job.ai_skills or job.requirements or "Not specified"}
Experience Level: {job.ai_experience_level or "Mid"}

Candidate Skills: {resume.parsed_skills or "Not specified"}
Candidate Experience: {resume.parsed_experience or resume.raw_text[:2000] or "Not specified"}
Candidate Summary: {resume.parsed_summary or resume.ai_summary or "Not specified"}

Return JSON only, no markdown."""

        result = self._generate(prompt)
        data = self._parse_json_response(result)

        if data:
            score = float(data.get("score", 0))
            score = max(0.0, min(100.0, score))
            strengths = data.get("strengths", [])
            gaps = data.get("gaps", [])
            return {
                "match_score": score,
                "match_analysis": data.get("analysis", ""),
                "match_strengths": "|".join(str(s) for s in strengths),
                "match_gaps": "|".join(str(s) for s in gaps),
            }

        return self._fallback_match(job, resume)

    def _fallback_match(self, job, resume):
        job_skills = set(s.lower() for s in job.skills_list)
        candidate_skills = set(s.lower() for s in resume.skills_list)

        if not job_skills:
            job_text = (job.description or "").lower()
            job_skills = set(
                kw for kw in candidate_skills if kw in job_text
            ) or {"communication"}

        overlap = job_skills & candidate_skills
        score = (len(overlap) / len(job_skills) * 100) if job_skills else 50.0
        score = round(min(100.0, score + 20), 1)

        strengths = [f"Strong in {s}" for s in list(overlap)[:5]]
        gaps = [f"Missing {s}" for s in list(job_skills - candidate_skills)[:4]]

        if not strengths:
            strengths = ["Relevant background for the role"]
        if not gaps:
            gaps = ["Some preferred skills not listed on resume"]

        return {
            "match_score": score,
            "match_analysis": f"Candidate matches {len(overlap)} of {len(job_skills)} key skills for {job.title}.",
            "match_strengths": "|".join(strengths),
            "match_gaps": "|".join(gaps),
        }
