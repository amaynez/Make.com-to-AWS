# VBliss_Blog

An AWS Serverless Step Functions implementation of an automated blog posting workflow see [VBliss](https://vbliss.com.mx).

## Overview

This project replaces a [Make.com](https://www.make.com) scenario with an AWS Serverless application using Step Functions. It automates the process of creating and posting blog content, including generating text with AI, creating images, and updating WordPress. All as part of a proof of concept to migrate the blog posting workflow from a cloud-based no-code platform to AWS [main repo](../README.md)

## Workflow

1. Retrieve a blog post title from Google Sheets
2. Generate a table of contents using Claude Opus (via AWS Bedrock API)
3. Create blog post sections for each top-level item
4. Concatenate sections into a full blog post
5. Generate a summary of the post
6. Create a prompt for Stable Diffusion image generation
7. Generate an image using Stable Diffusion
8. Upload the image to WordPress
9. Upload the blog post to WordPress
10. Update Google Sheets with post information (URL, image URL, excerpt, timestamp)

## Implementation

### Make.com Scenario (Original)

![Make Scenario](blueprint.jpg "make.com scenario")

[JSON Export of the Scenario](blueprint.json)

### AWS Step Functions State Machine

![State Machine](stepfunctions_graph.jpg "State Machine in AWS Step Functions")

## Deployment

The application is deployed as an AWS Serverless application using CloudFormation. It's configured to run on a schedule, which is disabled by default to avoid unexpected charges.

### Scheduling

The `template.yaml` file contains the following event configuration:

```yaml
Events:
  BlogPostingSchedule:
    Type: Schedule 
    Properties:
      Description: Schedule to write the blog post every hour
      Enabled: False # Disabled by default to avoid incurring charges
      Schedule: "rate(1 hour)"
```

To enable the schedule, set `Enabled: True` and redeploy the stack.

## Cost Analysis

We will monitor and compare the costs of this AWS solution against the original Make.com scenario. Results will be updated here when available.

## Technologies Used

- AWS Step Functions
- AWS Lambda
- AWS Bedrock (Claude Opus)
- Stable Diffusion
- WordPress
- Google Sheets API

## Getting Started

1. Clone this repository
2. Install the AWS SAM CLI
3. Deploy the application using `sam deploy --guided`
4. Configure the necessary API keys and credentials for external services

## Contributing

Contributions are welcome! Please open an issue or submit a pull request with any improvements.

## License

[GNU GENERAL PUBLIC LICENSE](../LICENSE)