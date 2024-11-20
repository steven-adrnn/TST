from main import handler

# Ini diperlukan untuk Vercel serverless function
def __call__(event, context):
    return handler(event, context)