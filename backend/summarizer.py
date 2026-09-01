import re

class MedicalReportSummarizer:
    def __init__(self):
        self.urgent_keywords = ['fracture', 'hemorrhage', 'pneumothorax', 'infarct', 'lesion', 'acute', 'critical']

    def summarize_report(self, text):
        sentences = [s.strip() for s in re.split(r'[.!?]', text) if s.strip()]
        
        findings = []
        is_urgent = False
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(kw in sentence_lower for kw in self.urgent_keywords):
                findings.append(sentence)
                is_urgent = True
            elif 'impression' in sentence_lower or 'finding' in sentence_lower or 'note' in sentence_lower:
                findings.append(sentence)
                
        if not findings and sentences:
            findings = sentences[:3]
            
        summary_text = " ".join(findings) if findings else "No prominent pathological findings detected."
        triage_level = "CRITICAL / URGENT" if is_urgent else "ROUTINE"
        
        return {
            'summary': summary_text,
            'key_findings': findings,
            'triage_level': triage_level
        }
