import json
import logging
from summarizer import MedicalReportSummarizer

logger = logging.getLogger()
logger.setLevel(logging.INFO)

summarizer = MedicalReportSummarizer()

def lambda_handler(event, context):
    logger.info("Received event: %s", json.dumps(event))
    
    try:
        # Parse body
        body = json.loads(event.get('body', '{}')) if isinstance(event.get('body'), str) else event.get('body', {})
        clinical_text = body.get('clinical_text', '')
        patient_id = body.get('patient_id', 'UNKNOWN')
        
        if not clinical_text:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'clinical_text field is required.'})
            }
            
        summary_result = summarizer.summarize_report(clinical_text)
        
        response_payload = {
            'patient_id': patient_id,
            'summary': summary_result['summary'],
            'key_findings': summary_result['key_findings'],
            'triage_level': summary_result['triage_level'],
            'status': 'success'
        }
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps(response_payload)
        }
    except Exception as e:
        logger.error("Error processing medical report: %s", str(e), exc_info=True)
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Internal server error processing medical report.'})
        }
