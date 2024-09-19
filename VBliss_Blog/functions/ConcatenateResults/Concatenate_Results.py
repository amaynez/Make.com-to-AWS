
def lambda_handler(event, context):
    # The event will contain an array of all processed sections
    processed_sections = event
    blog_post = ""
    
    # Concatenate all processed sections
    for section in processed_sections:
        blog_post += section['body'] + "\n\n"
    
    # Remove any extra newlines
    blog_post = blog_post.strip()
    
    print(blog_post)

    return {
        'statusCode': 200,
        'body': blog_post
    }
