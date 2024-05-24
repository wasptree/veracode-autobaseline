import datetime

def log(message, level='INFO'):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if level == 'INFO':
        prefix = '[INFO]'
    elif level == 'ERROR':
        prefix = '[ERROR]'
    elif level == 'WARN':
        prefix = '[WARN]'    
    else:
        prefix = '[UNKNOWN]'
    
    print(f"{timestamp} {prefix}: {message}")