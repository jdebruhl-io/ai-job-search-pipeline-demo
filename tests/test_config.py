import sys
sys.path.insert(0, 'C:\\ai-agents\\ai-job-search-pipeline')
import config
print('BASE_DIR:', config.BASE_DIR)
print('LLM_MODEL:', config.LLM_MODEL)
print('SCORE_THRESHOLD:', config.SCORE_THRESHOLD)
print('LOG_FILE:', config.LOG_FILE)
print('All good!')
