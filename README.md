# Make.com-to-AWS

This project aims to recreate complex [Make.com](https://make.com) scenarios using AWS Step Functions, potentially reducing costs for stable automation landscapes.

[Original Reddit Post](https://www.reddit.com/r/Integromat/comments/1fh5qzv/user_of_makecom_started_to_migrate_scenarios_to/)

## Project Overview

- **Goal**: Recreate Make.com scenarios using AWS Step Functions and Lambda functions
- **Motivation**: Potentially reduce costs for stable automation workflows
- **Working Scenario**: [VBliss Blog](https://github.com/amaynez/Make.com-to-AWS/tree/main/VBliss_Blog)
- **Planned Scenarios**: VBliss Image Alt Text, Linkedin Posts

## Getting Started

### Prerequisites

1. [AWS Account](https://aws.amazon.com/)
2. [Python 3](https://www.python.org/downloads/)
3. [Docker Community Edition](https://hub.docker.com/search/?type=edition&offering=community)
4. [AWS CLI](https://aws.amazon.com/cli/)
5. [SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
6. [Create AWS Secrets for API Credentials](https://docs.aws.amazon.com/secretsmanager/latest/userguide/create_secret.html)

### Installation and Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure AWS CLI:
   ```bash
   aws configure
   ```

## Development

### Project Structure

- `functions/`: Lambda function code
- `statemachines/`: Step Functions state machine definitions
- `template.yaml`: SAM template defining AWS resources

### Local Development

1. Use AWS Toolkit for your preferred IDE (VS Code, PyCharm, etc.)
2. Test Lambda functions locally using SAM CLI

### Deployment

1. Build the application:
   ```bash
   sam build --use-container
   ```
2. Deploy to AWS:
   ```bash
   sam deploy --guided
   ```

## Monitoring and Troubleshooting

- View Lambda function logs:
  ```bash
  sam logs -n FunctionName --stack-name "StackName" --tail
  ```

## Resources

- [AWS SAM Developer Guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html)
- [AWS Serverless Application Repository](https://aws.amazon.com/serverless/serverlessrepo/)

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

[GNU GENERAL PUBLIC LICENSE](LICENSE)
